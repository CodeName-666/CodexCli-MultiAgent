from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import AppConfig, RoleConfig


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_role_config(role_entry: Dict[str, object], base_dir: Path) -> RoleConfig:
    role_path = base_dir / str(role_entry["file"])
    data = load_json(role_path)
    role_id = str(role_entry.get("id") or data.get("id") or "")
    if not role_id:
        raise ValueError(f"Role file missing id: {role_path}")
    return RoleConfig(
        id=role_id,
        name=str(data.get("name") or role_id),
        role=str(data["role"]),
        prompt_template=str(data["prompt_template"]),
        apply_diff=bool(role_entry.get("apply_diff", False)),
    )


def load_app_config(config_path: Path) -> AppConfig:
    data = load_json(config_path)
    base_dir = config_path.parent
    roles = [load_role_config(role_entry, base_dir) for role_entry in data["roles"]]
    final_role_id = str(data.get("final_role_id") or (roles[-1].id if roles else ""))
    return AppConfig(
        system_rules=str(data["system_rules"]),
        roles=roles,
        final_role_id=final_role_id,
        summary_max_chars=int(data.get("summary_max_chars", 1400)),
        final_summary_max_chars=int(data.get("final_summary_max_chars", 2400)),
        codex_env_var=str(data["codex"]["env_var"]),
        codex_default_cmd=str(data["codex"]["default_cmd"]),
        paths=data["paths"],
        snapshot=data["snapshot"],
        agent_output=data["agent_output"],
        messages=data["messages"],
        diff_messages=data["diff_messages"],
        cli=data["cli"],
    )
