from pathlib import Path

DEFAULT_TIMEOUT_SEC = 20 * 60  # 20 Minuten pro Agent
DEFAULT_MAX_FILES = 350        # Snapshot: max Dateien
DEFAULT_MAX_FILE_BYTES = 90_000  # Snapshot: max bytes pro Datei
DEFAULT_CONCURRENCY = 2        # Parallelität (optional)
DEFAULT_MAX_PROMPT_CHARS = 24_000
DEFAULT_MAX_OUTPUT_CHARS = 16_000
DEFAULT_RETRIES = 1
DEFAULT_SNAPSHOT_MAX_BYTES = 1_200_000
DEFAULT_SNAPSHOT_CACHE = ".multi_agent_runs/snapshot_cache.json"

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "developer_main.json"
