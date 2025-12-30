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
    role_defaults = cfg.get("role_defaults", {})

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

        # Validate sharding configuration
        ok, error = _validate_sharding_config(role_entry, role_defaults)
        if not ok:
            return False, f"role {role_path}: {error}"

    return True, ""


def _validate_sharding_config(role_entry: Dict[str, object], role_defaults: Dict[str, object]) -> Tuple[bool, str]:
    """Validate sharding-related configuration fields."""
    shard_mode = role_entry.get("shard_mode", role_defaults.get("shard_mode", "none"))
    overlap_policy = role_entry.get("overlap_policy", role_defaults.get("overlap_policy", "warn"))

    # Validate shard_mode enum
    valid_shard_modes = ["none", "headings", "files", "llm"]
    if shard_mode not in valid_shard_modes:
        return False, f"invalid shard_mode '{shard_mode}', must be one of {valid_shard_modes}"

    # Validate overlap_policy enum
    valid_overlap_policies = ["forbid", "warn", "allow"]
    if overlap_policy not in valid_overlap_policies:
        return False, f"invalid overlap_policy '{overlap_policy}', must be one of {valid_overlap_policies}"

    # Validate numeric fields
    shard_count = role_entry.get("shard_count", role_defaults.get("shard_count"))
    if shard_count is not None:
        try:
            count = int(shard_count)
            if count < 1:
                return False, "shard_count must be >= 1"
        except (TypeError, ValueError):
            return False, "shard_count must be an integer"

    max_files_per_shard = role_entry.get("max_files_per_shard", role_defaults.get("max_files_per_shard", 10))
    if max_files_per_shard is not None:
        try:
            count = int(max_files_per_shard)
            if count < 1:
                return False, "max_files_per_shard must be >= 1"
        except (TypeError, ValueError):
            return False, "max_files_per_shard must be an integer"

    max_reshard_depth = role_entry.get("max_reshard_depth", role_defaults.get("max_reshard_depth", 2))
    try:
        depth = int(max_reshard_depth)
        if depth < 0:
            return False, "max_reshard_depth must be >= 0"
    except (TypeError, ValueError):
        return False, "max_reshard_depth must be an integer"

    return True, ""
