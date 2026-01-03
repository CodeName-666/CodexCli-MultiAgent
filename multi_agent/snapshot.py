"""Workspace snapshot builders for context packaging."""

from __future__ import annotations

import abc
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from .constants import DEFAULT_MAX_FILES, DEFAULT_MAX_FILE_BYTES
from .format_converter import FormatConversionError, build_default_converter
from .utils import read_text_safe, select_relevant_files


_JSON_FENCE_RE = re.compile(r"(^[ \t]*)```json\s*\n(.*?)\n\1```", re.DOTALL | re.MULTILINE)


def _indent_block(text: str, prefix: str) -> str:
    lines = (text or "").splitlines()
    if not prefix:
        return "\n".join(lines)
    return "\n".join(f"{prefix}{line}" if line else prefix.rstrip() for line in lines)


def _convert_json_fences(text: str, converter) -> str:
    def _replace(match: re.Match) -> str:
        prefix = match.group(1) or ""
        body = match.group(2) or ""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return match.group(0)
        try:
            toon_text = converter.encode(data, "toon")
        except (FormatConversionError, ValueError):
            return match.group(0)
        block = "\n".join(
            [
                f"{prefix}```toon",
                _indent_block(toon_text, prefix),
                f"{prefix}```",
            ]
        )
        return block

    return _JSON_FENCE_RE.sub(_replace, text or "")


def _convert_full_json(text: str, converter) -> str | None:
    stripped = (text or "").strip()
    if not stripped.startswith(("{", "[")):
        return None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    try:
        return converter.encode(data, "toon")
    except (FormatConversionError, ValueError):
        return None

@dataclass(frozen=True)
class SnapshotResult:
    """Snapshot text and metadata for a workspace capture."""
    text: str
    files: List[Path]
    cache_hit: bool
    delta_used: bool
    max_bytes_per_file: int
    total_bytes: int


class BaseSnapshotter(abc.ABC):
    """Abstract snapshotter interface."""

    @abc.abstractmethod
    def build_snapshot(
        self,
        root: Path,
        snapshot_cfg: Dict[str, object],
        max_files: int,
        max_bytes_per_file: int,
        task: str | None = None,
        formatting: Dict[str, object] | None = None,
    ) -> SnapshotResult:
        """Build a workspace snapshot with optional formatting."""
        raise NotImplementedError


class WorkspaceSnapshotter(BaseSnapshotter):
    """Snapshotter that captures files from a local workspace."""

    def build_snapshot(
        self,
        root: Path,
        snapshot_cfg: Dict[str, object],
        max_files: int = DEFAULT_MAX_FILES,
        max_bytes_per_file: int = DEFAULT_MAX_FILE_BYTES,
        task: str | None = None,
        formatting: Dict[str, object] | None = None,
    ) -> SnapshotResult:
        """
        Snapshot des Workspaces:
        - Liste der Dateien
        - Inhalte von Textdateien (gekürzt)
        """
        root = root.resolve()
        files: List[Path] = []
        skip_dirs = set(snapshot_cfg.get("skip_dirs", []))
        skip_exts = set(snapshot_cfg.get("skip_exts", []))
        cache_file = snapshot_cfg.get("cache_file")
        delta_snapshot = bool(snapshot_cfg.get("delta_snapshot", False))
        selective_context = snapshot_cfg.get("selective_context", {})
        if not isinstance(selective_context, dict):
            selective_context = {"enabled": bool(selective_context)}
        selective_enabled = bool(selective_context.get("enabled", False))
        selective_min_files = int(selective_context.get("min_files", 0))
        selective_max_files = int(selective_context.get("max_files", max_files))
        max_total_bytes = snapshot_cfg.get("max_total_bytes")

        for p in root.rglob("*"):
            if p.is_dir():
                continue
            parts = set(p.parts)
            if parts & skip_dirs:
                continue
            files.append(p)

        files = sorted(files)
        if selective_enabled:
            files = select_relevant_files(task or "", files, selective_min_files, selective_max_files)
        files = files[:max_files]

        cache_hit, delta_used, selected_files, cached_snapshot = self._apply_cache(
            root,
            files,
            cache_file,
            delta_snapshot,
        )
        if cache_hit and cached_snapshot is not None:
            return SnapshotResult(
                text=str(cached_snapshot),
                files=files,
                cache_hit=True,
                delta_used=False,
                max_bytes_per_file=max_bytes_per_file,
                total_bytes=len(str(cached_snapshot).encode("utf-8", errors="replace")),
            )
        if selected_files is not None:
            files = selected_files

        effective_max_bytes = int(max_bytes_per_file)
        if max_total_bytes is not None and files:
            per_file = int(max_total_bytes) // max(len(files), 1)
            effective_max_bytes = max(256, min(effective_max_bytes, per_file))

        formatting_cfg = formatting or {}
        formatting_enabled = bool(formatting_cfg.get("enabled", False))
        extension_map = formatting_cfg.get("extension_map") or {}
        if not isinstance(extension_map, dict):
            extension_map = {}
        normalized_map: Dict[str, object] = {}
        for key, value in extension_map.items():
            key_str = str(key).lower()
            if key_str and not key_str.startswith("."):
                key_str = f".{key_str}"
            normalized_map[key_str] = value
        extension_map = normalized_map
        conversion_strict = bool(formatting_cfg.get("conversion_strict", False))
        snapshot_note = str(formatting_cfg.get("snapshot_note") or "").strip()
        converter = build_default_converter(formatting_cfg) if formatting_enabled else None
        text_json_to_toon = bool(formatting_cfg.get("text_json_to_toon", False))
        text_extensions = formatting_cfg.get("text_extensions") or []
        if not isinstance(text_extensions, list):
            text_extensions = [text_extensions]
        text_extensions = [str(item).lower() for item in text_extensions if item]

        lines: List[str] = []
        lines.append(str(snapshot_cfg["workspace_header"]).format(root=root))
        lines.append("")
        lines.append(str(snapshot_cfg["files_header"]))
        total_bytes = 0
        for p in files:
            rel = p.relative_to(root)
            try:
                size = p.stat().st_size
            except OSError:
                size = -1
            lines.append(str(snapshot_cfg["file_line"]).format(rel=rel, size=size))

        lines.append("")
        lines.append(str(snapshot_cfg["content_header"]))
        for p in files:
            if p.suffix.lower() in skip_exts:
                continue
            rel = p.relative_to(root)
            try:
                size = p.stat().st_size
            except OSError:
                size = -1
            content = read_text_safe(p, limit_bytes=effective_max_bytes)
            if not content.strip():
                continue
            ext = p.suffix.lower()
            was_truncated = size > 0 and effective_max_bytes > 0 and size > effective_max_bytes
            if converter and ext in extension_map and not was_truncated:
                target_format = str(extension_map.get(ext) or "").strip().lower()
                if target_format:
                    try:
                        content = converter.convert_by_extension(content, ext, target_format)
                        if snapshot_note:
                            content = f"{snapshot_note}\n{content}"
                    except (FormatConversionError, ValueError):
                        if conversion_strict:
                            raise
            if converter and text_json_to_toon and (not was_truncated) and ext in text_extensions:
                content = _convert_json_fences(content, converter)
                full_toon = _convert_full_json(content, converter)
                if full_toon:
                    content = full_toon
            header = str(snapshot_cfg["file_section_header"]).format(rel=rel)
            lines.append(f"\n{header}\n")
            lines.append(content)
            total_bytes += len(content.encode("utf-8", errors="replace"))
        snapshot_text = "\n".join(lines)

        self._write_cache(root, files, cache_file, snapshot_text)
        return SnapshotResult(
            text=snapshot_text,
            files=files,
            cache_hit=cache_hit,
            delta_used=delta_used,
            max_bytes_per_file=effective_max_bytes,
            total_bytes=total_bytes,
        )

    def _apply_cache(
        self,
        root: Path,
        files: List[Path],
        cache_file: object,
        delta_snapshot: bool,
    ) -> Tuple[bool, bool, List[Path] | None, str | None]:
        """Apply snapshot caching and optional delta selection."""
        if not cache_file:
            return False, False, None, None
        cache_path = root / str(cache_file)
        cache = self._load_cache(cache_path)
        current_index = self._build_file_index(root, files)
        current_hash = self._hash_file_index(current_index)
        if cache and cache.get("signature_hash") == current_hash and cache.get("snapshot"):
            return True, False, files, str(cache.get("snapshot"))
        if delta_snapshot and cache and cache.get("file_index"):
            prev_index = cache.get("file_index", {})
            changed = [
                root / rel
                for rel, meta in current_index.items()
                if prev_index.get(rel) != meta
            ]
            return False, True, changed, None
        return False, False, None, None

    def _load_cache(self, path: Path) -> Dict[str, object]:
        """Load a snapshot cache file or return empty dict."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_cache(self, root: Path, files: List[Path], cache_file: object, snapshot: str) -> None:
        """Persist a snapshot cache payload."""
        if not cache_file:
            return
        cache_path = root / str(cache_file)
        file_index = self._build_file_index(root, files)
        payload = {
            "signature_hash": self._hash_file_index(file_index),
            "file_index": file_index,
            "snapshot": snapshot,
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload, ensure_ascii=True) + "\n", encoding="utf-8")

    @staticmethod
    def _build_file_index(root: Path, files: List[Path]) -> Dict[str, Tuple[int, int]]:
        """Build a file index of mtime and size for cache signatures."""
        index: Dict[str, Tuple[int, int]] = {}
        for p in files:
            rel = p.relative_to(root).as_posix()
            try:
                stat = p.stat()
                index[rel] = (int(stat.st_mtime), int(stat.st_size))
            except OSError:
                index[rel] = (0, 0)
        return index

    @staticmethod
    def _hash_file_index(index: Dict[str, Tuple[int, int]]) -> str:
        """Return a stable hash for a file index."""
        items = [f"{key}:{meta[0]}:{meta[1]}" for key, meta in sorted(index.items())]
        digest = hashlib.sha256("\n".join(items).encode("utf-8")).hexdigest()
        return digest
