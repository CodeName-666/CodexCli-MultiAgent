from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple

from .models import AgentResult, AgentSpec
from .utils import get_status_text, write_text


class CodexClient:
    def __init__(self, codex_cmd: List[str], timeout_sec: int) -> None:
        self._codex_cmd = codex_cmd
        self._timeout_sec = timeout_sec

    async def run(self, prompt: str, workdir: Path) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *self._codex_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workdir),
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(prompt.encode("utf-8")),
                timeout=self._timeout_sec,
            )
            rc = proc.returncode or 0
            return rc, stdout_b.decode("utf-8", "replace"), stderr_b.decode("utf-8", "replace")
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
        client: CodexClient,
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
