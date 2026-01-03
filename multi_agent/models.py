from __future__ import annotations

import dataclasses
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Dict, List

from .coordination import CoordinationConfig


@dataclasses.dataclass(frozen=True)
class MappingConfig(Mapping[str, object]):
    values: Dict[str, object]

    def __getitem__(self, key: str) -> object:
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def get(self, key: str, default: object | None = None) -> object | None:
        return self.values.get(key, default)

    def to_dict(self) -> Dict[str, object]:
        return dict(self.values)


@dataclasses.dataclass(frozen=True)
class PathsConfig:
    run_dir: str
    snapshot_filename: str
    apply_log_filename: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PathsConfig":
        data = data or {}
        return cls(
            run_dir=str(data.get("run_dir") or ".multi_agent_runs"),
            snapshot_filename=str(data.get("snapshot_filename") or "snapshot.txt"),
            apply_log_filename=str(data.get("apply_log_filename") or "apply.log"),
        )

    def __getitem__(self, key: str) -> str:
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class OutputsConfig:
    pattern: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "OutputsConfig":
        data = data or {}
        return cls(pattern=str(data.get("pattern") or "<role>_<instance>.md"))

    def __getitem__(self, key: str) -> str:
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class SnapshotConfig:
    skip_dirs: List[str]
    skip_exts: List[str]
    workspace_header: str
    files_header: str
    content_header: str
    file_line: str
    file_section_header: str
    cache_file: str
    delta_snapshot: bool
    max_total_bytes: int | None
    selective_context: Dict[str, object]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SnapshotConfig":
        data = data or {}
        selective_context = data.get("selective_context") or {}
        return cls(
            skip_dirs=[str(item) for item in data.get("skip_dirs", [])],
            skip_exts=[str(item) for item in data.get("skip_exts", [])],
            workspace_header=str(data.get("workspace_header") or "WORKSPACE: {root}"),
            files_header=str(data.get("files_header") or "FILES:"),
            content_header=str(data.get("content_header") or "FILE CONTENT (truncated):"),
            file_line=str(data.get("file_line") or "  - {rel} ({size} bytes)"),
            file_section_header=str(data.get("file_section_header") or "--- {rel} ---"),
            cache_file=str(data.get("cache_file") or ""),
            delta_snapshot=bool(data.get("delta_snapshot", False)),
            max_total_bytes=int(data["max_total_bytes"]) if data.get("max_total_bytes") is not None else None,
            selective_context=dict(selective_context) if isinstance(selective_context, dict) else {"enabled": bool(selective_context)},
        )

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def get(self, key: str, default: object | None = None) -> object | None:
        if hasattr(self, key):
            return getattr(self, key)
        return default


@dataclasses.dataclass(frozen=True)
class AgentOutputConfig:
    agent_header: str
    returncode_header: str
    stdout_header: str
    stderr_header: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AgentOutputConfig":
        data = data or {}
        return cls(
            agent_header=str(data.get("agent_header") or "## AGENT: {name} ({role})"),
            returncode_header=str(data.get("returncode_header") or "### Returncode"),
            stdout_header=str(data.get("stdout_header") or "### STDOUT"),
            stderr_header=str(data.get("stderr_header") or "### STDERR"),
        )

    def __getitem__(self, key: str) -> str:
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class CliConfig:
    description: str
    args: Dict[str, object]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CliConfig":
        data = data or {}
        return cls(
            description=str(data.get("description") or ""),
            args=dict(data.get("args") or {}),
        )

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def get(self, key: str, default: object | None = None) -> object | None:
        if hasattr(self, key):
            return getattr(self, key)
        return default


@dataclasses.dataclass(frozen=True)
class MessageCatalog(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class DiffMessageCatalog(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class RoleDefaultsConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class PromptLimitsConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class TaskLimitsConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class TaskSplitConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class StreamingConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class DiffSafetyConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class DiffApplyConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class LoggingConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class FeedbackLoopConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class FormattingConfig(MappingConfig):
    pass


@dataclasses.dataclass(frozen=True)
class CliProvidersConfig(MappingConfig):
    pass


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
    model: str | None
    # CLI Provider configuration
    cli_provider: str | None = None  # "codex", "claude", "gemini" - defaults to global default
    cli_parameters: Dict[str, object] | None = None  # Provider-specific parameters
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
    """
    Main application configuration.

    Aggregates all configuration aspects of the multi-agent system.
    Contains 22 fields organized by functional area (see inline comments).
    """
    # Runtime Configuration
    system_rules: str
    roles: List[RoleConfig]
    final_role_id: str

    # Resource Limits
    summary_max_chars: int
    final_summary_max_chars: int

    # Paths & Coordination
    paths: PathsConfig
    coordination: CoordinationConfig
    outputs: OutputsConfig
    snapshot: SnapshotConfig
    agent_output: AgentOutputConfig

    # Messages & Localization
    messages: MessageCatalog
    diff_messages: DiffMessageCatalog

    # CLI & Providers
    cli: CliConfig
    cli_providers: CliProvidersConfig

    # Role & Task Defaults
    role_defaults: RoleDefaultsConfig
    prompt_limits: PromptLimitsConfig
    task_limits: TaskLimitsConfig
    task_split: TaskSplitConfig
    streaming: StreamingConfig

    # Safety & Logging
    diff_safety: DiffSafetyConfig
    diff_apply: DiffApplyConfig
    logging: LoggingConfig
    feedback_loop: FeedbackLoopConfig
    formatting: FormattingConfig


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
