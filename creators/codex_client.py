"""Codex CLI client utilities for creator tools."""
from __future__ import annotations

import re
import subprocess
from typing import List


def call_codex(prompt: str, codex_cmd: List[str], timeout_sec: int) -> str:
    """
    Call Codex CLI and return stdout.

    Args:
        prompt: The prompt to send to Codex
        codex_cmd: Command and arguments for Codex CLI
        timeout_sec: Timeout in seconds

    Returns:
        Codex response (stdout)

    Raises:
        RuntimeError: If Codex CLI fails, times out, or is not found
    """
    try:
        proc = subprocess.run(
            codex_cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Codex CLI timeout nach {timeout_sec}s") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(f"Codex CLI nicht gefunden: {exc}") from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        raise RuntimeError(f"Codex CLI failed (rc={proc.returncode}): {stderr}")

    return (proc.stdout or "").strip()


def extract_json_from_markdown(text: str) -> str:
    """
    Extract JSON from Markdown code blocks if present.

    Tries to extract JSON from:
    1. ```json ... ``` blocks
    2. Generic ``` ... ``` blocks containing JSON
    3. Returns entire text if no code blocks found

    Args:
        text: Text potentially containing Markdown code blocks

    Returns:
        Extracted JSON string
    """
    # Try to find JSON code block
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1)

    # Try generic code block
    match = re.search(r"```\s*\n(\{.*?\})\n```", text, re.DOTALL)
    if match:
        return match.group(1)

    # Otherwise: entire text
    return text.strip()
