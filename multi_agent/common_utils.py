"""Common utility functions used across the codebase."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict


def load_json(path: Path) -> Dict[str, object]:
    """Load JSON file and return as dictionary."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, object]) -> None:
    """Write dictionary to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def deep_merge(base: Dict[str, object], override: Dict[str, object]) -> Dict[str, object]:
    """Deep merge two dictionaries, override wins conflicts."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def slugify(text: str) -> str:
    """Convert text to slug format (lowercase, alphanumeric with underscores)."""
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")
