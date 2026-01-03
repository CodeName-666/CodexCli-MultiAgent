"""Streaming helpers for real-time CLI output."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Callable, List

from .utils import estimate_tokens


@dataclass(frozen=True)
class StreamChunk:
    """Chunk of streamed output with source label."""
    source: str
    text: str


class StreamTimeout(RuntimeError):
    """Raised when streaming exceeds the timeout."""
    pass


class StreamCancelled(RuntimeError):
    """Raised when streaming is cancelled by the user."""
    pass


ProgressCallback = Callable[[str, int, float], None]
TokenCounter = Callable[[str], int]


def build_token_counter(mode: str, token_chars: int, model: str | None = None) -> TokenCounter:
    """Build a token counting function based on mode and model."""
    mode = (mode or "heuristic").strip().lower()
    if mode in {"tiktoken", "auto"}:
        try:
            import tiktoken  # type: ignore[import-not-found]
        except Exception:
            return lambda text: estimate_tokens(text, token_chars)
        try:
            encoding = tiktoken.encoding_for_model(model or "gpt-4")
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")
        return lambda text: len(encoding.encode(text))
    return lambda text: estimate_tokens(text, token_chars)


class StreamingClient:
    """Handles real-time output streaming from CLI providers."""

    def __init__(
        self,
        progress_callback: ProgressCallback | None = None,
        token_counter: TokenCounter | None = None,
        cancel_event: asyncio.Event | None = None,
        token_chars: int = 4,
        encoding: str = "utf-8",
        errors: str = "replace",
    ) -> None:
        """Initialize streaming client and counters."""
        self.progress_callback = progress_callback
        self.token_counter = token_counter or (lambda text: estimate_tokens(text, token_chars))
        self.cancel_event = cancel_event
        self.encoding = encoding
        self.errors = errors
        self.token_count = 0
        self.start_time = 0.0
        self.returncode: int | None = None

    async def stream_exec(
        self,
        cmd: List[str],
        input_text: str | None,
        timeout: int | None = None,
        workdir: Path | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Run a command and yield stdout/stderr chunks in real time."""
        self.start_time = time.monotonic()
        self.token_count = 0
        self.returncode = None

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_text is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workdir) if workdir else None,
        )

        stdout_task: asyncio.Task | None = None
        stderr_task: asyncio.Task | None = None
        sentinel = object()
        queue: asyncio.Queue[object] = asyncio.Queue()

        async def _pump(stream: asyncio.StreamReader, source: str) -> None:
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode(self.encoding, errors=self.errors)
                    self.token_count += self.token_counter(text)
                    elapsed = time.monotonic() - self.start_time
                    if self.progress_callback:
                        self.progress_callback(text, self.token_count, elapsed)
                    await queue.put(StreamChunk(source=source, text=text))
            finally:
                await queue.put((source, sentinel))

        try:
            if input_text is not None and proc.stdin:
                proc.stdin.write(input_text.encode(self.encoding, errors=self.errors))
                await proc.stdin.drain()
                proc.stdin.close()

            stdout_task = asyncio.create_task(_pump(proc.stdout, "stdout"))
            stderr_task = asyncio.create_task(_pump(proc.stderr, "stderr"))

            finished = 0
            while finished < 2:
                if timeout is not None:
                    remaining = timeout - (time.monotonic() - self.start_time)
                    if remaining <= 0:
                        raise StreamTimeout("Timeout")
                else:
                    remaining = None

                if self.cancel_event is not None:
                    if self.cancel_event.is_set():
                        raise StreamCancelled("Cancelled by user")
                    queue_task = asyncio.create_task(queue.get())
                    cancel_task = asyncio.create_task(self.cancel_event.wait())
                    pending: set[asyncio.Task] = set()
                    try:
                        done, pending = await asyncio.wait(
                            {queue_task, cancel_task},
                            timeout=remaining,
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                    finally:
                        for task in pending:
                            task.cancel()
                        if pending:
                            await asyncio.gather(*pending, return_exceptions=True)
                    if cancel_task in done:
                        raise StreamCancelled("Cancelled by user")
                    if queue_task in done:
                        item = queue_task.result()
                    else:
                        raise StreamTimeout("Timeout")
                else:
                    if remaining is not None:
                        try:
                            item = await asyncio.wait_for(queue.get(), timeout=remaining)
                        except asyncio.TimeoutError as exc:
                            raise StreamTimeout("Timeout") from exc
                    else:
                        item = await queue.get()

                if isinstance(item, tuple) and len(item) == 2 and item[1] is sentinel:
                    finished += 1
                    continue

                if isinstance(item, StreamChunk):
                    yield item

            if stdout_task:
                await stdout_task
            if stderr_task:
                await stderr_task
            self.returncode = await proc.wait()
        except (StreamTimeout, StreamCancelled):
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
            raise
        finally:
            for task in (stdout_task, stderr_task):
                if task and not task.done():
                    task.cancel()
