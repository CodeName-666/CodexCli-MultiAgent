"""
CLI Executor Module

Generic subprocess execution for any CLI provider (Codex, Claude, Gemini, etc.)
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from .models import AgentResult, AgentSpec
from .utils import get_status_text, write_text


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


class AgentExecutor:
    def __init__(
        self,
        client: CLIClient,
        agent_output_cfg: Dict[str, str],
        messages: Dict[str, str],
    ) -> None:
        self._client = client
        self._agent_output_cfg = agent_output_cfg
        self._messages = messages

    async def run_agent(
        self,
        agent: AgentSpec,
        prompt: str,
        workdir: Path,
        out_file: Path,
    ) -> AgentResult:
        print(f"[Agent-Start] {agent.name} ({agent.role})")
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
        print(f"[Agent-Ende] {agent.name} rc={rc}")
        return AgentResult(agent=agent, returncode=rc, stdout=out, stderr=err, out_file=out_file)
