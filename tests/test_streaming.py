import asyncio
import sys
import unittest
from pathlib import Path

from multi_agent.executor import CLIClient
from multi_agent.streaming import StreamingClient


class StreamingClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_streaming_client_basic(self) -> None:
        cmd = [
            sys.executable,
            "-c",
            "import sys; "
            "sys.stdout.write('hello\\n'); sys.stdout.flush(); "
            "sys.stderr.write('oops\\n'); sys.stderr.flush()",
        ]
        client = StreamingClient()
        chunks = []
        async for chunk in client.stream_exec(cmd, input_text=None, timeout=5):
            chunks.append(chunk)
        self.assertEqual(client.returncode, 0)
        stdout_text = "".join(c.text for c in chunks if c.source == "stdout")
        stderr_text = "".join(c.text for c in chunks if c.source == "stderr")
        self.assertIn("hello", stdout_text)
        self.assertIn("oops", stderr_text)


class StreamingExecutorTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_streaming_timeout(self) -> None:
        cmd = [sys.executable, "-c", "import time; time.sleep(2)"]
        client = CLIClient(cmd, timeout_sec=1, stdin_mode=False)
        rc, out, err = await client.run_streaming(prompt=None, workdir=Path("."))
        self.assertEqual(rc, 124)
        self.assertIn("TIMEOUT", err)

    async def test_run_streaming_cancel(self) -> None:
        cmd = [sys.executable, "-c", "import time; print('start'); time.sleep(5)"]
        client = CLIClient(cmd, timeout_sec=10, stdin_mode=False)
        cancel_event = asyncio.Event()

        async def trigger_cancel() -> None:
            await asyncio.sleep(0.1)
            cancel_event.set()

        asyncio.create_task(trigger_cancel())
        rc, out, err = await client.run_streaming(
            prompt=None,
            workdir=Path("."),
            cancel_event=cancel_event,
        )
        self.assertEqual(rc, 130)
        self.assertIn("CANCELLED", err)


if __name__ == "__main__":
    unittest.main()
