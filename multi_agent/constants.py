from pathlib import Path

DEFAULT_TIMEOUT_SEC = 20 * 60  # 20 Minuten pro Agent
DEFAULT_MAX_FILES = 350        # Snapshot: max Dateien
DEFAULT_MAX_FILE_BYTES = 90_000  # Snapshot: max bytes pro Datei
DEFAULT_CONCURRENCY = 2        # Parallelität (optional)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "main.json"
