from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import AppConfig, RoleConfig


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def load_role_config(
    role_entry: Dict[str, object],
    base_dir: Path,
    role_defaults: Dict[str, object],
) -> RoleConfig:
    role_path = base_dir / str(role_entry["file"])
    data = load_json(role_path)
    role_id = str(role_entry.get("id") or data.get("id") or "")
    if not role_id:
        raise ValueError(f"Role file missing id: {role_path}")
    defaults = role_defaults or {}
    timeout_sec = role_entry.get("timeout_sec", defaults.get("timeout_sec"))
    max_output_chars = role_entry.get("max_output_chars", defaults.get("max_output_chars"))
    max_prompt_chars = role_entry.get("max_prompt_chars", defaults.get("max_prompt_chars"))
    max_prompt_tokens = role_entry.get("max_prompt_tokens", defaults.get("max_prompt_tokens"))
    retries = role_entry.get("retries", defaults.get("retries", 0))
    return RoleConfig(
        id=role_id,
        name=str(data.get("name") or role_id),
        role=str(data["role"]),
        prompt_template=str(data["prompt_template"]),
        apply_diff=bool(role_entry.get("apply_diff", False)),
        instances=max(1, int(role_entry.get("instances", 1))),
        depends_on=_coerce_str_list(role_entry.get("depends_on")),
        timeout_sec=int(timeout_sec) if timeout_sec is not None else None,
        max_output_chars=int(max_output_chars) if max_output_chars is not None else None,
        max_prompt_chars=int(max_prompt_chars) if max_prompt_chars is not None else None,
        max_prompt_tokens=int(max_prompt_tokens) if max_prompt_tokens is not None else None,
        retries=max(0, int(retries)),
        codex_cmd=str(role_entry.get("codex_cmd")) if role_entry.get("codex_cmd") else None,
        model=str(role_entry.get("model")) if role_entry.get("model") else None,
        expected_sections=_coerce_str_list(role_entry.get("expected_sections")),
        run_if_review_critical=bool(role_entry.get("run_if_review_critical", False)),
    )


def load_app_config(config_path: Path) -> AppConfig:
    data = load_json(config_path)
    base_dir = config_path.parent
    role_defaults = data.get("role_defaults") or {}
    roles = [load_role_config(role_entry, base_dir, role_defaults) for role_entry in data["roles"]]
    final_role_id = str(data.get("final_role_id") or (roles[-1].id if roles else ""))
    coordination = data.get("coordination") or {}
    outputs = data.get("outputs") or {}
    return AppConfig(
        system_rules=str(data["system_rules"]),
        roles=roles,
        final_role_id=final_role_id,
        summary_max_chars=int(data.get("summary_max_chars", 1400)),
        final_summary_max_chars=int(data.get("final_summary_max_chars", 2400)),
        codex_env_var=str(data["codex"]["env_var"]),
        codex_default_cmd=str(data["codex"]["default_cmd"]),
        paths=data["paths"],
        coordination=coordination,
        outputs=outputs,
        snapshot=data["snapshot"],
        agent_output=data["agent_output"],
        messages=data["messages"],
        diff_messages=data["diff_messages"],
        cli=data["cli"],
        role_defaults=role_defaults,
        prompt_limits=data.get("prompt_limits") or {},
        diff_safety=data.get("diff_safety") or {},
        diff_apply=data.get("diff_apply") or {},
        logging=data.get("logging") or {},
        feedback_loop=data.get("feedback_loop") or {},
    )
