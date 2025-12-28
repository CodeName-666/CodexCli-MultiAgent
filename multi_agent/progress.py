from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass
class ProgressState:
    total_steps: int
    current_step: int = 0
    phase: str = ""
    detail: str = ""
    is_tty: bool = False


class ProgressReporter:
    def __init__(self, total_steps: int, is_tty: bool | None = None) -> None:
        if total_steps < 1:
            total_steps = 1
        if is_tty is None:
            is_tty = sys.stdout.isatty()
        self._state = ProgressState(total_steps=total_steps, is_tty=is_tty)

    def start(self, run_info: str) -> None:
        self._state.phase = "Start"
        self._state.detail = run_info
        self._emit_line(prefix="->")

    def step(self, phase: str, detail: str, advance: int = 1) -> None:
        self._state.current_step = min(
            self._state.current_step + max(advance, 0),
            self._state.total_steps,
        )
        self._state.phase = phase
        self._state.detail = detail
        self._emit_progress()

    def finish(self, status: str) -> None:
        self._state.phase = "Finish"
        self._state.detail = status
        self._state.current_step = self._state.total_steps
        self._emit_progress(final=True)

    def error(self, message: str) -> None:
        self._state.phase = "Error"
        self._state.detail = message
        self._emit_line(prefix="!!")

    def _emit_progress(self, final: bool = False) -> None:
        if self._state.is_tty:
            bar = self._render_bar()
            line = f"\r{bar} {self._state.phase}: {self._state.detail}"
            end = "\n" if final else ""
            sys.stdout.write(line + end)
            sys.stdout.flush()
        else:
            self._emit_line(prefix="..")

    def _emit_line(self, prefix: str) -> None:
        line = f"{prefix} {self._state.phase}: {self._state.detail}"
        print(line)

    def _render_bar(self, width: int = 30) -> str:
        filled = int(width * (self._state.current_step / self._state.total_steps))
        filled = min(max(filled, 0), width)
        bar = "#" * filled + "-" * (width - filled)
        return f"[{bar}] {self._state.current_step}/{self._state.total_steps}"
