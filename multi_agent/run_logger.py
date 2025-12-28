from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class JsonRunLogger:
    def __init__(self, path: Path, enabled: bool = True) -> None:
        self._path = path
        self._enabled = enabled

    def log(self, event: str, payload: Dict[str, object]) -> None:
        if not self._enabled:
            return
        entry = {"event": event, "payload": payload}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
