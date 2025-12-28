from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CoordinationConfig:
    task_board: str
    channel: str
    lock_mode: str
    claim_timeout_sec: int
    lock_timeout_sec: int


class CoordinationLog:
    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, sender: str, kind: str, payload: Dict[str, object]) -> None:
        entry = {
            "ts": _utc_now(),
            "sender": sender,
            "type": kind,
            "payload": payload,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


class TaskBoard:
    def __init__(self, path: Path, lock_mode: str, lock_timeout_sec: int) -> None:
        self._path = path
        self._lock_mode = lock_mode
        self._lock_timeout_sec = lock_timeout_sec
        self._lock = asyncio.Lock()
        self._lock_path = self._path.with_suffix(self._path.suffix + ".lock")

    async def initialize(self, tasks: Iterable[Dict[str, object]]) -> None:
        data = {
            "version": 1,
            "tasks": list(tasks),
        }
        await self._write(data)

    async def update_task(self, task_id: str, updates: Dict[str, object]) -> None:
        async with self._lock:
            async with self._acquire_lock():
                data = await self._read()
                tasks = data.get("tasks", [])
                updated = False
                for task in tasks:
                    if task.get("id") == task_id:
                        task.update(updates)
                        updated = True
                        break
                if not updated:
                    tasks.append({"id": task_id, **updates})
                data["version"] = int(data.get("version", 0)) + 1
                data["tasks"] = tasks
                await self._write(data)

    async def _read(self) -> Dict[str, object]:
        if not self._path.exists():
            return {"version": 0, "tasks": []}
        raw = self._path.read_text(encoding="utf-8")
        return json.loads(raw)

    async def _write(self, data: Dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
        self._path.write_text(payload, encoding="utf-8")

    @asynccontextmanager
    async def _acquire_lock(self):
        if self._lock_mode != "file_lock":
            yield
            return
        start = time.monotonic()
        while True:
            try:
                fd = os.open(str(self._lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() - start > self._lock_timeout_sec:
                    raise TimeoutError(f"TaskBoard lock timeout: {self._lock_path}")
                await asyncio.sleep(0.05)
                continue
            else:
                os.close(fd)
                break
        try:
            yield
        finally:
            try:
                self._lock_path.unlink()
            except FileNotFoundError:
                pass
