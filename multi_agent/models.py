from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Dict, List


@dataclasses.dataclass(frozen=True)
class RoleConfig:
    id: str
    name: str
    role: str
    prompt_template: str
    apply_diff: bool
    instances: int
    depends_on: List[str]
    timeout_sec: int | None
    retries: int
    max_prompt_chars: int | None
    max_prompt_tokens: int | None
    max_output_chars: int | None
    expected_sections: List[str]
    run_if_review_critical: bool
    codex_cmd: str | None
    model: str | None
    # Sharding configuration
    shard_mode: str = "none"
    shard_count: int | None = None
    overlap_policy: str = "warn"
    enforce_allowed_paths: bool = False
    max_files_per_shard: int | None = 10
    max_diff_lines_per_shard: int | None = 500
    reshard_on_timeout_124: bool = True
    max_reshard_depth: int = 2


@dataclasses.dataclass(frozen=True)
class AppConfig:
    system_rules: str
    roles: List[RoleConfig]
    final_role_id: str
    summary_max_chars: int
    final_summary_max_chars: int
    codex_env_var: str
    codex_default_cmd: str
    paths: Dict[str, str]
    coordination: Dict[str, object]
    outputs: Dict[str, object]
    snapshot: Dict[str, object]
    agent_output: Dict[str, str]
    messages: Dict[str, str]
    diff_messages: Dict[str, str]
    cli: Dict[str, object]
    role_defaults: Dict[str, object]
    prompt_limits: Dict[str, object]
    task_limits: Dict[str, object]
    task_split: Dict[str, object]
    diff_safety: Dict[str, object]
    diff_apply: Dict[str, object]
    logging: Dict[str, object]
    feedback_loop: Dict[str, object]


@dataclasses.dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str


@dataclasses.dataclass
class AgentResult:
    agent: AgentSpec
    returncode: int
    stdout: str
    stderr: str
    out_file: Path

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclasses.dataclass(frozen=True)
class Shard:
    id: str
    title: str
    goal: str
    content: str
    allowed_paths: List[str]


@dataclasses.dataclass(frozen=True)
class ShardPlan:
    role_id: str
    shard_mode: str
    shard_count: int
    shards: List[Shard]
    overlap_policy: str
    enforce_allowed_paths: bool
