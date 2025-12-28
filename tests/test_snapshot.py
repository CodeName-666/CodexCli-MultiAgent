import tempfile
import unittest
from pathlib import Path

from multi_agent.snapshot import WorkspaceSnapshotter


class SnapshotterTest(unittest.TestCase):
    def test_skip_dirs_and_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "keep.txt").write_text("hello", encoding="utf-8")
            (root / ".mypy_cache").mkdir()
            (root / ".mypy_cache" / "skip.txt").write_text("skip", encoding="utf-8")

            cfg = {
                "skip_dirs": [".mypy_cache"],
                "skip_exts": [],
                "workspace_header": "WORKSPACE: {root}",
                "files_header": "FILES:",
                "content_header": "FILE CONTENT (truncated):",
                "file_line": "  - {rel} ({size} bytes)",
                "file_section_header": "--- {rel} ---",
                "cache_file": ".cache.json",
                "delta_snapshot": True,
            }

            snapshotter = WorkspaceSnapshotter()
            first = snapshotter.build_snapshot(root, cfg, max_files=10, max_bytes_per_file=100, task="")
            self.assertIn("keep.txt", first.text)
            self.assertNotIn("skip.txt", first.text)
            self.assertFalse(first.cache_hit)

            second = snapshotter.build_snapshot(root, cfg, max_files=10, max_bytes_per_file=100, task="")
            self.assertTrue(second.cache_hit)

    def test_delta_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file_path = root / "file.txt"
            file_path.write_text("one", encoding="utf-8")
            cfg = {
                "skip_dirs": [],
                "skip_exts": [],
                "workspace_header": "WORKSPACE: {root}",
                "files_header": "FILES:",
                "content_header": "FILE CONTENT (truncated):",
                "file_line": "  - {rel} ({size} bytes)",
                "file_section_header": "--- {rel} ---",
                "cache_file": ".cache.json",
                "delta_snapshot": True,
            }
            snapshotter = WorkspaceSnapshotter()
            _ = snapshotter.build_snapshot(root, cfg, max_files=10, max_bytes_per_file=100, task="")
            file_path.write_text("two", encoding="utf-8")
            delta = snapshotter.build_snapshot(root, cfg, max_files=10, max_bytes_per_file=100, task="")
            self.assertTrue(delta.delta_used)
            self.assertIn("file.txt", delta.text)


if __name__ == "__main__":
    unittest.main()
