"""
CLI Executor Module

Generic subprocess execution for any CLI provider (Codex, Claude, Gemini, etc.)
"""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Protocol, Tuple

from .models import AgentResult, AgentSpec
from .streaming import StreamCancelled, StreamTimeout, StreamingClient
from .utils import get_status_text, write_text


class ProgressDisplay(Protocol):
    """Interface for progress display updates during streaming."""

    def update(self, chunk: str, tokens: int, elapsed: float) -> None:
        """Update progress with a streamed chunk and token count."""
        ...


@dataclass
class StreamingContext:
    """Runtime options for streaming execution and progress updates."""
    enabled: bool
    progress_display: ProgressDisplay | None = None
    cancel_event: asyncio.Event | None = None
    token_counter: Callable[[str], int] | None = None


class CLIClient:
    """
    Generic CLI client that supports multiple providers (Codex, Claude, Gemini).

    This class handles command execution with stdin support for any CLI provider.
    """

    def __init__(self, cli_cmd: List[str], timeout_sec: int, stdin_mode: bool = True) -> None:
        """
        Initialize CLI client.

        Args:
            cli_cmd: Full command to execute (e.g., ["codex", "exec", "-"] or ["claude", "-p"])
            timeout_sec: Timeout in seconds
            stdin_mode: If True, send prompt via stdin; if False, prompt is in cli_cmd
        """
        self._cli_cmd = cli_cmd
        self._timeout_sec = timeout_sec
        self._stdin_mode = stdin_mode

    async def run(self, prompt: str | None, workdir: Path) -> Tuple[int, str, str]:
        """
        Execute the CLI command with optional stdin prompt.

        Args:
            prompt: Prompt to send (via stdin or None if already in command)
            workdir: Working directory for execution

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        proc = await asyncio.create_subprocess_exec(
            *self._cli_cmd,
            stdin=asyncio.subprocess.PIPE if self._stdin_mode else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workdir),
        )
        try:
            if self._stdin_mode and prompt:
                stdin_data = prompt.encode("utf-8")
            else:
                stdin_data = None

            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(stdin_data),
                timeout=self._timeout_sec,
            )
            rc = proc.returncode or 0
            return rc, stdout_b.decode("utf-8", "replace"), stderr_b.decode("utf-8", "replace")
        except asyncio.CancelledError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            stdout_b, stderr_b = await proc.communicate()
            raise
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            stdout_b, stderr_b = await proc.communicate()
            return 124, stdout_b.decode("utf-8", "replace"), (stderr_b.decode("utf-8", "replace") + "\nTIMEOUT")

    async def run_streaming(
        self,
        prompt: str | None,
        workdir: Path,
        progress_display: ProgressDisplay | None = None,
        cancel_event: asyncio.Event | None = None,
        token_counter: Callable[[str], int] | None = None,
    ) -> Tuple[int, str, str]:
        """
        Execute the CLI command with streaming output.

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        stdin_content = prompt if self._stdin_mode and prompt else None
        progress_callback = None
        if progress_display is not None:
            def progress_callback(chunk: str, tokens: int, elapsed: float) -> None:
                progress_display.update(chunk, tokens, elapsed)

        streaming_client = StreamingClient(
            progress_callback=progress_callback,
            token_counter=token_counter,
            cancel_event=cancel_event,
        )

        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []
        try:
            async for chunk in streaming_client.stream_exec(
                self._cli_cmd,
                stdin_content,
                timeout=self._timeout_sec,
                workdir=workdir,
            ):
                if chunk.source == "stdout":
                    stdout_chunks.append(chunk.text)
                else:
                    stderr_chunks.append(chunk.text)
        except StreamTimeout:
            stderr_chunks.append("\nTIMEOUT")
            return 124, "".join(stdout_chunks), "".join(stderr_chunks)
        except StreamCancelled:
            stderr_chunks.append("\nCANCELLED")
            return 130, "".join(stdout_chunks), "".join(stderr_chunks)

        rc = streaming_client.returncode or 0
        return rc, "".join(stdout_chunks), "".join(stderr_chunks)


class AgentExecutor:
    """Execute agents via a CLI client and persist outputs."""

    def __init__(
        self,
        client: CLIClient,
        agent_output_cfg: Dict[str, str],
        messages: Dict[str, str],
    ) -> None:
        """Store dependencies for executing an agent run."""
        self._client = client
        self._agent_output_cfg = agent_output_cfg
        self._messages = messages

    async def run_agent(
        self,
        agent: AgentSpec,
        prompt: str,
        workdir: Path,
        out_file: Path,
        streaming: StreamingContext | None = None,
    ) -> AgentResult:
        """Run a single agent and return the structured result."""
        use_rich = bool(streaming and streaming.enabled and getattr(streaming.progress_display, "use_rich", False))
        if not use_rich:
            print(f"[Agent-Start] {agent.name} ({agent.role})")
        if streaming and streaming.enabled:
            rc, out, err = await self._client.run_streaming(
                prompt,
                workdir=workdir,
                progress_display=streaming.progress_display,
                cancel_event=streaming.cancel_event,
                token_counter=streaming.token_counter,
            )
        else:
            rc, out, err = await self._client.run(prompt, workdir=workdir)
        if rc == 1:
            error_detail = (err.strip() or out.strip() or "Keine Fehlerausgabe.")
            print(
                self._messages["role_rc1_error"].format(agent_name=agent.name, error=error_detail),
                file=sys.stderr,
            )
        status_text = get_status_text(rc, out, self._messages)
        content = (
            f"{self._agent_output_cfg['agent_header'].format(name=agent.name, role=agent.role)}\n\n"
            f"{self._agent_output_cfg['returncode_header']}\n{rc} ({status_text})\n\n"
            f"{self._agent_output_cfg['stdout_header']}\n{out}\n\n"
            f"{self._agent_output_cfg['stderr_header']}\n{err}\n"
        )
        write_text(out_file, content)
        if not use_rich:
            print(f"[Agent-Ende] {agent.name} rc={rc}")
        return AgentResult(agent=agent, returncode=rc, stdout=out, stderr=err, out_file=out_file)
