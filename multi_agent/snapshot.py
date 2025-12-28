from __future__ import annotations

import abc
from pathlib import Path
from typing import Dict, List

from .constants import DEFAULT_MAX_FILES, DEFAULT_MAX_FILE_BYTES
from .utils import read_text_safe


class BaseSnapshotter(abc.ABC):
    @abc.abstractmethod
    def build_snapshot(
        self,
        root: Path,
        snapshot_cfg: Dict[str, object],
        max_files: int,
        max_bytes_per_file: int,
    ) -> str:
        raise NotImplementedError


class WorkspaceSnapshotter(BaseSnapshotter):
    def build_snapshot(
        self,
        root: Path,
        snapshot_cfg: Dict[str, object],
        max_files: int = DEFAULT_MAX_FILES,
        max_bytes_per_file: int = DEFAULT_MAX_FILE_BYTES,
    ) -> str:
        """
        Snapshot des Workspaces:
        - Liste der Dateien
        - Inhalte von Textdateien (gekürzt)
        """
        root = root.resolve()
        files: List[Path] = []
        skip_dirs = set(snapshot_cfg.get("skip_dirs", []))
        skip_exts = set(snapshot_cfg.get("skip_exts", []))

        for p in root.rglob("*"):
            if p.is_dir():
                continue
            parts = set(p.parts)
            if parts & skip_dirs:
                continue
            files.append(p)

        files = sorted(files)[:max_files]

        lines: List[str] = []
        lines.append(str(snapshot_cfg["workspace_header"]).format(root=root))
        lines.append("")
        lines.append(str(snapshot_cfg["files_header"]))
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
            content = read_text_safe(p, limit_bytes=max_bytes_per_file)
            if not content.strip():
                continue
            header = str(snapshot_cfg["file_section_header"]).format(rel=rel)
            lines.append(f"\n{header}\n")
            lines.append(content)
        return "\n".join(lines)
