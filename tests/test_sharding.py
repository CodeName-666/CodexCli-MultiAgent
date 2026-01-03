"""Unit tests for sharding module."""

import unittest
from pathlib import Path

from multi_agent.models import RoleConfig, Shard
from multi_agent.sharding import (
    create_shard_plan,
    _extract_paths_from_text,
    _extract_section_metadata,
    _group_sections_greedy,
    _plan_shards_by_headings,
)
from multi_agent.task_split import HeadingInfo


class ShardingTest(unittest.TestCase):
    """Tests for shard planning functionality."""

    def _create_test_role_config(self, shard_mode: str = "headings", instances: int = 3) -> RoleConfig:
        """Helper to create a minimal RoleConfig for testing."""
        return RoleConfig(
            id="test_role",
            name="Test Role",
            role="implementer",
            prompt_template="Task: {task}",
            apply_diff=True,
            instances=instances,
            depends_on=[],
            timeout_sec=1800,
            retries=0,
            max_prompt_chars=None,
            max_prompt_tokens=None,
            max_output_chars=None,
            expected_sections=[],
            run_if_review_critical=False,
            codex_cmd=None,
            model=None,
            shard_mode=shard_mode,
            shard_count=None,
            overlap_policy="warn",
            enforce_allowed_paths=False,
            max_files_per_shard=10,
            max_diff_lines_per_shard=500,
            reshard_on_timeout_124=True,
            max_reshard_depth=2,
        )

    def test_create_shard_plan_none_mode(self) -> None:
        """Test that shard_mode='none' returns None."""
        role_cfg = self._create_test_role_config(shard_mode="none")
        task_text = "# Task\nDo something"

        result = create_shard_plan(role_cfg, task_text)

        self.assertIsNone(result)

    def test_create_shard_plan_single_instance(self) -> None:
        """Test that single instance returns None (no sharding needed)."""
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=1)
        task_text = "# Task\nDo something"

        result = create_shard_plan(role_cfg, task_text)

        self.assertIsNone(result)

    def test_plan_shards_by_headings_basic(self) -> None:
        """Test basic heading-based sharding with 3 sections."""
        task_text = """# Chunk 1: Add config fields
## Goal
Add new RoleConfig fields

## Allowed paths
- multi_agent/models.py
- multi_agent/config_loader.py

# Chunk 2: Implement planner
## Goal
Create ShardPlanner

## Allowed paths
- multi_agent/sharding.py

# Chunk 3: Pipeline integration
## Goal
Integrate into pipeline

## Allowed paths
- multi_agent/pipeline.py
"""
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=3)

        shards = _plan_shards_by_headings(task_text, shard_count=3, role_cfg=role_cfg)

        self.assertEqual(len(shards), 3)
        self.assertEqual(shards[0].title, "Chunk 1: Add config fields")
        self.assertEqual(shards[1].title, "Chunk 2: Implement planner")
        self.assertEqual(shards[2].title, "Chunk 3: Pipeline integration")

        self.assertEqual(shards[0].goal, "Add new RoleConfig fields")
        self.assertEqual(shards[1].goal, "Create ShardPlanner")

        self.assertIn("multi_agent/models.py", shards[0].allowed_paths)
        self.assertIn("multi_agent/config_loader.py", shards[0].allowed_paths)
        self.assertIn("multi_agent/sharding.py", shards[1].allowed_paths)

    def test_plan_shards_by_headings_more_sections_than_shards(self) -> None:
        """Test greedy grouping when sections > shards."""
        task_text = """# Section 1
Content 1

# Section 2
Content 2

# Section 3
Content 3

# Section 4
Content 4
"""
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=2)

        shards = _plan_shards_by_headings(task_text, shard_count=2, role_cfg=role_cfg)

        self.assertEqual(len(shards), 2)
        self.assertIn(" / ", shards[0].title or shards[1].title)

    def test_plan_shards_no_headings(self) -> None:
        """Test that task without headings creates single shard."""
        task_text = "Just some plain text without any headings."
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=3)

        shards = _plan_shards_by_headings(task_text, shard_count=3, role_cfg=role_cfg)

        self.assertEqual(len(shards), 1)
        self.assertEqual(shards[0].title, "Full Task")
        self.assertEqual(shards[0].allowed_paths, ["**"])

    def test_extract_section_metadata(self) -> None:
        """Test extraction of goal and allowed_paths from markdown section."""
        section_text = """# Some Task

## Goal
Implement feature X

## Allowed paths
- path/to/file1.py
- path/to/file2.py

Some other content.
"""
        goal, allowed_paths = _extract_section_metadata(section_text)

        self.assertEqual(goal, "Implement feature X")
        self.assertEqual(len(allowed_paths), 2)
        self.assertIn("path/to/file1.py", allowed_paths)
        self.assertIn("path/to/file2.py", allowed_paths)

    def test_extract_section_metadata_no_markers(self) -> None:
        """Test section without goal/paths markers."""
        section_text = """# Some Task

Just regular content without special markers.
"""
        goal, allowed_paths = _extract_section_metadata(section_text)

        self.assertEqual(goal, "")
        self.assertEqual(len(allowed_paths), 0)

    def test_extract_paths_from_text(self) -> None:
        """Test path extraction heuristics."""
        text = """
Please modify the following files:
- `multi_agent/models.py`
- `multi_agent/config_loader.py`

Also check multi_agent/pipeline.py and tests/test_sharding.py.

See [documentation](docs/README.md) for details.
"""
        paths = _extract_paths_from_text(text)

        self.assertIn("multi_agent/models.py", paths)
        self.assertIn("multi_agent/config_loader.py", paths)
        self.assertIn("multi_agent/pipeline.py", paths)
        self.assertIn("tests/test_sharding.py", paths)
        self.assertIn("docs/README.md", paths)

    def test_group_sections_greedy_balancing(self) -> None:
        """Test that greedy algorithm distributes size fairly."""
        sections = [
            (HeadingInfo(1, 1, "Big Section", 1), "line\n" * 100, "Goal 1", []),
            (HeadingInfo(2, 1, "Medium Section", 102), "line\n" * 50, "Goal 2", []),
            (HeadingInfo(3, 1, "Small Section", 153), "line\n" * 10, "Goal 3", []),
        ]

        shards = _group_sections_greedy(sections, shard_count=2, preamble="")

        self.assertEqual(len(shards), 2)
        self.assertTrue(all(len(shard.content) > 0 for shard in shards))

    def test_create_shard_plan_deterministic(self) -> None:
        """Test that shard planning is deterministic (same input -> same output)."""
        task_text = """# Task 1
Content A

# Task 2
Content B

# Task 3
Content C
"""
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=3)

        plan1 = create_shard_plan(role_cfg, task_text)
        plan2 = create_shard_plan(role_cfg, task_text)

        self.assertIsNotNone(plan1)
        self.assertIsNotNone(plan2)
        self.assertEqual(plan1.shard_count, plan2.shard_count)
        self.assertEqual(len(plan1.shards), len(plan2.shards))

        for i in range(len(plan1.shards)):
            self.assertEqual(plan1.shards[i].id, plan2.shards[i].id)
            self.assertEqual(plan1.shards[i].title, plan2.shards[i].title)
            self.assertEqual(plan1.shards[i].content, plan2.shards[i].content)

    def test_create_shard_plan_with_preamble(self) -> None:
        """Test that text before first heading (preamble) is included in first shard."""
        task_text = """This is a preamble before any headings.
It should be included in the first shard.

# Task 1
Content A

# Task 2
Content B
"""
        role_cfg = self._create_test_role_config(shard_mode="headings", instances=2)

        plan = create_shard_plan(role_cfg, task_text)

        self.assertIsNotNone(plan)
        self.assertEqual(len(plan.shards), 2)
        self.assertIn("This is a preamble", plan.shards[0].content)
        self.assertNotIn("This is a preamble", plan.shards[1].content)


class DiffUtilsTest(unittest.TestCase):
    """Tests for diff_utils module."""

    def test_extract_touched_files_basic(self) -> None:
        """Test basic diff parsing."""
        from multi_agent.diff_utils import extract_touched_files_from_unified_diff

        diff_text = """--- a/multi_agent/models.py
+++ b/multi_agent/models.py
@@ -10,6 +10,8 @@
 class RoleConfig:
+    shard_mode: str = "none"
--- a/multi_agent/pipeline.py
+++ b/multi_agent/pipeline.py
@@ -100,3 +100,5 @@
+    # New code
"""
        touched = extract_touched_files_from_unified_diff(diff_text)

        self.assertEqual(len(touched), 2)
        self.assertIn("multi_agent/models.py", touched)
        self.assertIn("multi_agent/pipeline.py", touched)

    def test_extract_touched_files_ignores_dev_null(self) -> None:
        """Test that /dev/null entries are ignored."""
        from multi_agent.diff_utils import extract_touched_files_from_unified_diff

        diff_text = """--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,5 @@
+new content
"""
        touched = extract_touched_files_from_unified_diff(diff_text)

        self.assertEqual(len(touched), 1)
        self.assertIn("new_file.py", touched)

    def test_check_path_matches_globs(self) -> None:
        """Test glob pattern matching."""
        from multi_agent.diff_utils import check_path_matches_globs

        self.assertTrue(check_path_matches_globs("multi_agent/models.py", ["multi_agent/models.py"]))

        self.assertTrue(check_path_matches_globs("multi_agent/models.py", ["multi_agent/**"]))
        self.assertTrue(check_path_matches_globs("multi_agent/sub/file.py", ["multi_agent/**"]))

        self.assertTrue(check_path_matches_globs("test.py", ["*.py"]))

        self.assertFalse(check_path_matches_globs("other/file.py", ["multi_agent/**"]))

        self.assertTrue(check_path_matches_globs("anything/anywhere.txt", ["**"]))

    def test_validate_allowed_paths(self) -> None:
        """Test allowed paths validation."""
        from multi_agent.diff_utils import validate_touched_files_against_allowed_paths

        touched = {"multi_agent/models.py", "multi_agent/config_loader.py"}
        allowed = ["multi_agent/**"]

        is_valid, violations = validate_touched_files_against_allowed_paths(touched, allowed)

        self.assertTrue(is_valid)
        self.assertEqual(len(violations), 0)

    def test_validate_allowed_paths_violation(self) -> None:
        """Test detection of allowed paths violations."""
        from multi_agent.diff_utils import validate_touched_files_against_allowed_paths

        touched = {"multi_agent/models.py", "tests/test_something.py"}
        allowed = ["multi_agent/**"]

        is_valid, violations = validate_touched_files_against_allowed_paths(touched, allowed)

        self.assertFalse(is_valid)
        self.assertEqual(len(violations), 1)
        self.assertIn("tests/test_something.py", violations)

    def test_detect_file_overlaps(self) -> None:
        """Test overlap detection."""
        from multi_agent.diff_utils import detect_file_overlaps

        instance_diffs = {
            "instance1": {"file_a.py", "file_b.py"},
            "instance2": {"file_c.py"},
            "instance3": {"file_b.py", "file_d.py"},
        }

        overlaps = detect_file_overlaps(instance_diffs)

        self.assertEqual(len(overlaps), 1)
        self.assertIn("file_b.py", overlaps)
        self.assertEqual(set(overlaps["file_b.py"]), {"instance1", "instance3"})

    def test_detect_file_overlaps_none(self) -> None:
        """Test that no overlaps are detected when files are disjoint."""
        from multi_agent.diff_utils import detect_file_overlaps

        instance_diffs = {
            "instance1": {"file_a.py"},
            "instance2": {"file_b.py"},
            "instance3": {"file_c.py"},
        }

        overlaps = detect_file_overlaps(instance_diffs)

        self.assertEqual(len(overlaps), 0)


if __name__ == "__main__":
    unittest.main()
