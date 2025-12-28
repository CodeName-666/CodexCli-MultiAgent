from __future__ import annotations

import math
import os
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_safe(path: Path, limit_bytes: int) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > limit_bytes:
        data = data[:limit_bytes]
    return data.decode("utf-8", errors="replace")


def get_codex_cmd(env_var: str, default_cmd: str) -> List[str]:
    """
    Erlaubt Overrides via ENV:
      CODEX_CMD="codex --model xyz"
    """
    raw = os.environ.get(env_var, default_cmd)
    # On Windows, use non-POSIX splitting to keep backslashes/paths intact.
    return shlex.split(raw, posix=(os.name != "nt"))


def parse_cmd(raw_cmd: str) -> List[str]:
    return shlex.split(raw_cmd, posix=(os.name != "nt"))


def estimate_tokens(text: str, token_chars: int = 4) -> int:
    if not text:
        return 0
    token_chars = max(1, int(token_chars))
    return int(math.ceil(len(text) / token_chars))


def detect_model_from_cmd(cmd: List[str]) -> str:
    for idx, part in enumerate(cmd):
        if part in ("--model", "-m"):
            if idx + 1 < len(cmd):
                return cmd[idx + 1]
        if part.startswith("--model="):
            return part.split("=", 1)[1]
    return ""


def summarize_text(text: str, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2].rstrip()
    tail = text[- max_chars // 2 :].lstrip()
    return head + "\n...\n" + tail


def truncate_text(text: str, max_chars: int) -> str:
    text = (text or "")
    if max_chars < 1:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def format_prompt(template: str, context: Dict[str, str], role_id: str, messages: Dict[str, str]) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        key = exc.args[0] if exc.args else "unknown"
        raise ValueError(messages["error_prompt_missing_key"].format(role_id=role_id, key=key)) from exc


def get_status_text(returncode: int, stdout: str, messages: Dict[str, str]) -> str:
    if returncode != 0:
        return messages["status_error"]
    if not (stdout or "").strip():
        return messages["status_no_output"]
    return messages["status_ok"]


def extract_error_reason(stdout: str, stderr: str, max_chars: int = 200) -> str:
    raw = (stderr or "").strip() or (stdout or "").strip()
    if not raw:
        return "Keine Fehlerausgabe."
    raw = re.sub(r"\s+", " ", raw)
    return truncate_text(raw, max_chars)


def normalize_output_text(text: str) -> str:
    lines = [(line.rstrip()) for line in (text or "").splitlines()]
    normalized: List[str] = []
    blank = False
    for idx, line in enumerate(lines):
        if line.strip() == "":
            if blank:
                continue
            blank = True
            normalized.append("")
            continue
        blank = False
        if line.strip().endswith(":"):
            next_idx = idx + 1
            while next_idx < len(lines) and lines[next_idx].strip() == "":
                next_idx += 1
            if next_idx >= len(lines):
                continue
            next_line = lines[next_idx].lstrip()
            if next_line.startswith("-") or next_line.startswith("#"):
                continue
        normalized.append(line)
    return "\n".join(normalized).strip()


def validate_output_sections(text: str, expected_sections: Iterable[str]) -> Tuple[bool, List[str]]:
    missing: List[str] = []
    for section in expected_sections:
        if section and section not in text:
            missing.append(section)
    return len(missing) == 0, missing


def select_relevant_files(
    task: str,
    files: Iterable[Path],
    min_files: int,
    max_files: int,
) -> List[Path]:
    tokens = [t for t in re.split(r"[^A-Za-z0-9_./-]+", task or "") if len(t) >= 3]
    lowered = [t.lower() for t in tokens]
    if not lowered:
        return list(files)
    matches: List[Path] = []
    for path in files:
        rel = path.as_posix().lower()
        if any(tok in rel for tok in lowered):
            matches.append(path)
    if len(matches) < min_files:
        return list(files)
    return matches[:max_files]
