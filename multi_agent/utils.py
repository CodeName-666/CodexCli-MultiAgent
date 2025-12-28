from __future__ import annotations

import os
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, List


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


def summarize_text(text: str, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2].rstrip()
    tail = text[- max_chars // 2 :].lstrip()
    return head + "\n...\n" + tail


def format_prompt(template: str, context: Dict[str, str], role_id: str, messages: Dict[str, str]) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        key = exc.args[0] if exc.args else "unknown"
        raise ValueError(messages["error_prompt_missing_key"].format(role_id=role_id, key=key)) from exc
