import tempfile
import unittest
from pathlib import Path

from multi_agent.diff_applier import UnifiedDiffApplier


class DiffApplierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.messages = {
            "no_git_header": "no header",
            "patch_applied": "applied",
            "patch_applied_3way": "applied3",
            "patch_exception": "exception: {error}",
            "delete_file_error": "{rel_path}: {error}",
            "no_hunks": "{rel_path}: no hunks",
            "context_mismatch": "{rel_path}: context mismatch",
            "delete_mismatch": "{rel_path}: delete mismatch",
            "unknown_prefix": "{rel_path}: unknown prefix",
            "file_deleted": "{rel_path}: deleted",
            "file_updated": "{rel_path}: updated",
            "file_created": "{rel_path}: created",
            "blocked_path": "blocked: {path}",
            "git_apply_check_failed": "git check failed: {error}",
            "git_apply_failed": "git apply failed: {error}",
        }
        self.safety = {"blocklist": [], "allowlist": []}
        self.apply_cfg = {"use_git": False, "use_3way": False, "fallback_to_builtin": True}

    def test_apply_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "foo.txt"
            target.write_text("old\n", encoding="utf-8")
            diff = (
                "diff --git a/foo.txt b/foo.txt\n"
                "--- a/foo.txt\n"
                "+++ b/foo.txt\n"
                "@@ -1 +1 @@\n"
                "-old\n"
                "+new\n"
            )
            applier = UnifiedDiffApplier()
            ok, _ = applier.apply(root, diff, self.messages, self.safety, self.apply_cfg)
            self.assertTrue(ok)
            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")

    def test_context_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "foo.txt"
            target.write_text("old\n", encoding="utf-8")
            diff = (
                "diff --git a/foo.txt b/foo.txt\n"
                "--- a/foo.txt\n"
                "+++ b/foo.txt\n"
                "@@ -1 +1 @@\n"
                "-wrong\n"
                "+new\n"
            )
            applier = UnifiedDiffApplier()
            ok, _ = applier.apply(root, diff, self.messages, self.safety, self.apply_cfg)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
