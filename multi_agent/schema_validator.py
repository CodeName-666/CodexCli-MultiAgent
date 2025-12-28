from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_required(data: Dict[str, object], keys: list[str]) -> Tuple[bool, str]:
    for key in keys:
        if key not in data:
            return False, f"missing key: {key}"
    return True, ""


def validate_config(config_path: Path) -> Tuple[bool, str]:
    try:
        cfg = _load_json(config_path)
    except FileNotFoundError as exc:
        return False, f"config not found: {exc}"
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"

    ok, error = _validate_required(
        cfg,
        [
            "system_rules",
            "roles",
            "codex",
            "paths",
            "snapshot",
            "agent_output",
            "messages",
            "diff_messages",
            "cli",
        ],
    )
    if not ok:
        return False, error

    roles = cfg.get("roles")
    if not isinstance(roles, list):
        return False, "roles must be a list"

    base_dir = config_path.parent
    for role_entry in roles:
        if not isinstance(role_entry, dict):
            return False, "role entry must be an object"
        if "file" not in role_entry:
            return False, "role entry missing file"
        role_path = base_dir / str(role_entry["file"])
        try:
            role_data = _load_json(role_path)
        except FileNotFoundError as exc:
            return False, f"role file not found: {exc}"
        except json.JSONDecodeError as exc:
            return False, f"invalid role JSON: {exc}"
        ok, error = _validate_required(role_data, ["id", "role", "prompt_template"])
        if not ok:
            return False, f"role {role_path}: {error}"

    return True, ""
