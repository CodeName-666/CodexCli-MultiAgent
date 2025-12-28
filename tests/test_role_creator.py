import unittest

import multi_role_agent_creator as creator


class RoleCreatorTest(unittest.TestCase):
    def test_normalize_sections_preserves_codeblock_lines(self) -> None:
        sections = [
            "Header",
            "```diff",
            "diff --git a/x b/x",
            "...",
            "```",
        ]
        normalized = creator.normalize_sections(sections)
        self.assertEqual(normalized[0], "- Header")
        self.assertEqual(normalized[1], "```diff")
        self.assertEqual(normalized[2], "diff --git a/x b/x")
        self.assertEqual(normalized[3], "...")
        self.assertEqual(normalized[4], "```")

    def test_build_expected_sections_filters_non_markers(self) -> None:
        format_sections = [
            "- Foo:",
            "```diff",
            "diff --git a/x b/x",
            "...",
            "```",
        ]
        expected = creator.build_expected_sections(
            title="Title",
            format_sections=format_sections,
            include_diff_instructions=False,
            expected_override=[],
            allow_expected_diff=True,
        )
        self.assertEqual(expected, ["# Title", "- Foo:", "```diff"])

    def test_build_expected_sections_can_drop_diff_marker(self) -> None:
        format_sections = [
            "- Foo:",
            "```diff",
            "diff --git a/x b/x",
            "...",
            "```",
        ]
        expected = creator.build_expected_sections(
            title="Title",
            format_sections=format_sections,
            include_diff_instructions=True,
            expected_override=[],
            allow_expected_diff=False,
        )
        self.assertEqual(expected, ["# Title", "- Foo:"])

    def test_description_block_optional(self) -> None:
        prompt = creator.build_prompt_template(
            title="Title",
            description="Beschreibung",
            context_entries=[],
            format_sections=["- Foo:"],
            rule_lines=["- Regel"],
            include_diff_instructions=False,
            diff_text="",
            include_description=False,
            include_last_applied_diff=False,
            include_coordination=False,
            include_snapshot=False,
        )
        self.assertNotIn("BESCHREIBUNG:", prompt)
        prompt_with_description = creator.build_prompt_template(
            title="Title",
            description="Beschreibung",
            context_entries=[],
            format_sections=["- Foo:"],
            rule_lines=["- Regel"],
            include_diff_instructions=False,
            diff_text="",
            include_description=True,
            include_last_applied_diff=False,
            include_coordination=False,
            include_snapshot=False,
        )
        self.assertIn("BESCHREIBUNG:", prompt_with_description)


if __name__ == "__main__":
    unittest.main()
