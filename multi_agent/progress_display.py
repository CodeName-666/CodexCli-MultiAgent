"""Optional rich progress display for streaming agent output."""

from __future__ import annotations

import time
from typing import List


try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    RICH_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    Console = Group = Panel = Progress = SpinnerColumn = BarColumn = TextColumn = object
    RICH_AVAILABLE = False


class AgentProgressDisplay:
    """Progress display for agent execution (rich when available)."""

    def __init__(
        self,
        refresh_rate_hz: int = 4,
        output_preview_lines: int = 10,
        buffer_max_lines: int = 1000,
        expected_tokens: int = 0,
        stream_label: str = "",
        force_plain: bool = False,
    ) -> None:
        """Initialize display settings and buffering state."""
        self.refresh_rate_hz = max(1, int(refresh_rate_hz))
        self.output_preview_lines = max(1, int(output_preview_lines))
        self.buffer_max_lines = max(50, int(buffer_max_lines))
        self.expected_tokens = max(0, int(expected_tokens))
        self.stream_label = stream_label

        self.output_buffer: List[str] = []
        self.token_count = 0
        self.start_time = time.monotonic()
        self.current_task = None
        self.should_cancel = False

        self.use_rich = bool(RICH_AVAILABLE and not force_plain)
        self.console = Console() if self.use_rich else None
        if self.use_rich:
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("tokens: {task.fields[tokens]}"),
                TextColumn("elapsed: {task.fields[elapsed]}"),
                console=self.console,
                auto_refresh=False,
            )
        else:
            self.progress = None

    def __rich__(self) -> Group:
        """Return a rich renderable for live updates."""
        if not self.use_rich:
            return Group()
        return self.render()

    def start_agent(self, agent_name: str) -> None:
        """Start tracking a new agent stream."""
        self.start_time = time.monotonic()
        if not self.stream_label:
            self.stream_label = agent_name
        if not self.use_rich:
            print(f"[Streaming] {agent_name}")
            return
        self.current_task = self.progress.add_task(
            f"Running {agent_name}...",
            total=100,
            tokens=0,
            elapsed="0s",
        )

    def update(self, chunk: str, tokens: int, elapsed: float) -> None:
        """Update the display with streaming data."""
        self.token_count = tokens
        if not self.use_rich:
            if chunk:
                self._print_plain(chunk)
            return
        if chunk:
            self._add_to_buffer(chunk)
        if self.current_task is None:
            return
        progress_pct = self._estimate_progress(tokens)
        self.progress.update(
            self.current_task,
            completed=progress_pct,
            tokens=tokens,
            elapsed=f"{int(elapsed)}s",
        )

    def render(self) -> Group:
        """Render the progress display as a rich Group."""
        if not self.use_rich:
            return Group()
        output_preview = "\n".join(self.output_buffer[-self.output_preview_lines :]) or "(no output yet)"
        output_panel = Panel(
            output_preview,
            title="Live Output",
            border_style="cyan",
        )
        return Group(self.progress, output_panel)

    def _estimate_progress(self, tokens: int) -> float:
        """Estimate progress percentage from token count."""
        if self.expected_tokens <= 0:
            return 50.0
        progress = (tokens / self.expected_tokens) * 100
        return min(95.0, progress)

    def _add_to_buffer(self, text: str) -> None:
        """Append output text to the buffered preview."""
        lines = text.splitlines()
        if not lines and text:
            lines = [text]
        self.output_buffer.extend(lines)
        if len(self.output_buffer) <= self.buffer_max_lines:
            return
        keep_head = 100
        keep_tail = self.buffer_max_lines - keep_head - 1
        if keep_tail < 1:
            self.output_buffer = self.output_buffer[-self.buffer_max_lines :]
            return
        self.output_buffer = (
            self.output_buffer[:keep_head]
            + ["... (output truncated) ..."]
            + self.output_buffer[-keep_tail:]
        )

    def _print_plain(self, text: str) -> None:
        """Print streaming output in plain text mode."""
        label = self.stream_label.strip()
        prefix = f"[{label}] " if label else ""
        lines = text.splitlines()
        if not lines and text:
            lines = [text]
        for line in lines:
            print(f"{prefix}{line}", flush=True)
