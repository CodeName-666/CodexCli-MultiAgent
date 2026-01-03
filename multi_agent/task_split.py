"""Task splitting utilities for large Markdown prompts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .format_converter import FormatConversionError, build_default_converter, extract_payload_from_markdown
from .utils import estimate_tokens, now_stamp, truncate_text, write_text

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass(frozen=True)
class TaskChunk:
    """Chunk of task text with an index and title."""
    index: int
    title: str
    content: str


@dataclass(frozen=True)
class HeadingInfo:
    """Parsed heading metadata from Markdown."""
    index: int
    level: int
    title: str
    line_no: int


def load_task_text(task_arg: str, workdir: Path) -> Tuple[str, str]:
    """Load task text from inline input or a file reference."""
    raw = (task_arg or "").strip()
    if not raw:
        raise ValueError("Fehler: --task ist leer.")
    if raw.startswith("@"):
        path_raw = raw[1:].strip()
        if not path_raw:
            raise ValueError("Fehler: Task-Datei ist leer (nutze '@pfad').")
        path = Path(path_raw).expanduser()
        if not path.is_absolute():
            path = (workdir / path).resolve()
        try:
            return path.read_text(encoding="utf-8"), str(path)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Fehler: Task-Datei nicht gefunden: {path}") from exc
    return raw, ""


def build_split_id(task_source: str, task_text: str) -> str:
    """Build a stable split id from task content."""
    base = Path(task_source).stem if task_source else "inline_task"
    slug = _slugify(base)
    digest = hashlib.sha256(task_text.encode("utf-8")).hexdigest()[:8]
    return f"{slug}_{digest}"


def needs_split(task_text: str, split_cfg: Dict[str, object]) -> bool:
    """Return True if heuristics indicate the task should be split."""
    text = (task_text or "").strip()
    if not text:
        return False
    max_chars = int(split_cfg.get("heuristic_max_chars", 3000) or 3000)
    max_tokens = int(split_cfg.get("heuristic_max_tokens", 1200) or 1200)
    max_headings = int(split_cfg.get("heuristic_max_headings", 8) or 8)
    heading_level = int(split_cfg.get("heading_level", 2) or 2)
    heading_count = len(extract_headings(text, heading_level))
    token_chars = int(split_cfg.get("heuristic_token_chars", 4) or 4)
    token_estimate = estimate_tokens(text, token_chars)
    if max_chars > 0 and len(text) > max_chars:
        return True
    if max_tokens > 0 and token_estimate > max_tokens:
        return True
    if max_headings > 0 and heading_count > max_headings:
        return True
    return False


def split_task_markdown(
    text: str,
    heading_level: int,
    min_chars: int,
    max_chars: int,
) -> List[TaskChunk]:
    """Split Markdown into chunks based on headings and size limits."""
    raw = (text or "").strip()
    if not raw:
        return []
    heading_level = max(1, min(heading_level, 6))
    primary = _split_by_heading_level(raw, heading_level)
    sized = _split_large_chunks(primary, heading_level + 1, max_chars)
    merged = _merge_small_chunks(sized, min_chars)
    chunks: List[TaskChunk] = []
    for idx, chunk in enumerate(merged, start=1):
        content = chunk.content.strip()
        if not content:
            continue
        chunks.append(TaskChunk(index=idx, title=chunk.title, content=content + "\n"))
    return chunks


def extract_headings(text: str, max_level: int) -> List[HeadingInfo]:
    """Extract headings up to a max level from Markdown text."""
    lines = (text or "").splitlines()
    max_level = max(1, min(max_level, 6))
    in_code = False
    headings: List[HeadingInfo] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        if level > max_level:
            continue
        title = match.group(2).strip()
        headings.append(HeadingInfo(index=len(headings) + 1, level=level, title=title, line_no=idx))
    return headings


def plan_chunks_with_llm(
    headings: List[HeadingInfo],
    codex_cmd: List[str],
    timeout_sec: int,
    max_headings: int,
    output_format: str = "json",
    formatting: Dict[str, object] | None = None,
) -> List[Dict[str, object]]:
    """Use an LLM to propose chunk boundaries for headings."""
    if not headings or len(headings) < 2:
        return []
    if max_headings > 0 and len(headings) > max_headings:
        return []
    prompt = _build_llm_prompt(headings, output_format=output_format)
    try:
        proc = subprocess.run(
            codex_cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    raw = (proc.stdout or "").strip()
    converter = build_default_converter(formatting) if output_format == "toon" else None
    data = _extract_plan_payload(raw, output_format, converter)
    if not isinstance(data, dict):
        return []
    chunks = data.get("chunks")
    if not isinstance(chunks, list):
        return []
    return chunks


def build_chunks_from_plan(
    text: str,
    headings: List[HeadingInfo],
    plan: List[Dict[str, object]],
) -> List[TaskChunk]:
    """Build task chunks from an LLM-provided plan."""
    validated = _validate_plan(plan, len(headings))
    if not validated:
        return []
    lines = (text or "").splitlines()
    preface = lines[: headings[0].line_no - 1] if headings else []
    chunks: List[TaskChunk] = []
    for idx, entry in enumerate(validated, start=1):
        start_idx, end_idx, title = entry
        start_line = headings[start_idx - 1].line_no
        end_line = headings[end_idx].line_no - 1 if end_idx < len(headings) else len(lines)
        chunk_lines = lines[start_line - 1 : end_line]
        if idx == 1 and preface:
            chunk_lines = preface + chunk_lines
        content = "\n".join(chunk_lines).strip()
        if not content:
            continue
        chunk_title = title or headings[start_idx - 1].title
        chunks.append(TaskChunk(index=idx, title=chunk_title, content=content + "\n"))
    return chunks


def build_chunk_payload(
    base_text: str,
    carry_over: str,
    carry_over_max_chars: int,
) -> str:
    """Compose a chunk payload with optional carry-over context."""
    payload = (base_text or "").rstrip()
    if not carry_over:
        return payload + "\n"
    carry = carry_over.strip()
    if carry_over_max_chars > 0:
        carry = truncate_text(carry, carry_over_max_chars)
    block = [payload, "", "## Kontext aus vorherigem Run", carry]
    return "\n".join(block).rstrip() + "\n"


def write_base_chunks(chunks: Iterable[TaskChunk], tasks_dir: Path) -> None:
    """Write base chunk files to the tasks directory."""
    tasks_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        filename = f"chunk_{chunk.index:03d}.md"
        write_text(tasks_dir / filename, chunk.content)


def init_manifest(
    split_id: str,
    task_source: str,
    chunks: List[TaskChunk],
    tasks_dir: Path,
) -> Dict[str, object]:
    """Create a task split manifest payload."""
    payload = {
        "split_id": split_id,
        "created_at": now_stamp(),
        "task_source": task_source,
        "tasks_dir": str(tasks_dir),
        "chunks": [],
    }
    for chunk in chunks:
        payload["chunks"].append(
            {
                "index": chunk.index,
                "title": chunk.title,
                "base_file": f"chunk_{chunk.index:03d}.md",
                "task_file": f"task_{chunk.index:03d}.md",
                "status": "pending",
                "run_id": "",
                "run_dir": "",
                "returncode": None,
                "summary": "",
            }
        )
    return payload


def save_manifest(path: Path, manifest: Dict[str, object]) -> None:
    """Write a manifest JSON file to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> Dict[str, object]:
    """Load a manifest JSON file from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_split_dirs(workdir: Path, split_cfg: Dict[str, object], split_id: str) -> Tuple[Path, Path]:
    """Resolve output and task directories for a split run."""
    raw = str(split_cfg.get("output_dir") or f".multi_agent_runs/{split_id}").replace("<split_id>", split_id)
    split_dir = Path(raw)
    if not split_dir.is_absolute():
        split_dir = workdir / split_dir
    tasks_dir = split_dir / "tasks"
    return split_dir, tasks_dir


def _split_by_heading_level(text: str, max_level: int) -> List[TaskChunk]:
    """Split text into chunks using headings up to a level."""
    lines = text.splitlines()
    in_code = False
    chunks: List[TaskChunk] = []
    current_lines: List[str] = []
    current_title = "Intro"

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
        if not in_code:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) <= max_level:
                if current_lines:
                    chunks.append(TaskChunk(index=0, title=current_title, content="\n".join(current_lines)))
                current_title = match.group(2).strip() or current_title
                current_lines = [line]
                continue
        current_lines.append(line)

    if current_lines:
        chunks.append(TaskChunk(index=0, title=current_title, content="\n".join(current_lines)))
    return chunks


def _split_large_chunks(chunks: List[TaskChunk], min_heading_level: int, max_chars: int) -> List[TaskChunk]:
    """Further split chunks that exceed the maximum size."""
    if max_chars <= 0:
        return list(chunks)
    out: List[TaskChunk] = []
    for chunk in chunks:
        if len(chunk.content) <= max_chars:
            out.append(chunk)
            continue
        out.extend(_split_chunk_to_size(chunk, min_heading_level, max_chars))
    return out


def _split_chunk_to_size(chunk: TaskChunk, min_heading_level: int, max_chars: int) -> List[TaskChunk]:
    """Split a single chunk by headings or paragraphs to fit size."""
    if len(chunk.content) <= max_chars:
        return [chunk]
    min_heading_level = max(1, min(min_heading_level, 6))
    prefix, remainder = _extract_prefix(chunk.content, min_heading_level)
    sub_chunks = _split_by_heading_min_level(remainder, min_heading_level) if remainder else []
    if len(sub_chunks) > 1:
        out: List[TaskChunk] = []
        for sub in sub_chunks:
            content = sub.content
            if prefix:
                content = f"{prefix}\n\n{content}"
            title = _join_titles(chunk.title, sub.title)
            out.extend(_split_chunk_to_size(TaskChunk(index=0, title=title, content=content), min_heading_level + 1, max_chars))
        return out
    return _split_by_paragraphs(chunk, max_chars)


def _split_by_heading_min_level(text: str, min_level: int) -> List[TaskChunk]:
    """Split text into chunks using headings at or below min level."""
    lines = text.splitlines()
    in_code = False
    chunks: List[TaskChunk] = []
    current_lines: List[str] = []
    current_title = "Teil"

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
        if not in_code:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) >= min_level:
                if current_lines:
                    chunks.append(TaskChunk(index=0, title=current_title, content="\n".join(current_lines)))
                current_title = match.group(2).strip() or current_title
                current_lines = [line]
                continue
        current_lines.append(line)
    if current_lines:
        chunks.append(TaskChunk(index=0, title=current_title, content="\n".join(current_lines)))
    return chunks


def _extract_prefix(text: str, min_level: int) -> Tuple[str, str]:
    """Extract a prefix section before the first heading at min level."""
    lines = text.splitlines()
    in_code = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
        if not in_code:
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) >= min_level:
                prefix = "\n".join(lines[:idx]).strip()
                remainder = "\n".join(lines[idx:]).strip()
                return prefix, remainder
    return text.strip(), ""


def _split_by_paragraphs(chunk: TaskChunk, max_chars: int) -> List[TaskChunk]:
    """Split a chunk into paragraph-sized chunks."""
    if max_chars <= 0:
        return [chunk]
    text = chunk.content.strip()
    if not text:
        return []
    paragraphs = re.split(r"\\n\\s*\\n", text)
    out: List[TaskChunk] = []
    buffer: List[str] = []
    part_idx = 1
    for para in paragraphs:
        candidate = "\n\n".join(buffer + [para]).strip()
        if candidate and len(candidate) > max_chars and buffer:
            title = f"{chunk.title} (Teil {part_idx})"
            out.append(TaskChunk(index=0, title=title, content="\n\n".join(buffer).strip()))
            buffer = [para]
            part_idx += 1
        else:
            buffer.append(para)
    if buffer:
        title = chunk.title if part_idx == 1 else f"{chunk.title} (Teil {part_idx})"
        out.append(TaskChunk(index=0, title=title, content="\n\n".join(buffer).strip()))
    return out


def _merge_small_chunks(chunks: List[TaskChunk], min_chars: int) -> List[TaskChunk]:
    """Merge adjacent chunks until they meet a minimum size."""
    if min_chars <= 0:
        return list(chunks)
    merged: List[TaskChunk] = []
    buffer: TaskChunk | None = None
    for chunk in chunks:
        if buffer is None:
            buffer = chunk
            continue
        if len(buffer.content) < min_chars:
            content = f"{buffer.content.rstrip()}\n\n{chunk.content.lstrip()}"
            buffer = TaskChunk(index=0, title=buffer.title, content=content)
        else:
            merged.append(buffer)
            buffer = chunk
    if buffer is not None:
        merged.append(buffer)
    return merged


def _join_titles(parent: str, child: str) -> str:
    """Join parent and child titles with a separator."""
    parent = parent.strip()
    child = child.strip()
    if not child or child.lower() == "teil":
        return parent
    if not parent:
        return child
    return f"{parent} / {child}"


def _slugify(text: str) -> str:
    """Return a lowercase ASCII slug from input text."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "task"


def _build_llm_prompt(headings: List[HeadingInfo], output_format: str = "json") -> str:
    """Build an LLM prompt for chunk planning."""
    if output_format == "toon":
        lines = [
            "You are a planner. Group the numbered headings into chunks by feature/module.",
            "Return TOON only in this shape:",
            "chunks[2]{start,end,title}:",
            "  1,2,Auth",
            "  3,4,DB",
            "",
            "Rules:",
            "- Cover all headings 1..N exactly once in order.",
            "- Chunks must be contiguous (next.start = previous.end + 1).",
            "- Keep the number of chunks minimal but reasonable.",
            "- Use short ASCII titles.",
            "",
            "Headings:",
        ]
        for heading in headings:
            lines.append(f"{heading.index}) [L{heading.level}] {heading.title}")
        lines.append("")
        return "\n".join(lines)

    lines = [
        "You are a planner. Group the numbered headings into chunks by feature/module.",
        "Return JSON only in this shape:",
        '{"chunks":[{"start":1,"end":2,"title":"Auth"}, {"start":3,"end":4,"title":"DB"}]}',
        "",
        "Rules:",
        "- Cover all headings 1..N exactly once in order.",
        "- Chunks must be contiguous (next.start = previous.end + 1).",
        "- Keep the number of chunks minimal but reasonable.",
        "- Use short ASCII titles.",
        "",
        "Headings:",
    ]
    for heading in headings:
        lines.append(f"{heading.index}) [L{heading.level}] {heading.title}")
    lines.append("")
    return "\n".join(lines)


def _extract_plan_payload(
    raw: str,
    output_format: str,
    converter,
) -> object:
    """Extract a JSON or TOON plan payload from LLM output."""
    if not raw:
        return None
    if output_format == "toon":
        payload = extract_payload_from_markdown(raw, "toon")
        if not payload:
            return None
        try:
            return converter.decode(payload, "toon") if converter else None
        except (FormatConversionError, ValueError):
            return None

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    snippet = raw[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def _validate_plan(
    plan: List[Dict[str, object]],
    total_headings: int,
) -> List[Tuple[int, int, str]]:
    """Validate plan entries and return normalized tuples."""
    if total_headings < 1:
        return []
    entries: List[Tuple[int, int, str]] = []
    expected_start = 1
    for entry in plan:
        if not isinstance(entry, dict):
            return []
        try:
            start = int(entry.get("start"))
            end = int(entry.get("end"))
        except (TypeError, ValueError):
            return []
        if start != expected_start or start < 1 or end < start or end > total_headings:
            return []
        title = str(entry.get("title") or "").strip()
        entries.append((start, end, title))
        expected_start = end + 1
    if expected_start != total_headings + 1:
        return []
    return entries
