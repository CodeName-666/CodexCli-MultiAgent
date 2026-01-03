"""Dataclasses and mapping wrappers for multi-agent configuration and results."""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Dict, List

from .coordination import CoordinationConfig


@dataclasses.dataclass(frozen=True)
class MappingConfig(Mapping[str, object]):
    """Mapping wrapper used by config sections."""
    values: Dict[str, object]

    def __getitem__(self, key: str) -> object:
        """Return a value by key."""
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        return iter(self.values)

    def __len__(self) -> int:
        """Return the number of stored values."""
        return len(self.values)

    def get(self, key: str, default: object | None = None) -> object | None:
        """Return a value by key with an optional default."""
        return self.values.get(key, default)

    def to_dict(self) -> Dict[str, object]:
        """Return a shallow dict copy of the values."""
        return dict(self.values)


@dataclasses.dataclass(frozen=True)
class PathsConfig:
    """Filesystem path settings for runs and snapshots."""
    run_dir: str
    snapshot_filename: str
    apply_log_filename: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PathsConfig":
        """Build a PathsConfig from raw config data."""
        data = data or {}
        return cls(
            run_dir=str(data.get("run_dir") or ".multi_agent_runs"),
            snapshot_filename=str(data.get("snapshot_filename") or "snapshot.txt"),
            apply_log_filename=str(data.get("apply_log_filename") or "apply.log"),
        )

    def __getitem__(self, key: str) -> str:
        """Return a string value by key."""
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return a string value by key with fallback."""
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class OutputsConfig:
    """Output filename pattern settings."""
    pattern: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "OutputsConfig":
        """Build an OutputsConfig from raw config data."""
        data = data or {}
        return cls(pattern=str(data.get("pattern") or "<role>_<instance>.md"))

    def __getitem__(self, key: str) -> str:
        """Return a string value by key."""
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return a string value by key with fallback."""
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class SnapshotConfig:
    """Snapshot formatting and filtering configuration."""
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
        """Build a SnapshotConfig from raw config data."""
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
        """Return a value by key."""
        return getattr(self, key)

    def get(self, key: str, default: object | None = None) -> object | None:
        """Return a value by key with fallback."""
        if hasattr(self, key):
            return getattr(self, key)
        return default


@dataclasses.dataclass(frozen=True)
class AgentOutputConfig:
    """Formatting for per-agent output files."""
    agent_header: str
    returncode_header: str
    stdout_header: str
    stderr_header: str

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AgentOutputConfig":
        """Build an AgentOutputConfig from raw config data."""
        data = data or {}
        return cls(
            agent_header=str(data.get("agent_header") or "## AGENT: {name} ({role})"),
            returncode_header=str(data.get("returncode_header") or "### Returncode"),
            stdout_header=str(data.get("stdout_header") or "### STDOUT"),
            stderr_header=str(data.get("stderr_header") or "### STDERR"),
        )

    def __getitem__(self, key: str) -> str:
        """Return a string value by key."""
        return str(getattr(self, key))

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return a string value by key with fallback."""
        if hasattr(self, key):
            return str(getattr(self, key))
        return default


@dataclasses.dataclass(frozen=True)
class CliConfig:
    """CLI metadata and arguments."""
    description: str
    args: Dict[str, object]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "CliConfig":
        """Build a CliConfig from raw config data."""
        data = data or {}
        return cls(
            description=str(data.get("description") or ""),
            args=dict(data.get("args") or {}),
        )

    def __getitem__(self, key: str) -> object:
        """Return a value by key."""
        return getattr(self, key)

    def get(self, key: str, default: object | None = None) -> object | None:
        """Return a value by key with fallback."""
        if hasattr(self, key):
            return getattr(self, key)
        return default


@dataclasses.dataclass(frozen=True)
class MessageCatalog(MappingConfig):
    """Localized message catalog."""
    pass


@dataclasses.dataclass(frozen=True)
class DiffMessageCatalog(MappingConfig):
    """Diff-related message catalog."""
    pass


@dataclasses.dataclass(frozen=True)
class RoleDefaultsConfig(MappingConfig):
    """Defaults applied to role configs."""
    pass


@dataclasses.dataclass(frozen=True)
class PromptLimitsConfig(MappingConfig):
    """Prompt limits configuration."""
    pass


@dataclasses.dataclass(frozen=True)
class TaskLimitsConfig(MappingConfig):
    """Task input sizing and truncation settings."""
    pass


@dataclasses.dataclass(frozen=True)
class TaskSplitConfig(MappingConfig):
    """Task splitting configuration."""
    pass


@dataclasses.dataclass(frozen=True)
class StreamingConfig(MappingConfig):
    """Streaming display settings."""
    pass


@dataclasses.dataclass(frozen=True)
class DiffSafetyConfig(MappingConfig):
    """Diff safety guardrails."""
    pass


@dataclasses.dataclass(frozen=True)
class DiffApplyConfig(MappingConfig):
    """Diff apply behavior settings."""
    pass


@dataclasses.dataclass(frozen=True)
class LoggingConfig(MappingConfig):
    """Structured logging configuration."""
    pass


@dataclasses.dataclass(frozen=True)
class FeedbackLoopConfig(MappingConfig):
    """Feedback loop settings for review gating."""
    pass


@dataclasses.dataclass(frozen=True)
class FormattingConfig(MappingConfig):
    """Formatting and TOON conversion settings."""
    pass


@dataclasses.dataclass(frozen=True)
class CliProvidersConfig(MappingConfig):
    """CLI provider configuration map."""
    pass


@dataclasses.dataclass(frozen=True)
class RoleConfig:
    """
    Role definition used during pipeline execution.

    Includes prompt templates, runtime limits, CLI provider overrides, and sharding.
    """
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
    Fields are organized by runtime, limits, paths, messages, CLI, defaults,
    safety, logging, and formatting settings.
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
    """Agent identity used for execution and logging."""
    name: str
    role: str


@dataclasses.dataclass
class AgentResult:
    """Execution result for a single agent instance."""
    agent: AgentSpec
    returncode: int
    stdout: str
    stderr: str
    out_file: Path

    @property
    def ok(self) -> bool:
        """Return True when the return code is zero."""
        return self.returncode == 0


@dataclasses.dataclass(frozen=True)
class Shard:
    """Shard specification for sharding tasks."""
    id: str
    title: str
    goal: str
    content: str
    allowed_paths: List[str]


@dataclasses.dataclass(frozen=True)
class ShardPlan:
    """Plan containing shard metadata for a role."""
    role_id: str
    shard_mode: str
    shard_count: int
    shards: List[Shard]
    overlap_policy: str
    enforce_allowed_paths: bool
