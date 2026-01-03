from __future__ import annotations

from pathlib import Path
from typing import Dict

from .common_utils import load_json, deep_merge
from .coordination import CoordinationConfig
from .constants import get_static_config_dir
from .models import (
    AgentOutputConfig,
    AppConfig,
    CliConfig,
    CliProvidersConfig,
    DiffApplyConfig,
    DiffMessageCatalog,
    DiffSafetyConfig,
    FeedbackLoopConfig,
    LoggingConfig,
    MessageCatalog,
    OutputsConfig,
    PathsConfig,
    PromptLimitsConfig,
    RoleConfig,
    RoleDefaultsConfig,
    SnapshotConfig,
    StreamingConfig,
    TaskLimitsConfig,
    TaskSplitConfig,
)


def _coerce_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _normalize_prompt_template(value: object, role_path: Path) -> str:
    if isinstance(value, list):
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"Role file prompt_template must be list of strings: {role_path}")
        return "\n".join(value)
    if isinstance(value, str):
        return value
    raise ValueError(f"Role file prompt_template must be string or list of strings: {role_path}")


def load_role_config(
    role_entry: Dict[str, object],
    base_dir: Path,
    role_defaults: RoleDefaultsConfig,
) -> RoleConfig:
    role_path = base_dir / str(role_entry["file"])
    data = load_json(role_path)
    role_id = str(role_entry.get("id") or data.get("id") or "")
    if not role_id:
        raise ValueError(f"Role file missing id: {role_path}")
    if "prompt_template" not in data:
        raise ValueError(f"Role file missing prompt_template: {role_path}")
    defaults = role_defaults
    timeout_sec = role_entry.get("timeout_sec", defaults.get("timeout_sec"))
    max_output_chars = role_entry.get("max_output_chars", defaults.get("max_output_chars"))
    max_prompt_chars = role_entry.get("max_prompt_chars", defaults.get("max_prompt_chars"))
    max_prompt_tokens = role_entry.get("max_prompt_tokens", defaults.get("max_prompt_tokens"))
    retries = role_entry.get("retries", defaults.get("retries", 0))

    # Sharding configuration with defaults
    shard_mode = role_entry.get("shard_mode", defaults.get("shard_mode", "none"))
    shard_count = role_entry.get("shard_count", defaults.get("shard_count"))
    overlap_policy = role_entry.get("overlap_policy", defaults.get("overlap_policy", "warn"))
    enforce_allowed_paths = role_entry.get("enforce_allowed_paths", defaults.get("enforce_allowed_paths", False))
    max_files_per_shard = role_entry.get("max_files_per_shard", defaults.get("max_files_per_shard", 10))
    max_diff_lines_per_shard = role_entry.get("max_diff_lines_per_shard", defaults.get("max_diff_lines_per_shard", 500))
    reshard_on_timeout_124 = role_entry.get("reshard_on_timeout_124", defaults.get("reshard_on_timeout_124", True))
    max_reshard_depth = role_entry.get("max_reshard_depth", defaults.get("max_reshard_depth", 2))

    # CLI provider configuration
    cli_provider = role_entry.get("cli_provider", defaults.get("cli_provider"))
    cli_parameters_raw = role_entry.get("cli_parameters", defaults.get("cli_parameters"))
    cli_parameters = dict(cli_parameters_raw) if cli_parameters_raw else None

    return RoleConfig(
        id=role_id,
        name=str(data.get("name") or role_id),
        role=str(data["role"]),
        prompt_template=_normalize_prompt_template(data["prompt_template"], role_path),
        apply_diff=bool(role_entry.get("apply_diff", False)),
        instances=max(1, int(role_entry.get("instances", 1))),
        depends_on=_coerce_str_list(role_entry.get("depends_on")),
        timeout_sec=int(timeout_sec) if timeout_sec is not None else None,
        max_output_chars=int(max_output_chars) if max_output_chars is not None else None,
        max_prompt_chars=int(max_prompt_chars) if max_prompt_chars is not None else None,
        max_prompt_tokens=int(max_prompt_tokens) if max_prompt_tokens is not None else None,
        retries=max(0, int(retries)),
        expected_sections=_coerce_str_list(role_entry.get("expected_sections")),
        run_if_review_critical=bool(role_entry.get("run_if_review_critical", False)),
        model=str(role_entry.get("model")) if role_entry.get("model") else None,
        cli_provider=str(cli_provider) if cli_provider else None,
        cli_parameters=cli_parameters,
        # Sharding fields
        shard_mode=str(shard_mode),
        shard_count=int(shard_count) if shard_count is not None else None,
        overlap_policy=str(overlap_policy),
        enforce_allowed_paths=bool(enforce_allowed_paths),
        max_files_per_shard=int(max_files_per_shard) if max_files_per_shard is not None else None,
        max_diff_lines_per_shard=int(max_diff_lines_per_shard) if max_diff_lines_per_shard is not None else None,
        reshard_on_timeout_124=bool(reshard_on_timeout_124),
        max_reshard_depth=int(max_reshard_depth),
    )


def load_app_config(config_path: Path) -> AppConfig:
    """
    Load application config with defaults.json merge support.

    Static configs (defaults.json, cli_config.json) are loaded from static_config/.
    Family-specific configs are in agent_families/.
    """
    base_dir = config_path.parent
    # Static configs are in static_config/ directory
    static_config_dir = get_static_config_dir()
    defaults_path = static_config_dir / "defaults.json"
    cli_config_path = static_config_dir / "cli_config.json"

    # Load defaults and family config
    if not defaults_path.exists():
        raise FileNotFoundError(
            f"defaults.json not found at {defaults_path}. "
            "Please ensure static_config/defaults.json exists."
        )
    defaults = load_json(defaults_path)
    family_config = load_json(config_path)
    data = deep_merge(defaults, family_config)

    # Load CLI provider config if available
    cli_providers = {}
    if cli_config_path.exists():
        cli_config = load_json(cli_config_path)
        cli_providers = cli_config.get("cli_providers", {})

    role_defaults_data = data.get("role_defaults") or {}
    role_defaults_cfg = RoleDefaultsConfig(dict(role_defaults_data or {}))
    roles = [load_role_config(role_entry, base_dir, role_defaults_cfg) for role_entry in data["roles"]]
    final_role_id = str(data.get("final_role_id") or (roles[-1].id if roles else ""))
    coordination_raw = data.get("coordination") or {}
    outputs_raw = data.get("outputs") or {}
    task_limits = data.get("task_limits") or {}
    task_split = data.get("task_split") or {}
    streaming = data.get("streaming") or {}

    paths_cfg = PathsConfig.from_dict(data.get("paths") or {})
    outputs_cfg = OutputsConfig.from_dict(outputs_raw)
    snapshot_cfg = SnapshotConfig.from_dict(data.get("snapshot") or {})
    agent_output_cfg = AgentOutputConfig.from_dict(data.get("agent_output") or {})
    messages_cfg = MessageCatalog(dict(data.get("messages") or {}))
    diff_messages_cfg = DiffMessageCatalog(dict(data.get("diff_messages") or {}))
    cli_cfg = CliConfig.from_dict(data.get("cli") or {})
    cli_providers_cfg = CliProvidersConfig(dict(cli_providers or {}))
    prompt_limits_cfg = PromptLimitsConfig(dict(data.get("prompt_limits") or {}))
    task_limits_cfg = TaskLimitsConfig(dict(task_limits or {}))
    task_split_cfg = TaskSplitConfig(dict(task_split or {}))
    streaming_cfg = StreamingConfig(dict(streaming or {}))
    diff_safety_cfg = DiffSafetyConfig(dict(data.get("diff_safety") or {}))
    diff_apply_cfg = DiffApplyConfig(dict(data.get("diff_apply") or {}))
    logging_cfg = LoggingConfig(dict(data.get("logging") or {}))
    feedback_cfg = FeedbackLoopConfig(dict(data.get("feedback_loop") or {}))
    coordination_cfg = CoordinationConfig(
        task_board=str(coordination_raw.get("task_board") or ".multi_agent_runs/<run_id>/task_board.json"),
        channel=str(coordination_raw.get("channel") or ".multi_agent_runs/<run_id>/coordination.log"),
        lock_mode=str(coordination_raw.get("lock_mode") or "file_lock"),
        claim_timeout_sec=int(coordination_raw.get("claim_timeout_sec", 300) or 300),
        lock_timeout_sec=int(coordination_raw.get("lock_timeout_sec", 10) or 10),
    )

    return AppConfig(
        system_rules=str(data["system_rules"]),
        roles=roles,
        final_role_id=final_role_id,
        summary_max_chars=int(data.get("summary_max_chars", 1400)),
        final_summary_max_chars=int(data.get("final_summary_max_chars", 2400)),
        paths=paths_cfg,
        coordination=coordination_cfg,
        outputs=outputs_cfg,
        snapshot=snapshot_cfg,
        agent_output=agent_output_cfg,
        messages=messages_cfg,
        diff_messages=diff_messages_cfg,
        cli=cli_cfg,
        cli_providers=cli_providers_cfg,
        role_defaults=role_defaults_cfg,
        prompt_limits=prompt_limits_cfg,
        task_limits=task_limits_cfg,
        task_split=task_split_cfg,
        streaming=streaming_cfg,
        diff_safety=diff_safety_cfg,
        diff_apply=diff_apply_cfg,
        logging=logging_cfg,
        feedback_loop=feedback_cfg,
    )
