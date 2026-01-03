"""
Central constants and configuration paths for the multi-agent system.

Includes exit codes, default resource limits, and legacy DEFAULT_CONFIG_PATH.
"""
from __future__ import annotations

from enum import IntEnum
from pathlib import Path


# Exit codes
class ExitCode(IntEnum):
    """Standard exit codes for the application."""
    SUCCESS = 0
    RUNTIME_ERROR = 1
    VALIDATION_ERROR = 2
    CONFIG_ERROR = 3
    INTERRUPTED = 130


# Default resource limits
DEFAULT_TIMEOUT_SEC = 20 * 60  # 20 Minuten pro Agent
DEFAULT_MAX_FILES = 350        # Snapshot: max Dateien
DEFAULT_MAX_FILE_BYTES = 90_000  # Snapshot: max bytes pro Datei
DEFAULT_CONCURRENCY = 2        # Parallelität (optional)
DEFAULT_MAX_PROMPT_CHARS = 24_000
DEFAULT_MAX_OUTPUT_CHARS = 16_000
DEFAULT_RETRIES = 1
DEFAULT_SNAPSHOT_MAX_BYTES = 1_200_000
DEFAULT_SNAPSHOT_CACHE = ".multi_agent_runs/snapshot_cache.json"

# Default prompt settings
DEFAULT_TOKEN_CHARS = 4


# Path helpers
def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to the project root (parent of multi_agent/)
    """
    return Path(__file__).resolve().parent.parent


def get_static_config_dir() -> Path:
    """
    Get the static configuration directory.

    Returns:
        Path to static_config/ directory
    """
    return get_project_root() / "static_config"


def get_agent_families_dir() -> Path:
    """
    Get the agent families directory.

    Returns:
        Path to agent_families/ directory
    """
    return get_project_root() / "agent_families"


def get_defaults_path() -> Path:
    """
    Get the path to defaults.json.

    Returns:
        Path to static_config/defaults.json
    """
    return get_static_config_dir() / "defaults.json"


def get_cli_config_path() -> Path:
    """
    Get the path to cli_config.json.

    Returns:
        Path to static_config/cli_config.json
    """
    return get_static_config_dir() / "cli_config.json"


# Legacy path constant (for backward compatibility with existing code)
DEFAULT_CONFIG_PATH = get_agent_families_dir() / "developer_main.json"
