"""Tests for multi_family_creator.py"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from multi_family_creator import (
    FamilyCreator,
    FamilyValidationError,
    build_family_spec_prompt,
    build_prompt_template_generator_prompt,
    validate_dependencies,
    parse_args,
)


class TestSlugify:
    """Test slugify function (imported from multi_role_agent_creator)."""

    def test_basic_slugify(self):
        from multi_role_agent_creator import slugify
        assert slugify("ML Model Team") == "ml_model_team"
        assert slugify("Backend API") == "backend_api"
        assert slugify("Data-Science Team") == "data_science_team"

    def test_slugify_special_chars(self):
        from multi_role_agent_creator import slugify
        assert slugify("Team@2024!") == "team_2024"
        assert slugify("A/B Testing") == "a_b_testing"


class TestValidateDependencies:
    """Test dependency validation."""

    def test_no_cycle(self):
        """Valid linear dependencies should not raise."""
        roles = [
            {"id": "a", "depends_on": []},
            {"id": "b", "depends_on": ["a"]},
            {"id": "c", "depends_on": ["b"]}
        ]
        validate_dependencies(roles)  # Should not raise

    def test_with_cycle(self):
        """Circular dependencies should raise error."""
        roles = [
            {"id": "a", "depends_on": ["c"]},
            {"id": "b", "depends_on": ["a"]},
            {"id": "c", "depends_on": ["b"]}
        ]
        with pytest.raises(FamilyValidationError, match="Dependency-Zyklus"):
            validate_dependencies(roles)

    def test_self_dependency(self):
        """Self-dependency should raise error."""
        roles = [
            {"id": "a", "depends_on": ["a"]}
        ]
        with pytest.raises(FamilyValidationError, match="Dependency-Zyklus"):
            validate_dependencies(roles)

    def test_unknown_dependency(self):
        """Dependency on non-existent role should raise."""
        roles = [
            {"id": "a", "depends_on": []},
            {"id": "b", "depends_on": ["unknown"]}
        ]
        with pytest.raises(FamilyValidationError, match="unbekannter Rolle"):
            validate_dependencies(roles)

    def test_branching_dependencies(self):
        """Branching (non-linear) dependencies should be valid."""
        roles = [
            {"id": "a", "depends_on": []},
            {"id": "b", "depends_on": ["a"]},
            {"id": "c", "depends_on": ["a"]},
            {"id": "d", "depends_on": ["b", "c"]}
        ]
        validate_dependencies(roles)  # Should not raise


class TestExtractJson:
    """Test JSON extraction from Markdown."""

    def test_extract_from_json_block(self):
        """Should extract JSON from ```json code block."""
        text = '```json\n{"key": "value"}\n```'
        creator = FamilyCreator(MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        ))
        result = creator._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_from_generic_block(self):
        """Should extract JSON from generic ``` code block."""
        text = '```\n{"key": "value"}\n```'
        creator = FamilyCreator(MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        ))
        result = creator._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_plain_json(self):
        """Should return plain JSON as-is."""
        text = '{"key": "value"}'
        creator = FamilyCreator(MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        ))
        result = creator._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_with_surrounding_text(self):
        """Should extract JSON even with surrounding text."""
        text = 'Here is the JSON:\n```json\n{"key": "value"}\n```\nEnd.'
        creator = FamilyCreator(MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        ))
        result = creator._extract_json(text)
        assert result == '{"key": "value"}'


class TestBuildFamilySpecPrompt:
    """Test family spec prompt generation."""

    def test_prompt_german(self):
        """Should generate German prompt."""
        prompt = build_family_spec_prompt(
            description="ML Team",
            template_config=None,
            template_mode="scratch",
            extra_instructions="",
            role_count_hint=5,
            lang="de"
        )
        assert "5 Rollen" in prompt
        assert "JSON" in prompt
        assert "AUFGABE:" in prompt
        assert "REGELN:" in prompt

    def test_prompt_english(self):
        """Should generate English prompt."""
        prompt = build_family_spec_prompt(
            description="ML Team",
            template_config=None,
            template_mode="scratch",
            extra_instructions="",
            role_count_hint=5,
            lang="en"
        )
        assert "5 roles" in prompt
        assert "JSON" in prompt
        assert "TASK:" in prompt
        assert "RULES:" in prompt

    def test_prompt_with_template(self):
        """Should include template when mode is clone or inspire."""
        template_config = {
            "roles": [
                {"id": "architect", "depends_on": [], "apply_diff": False},
                {"id": "implementer", "depends_on": ["architect"], "apply_diff": True}
            ],
            "final_role_id": "implementer"
        }

        prompt = build_family_spec_prompt(
            description="ML Team",
            template_config=template_config,
            template_mode="clone",
            extra_instructions="",
            role_count_hint=None,
            lang="de"
        )
        assert "TEMPLATE ZUM KLONEN" in prompt
        assert "architect" in prompt
        assert "implementer" in prompt

    def test_prompt_with_extra_instructions(self):
        """Should include extra instructions."""
        prompt = build_family_spec_prompt(
            description="ML Team",
            template_config=None,
            template_mode="scratch",
            extra_instructions="Focus on security",
            role_count_hint=None,
            lang="de"
        )
        assert "ZUSÄTZLICHE ANFORDERUNGEN" in prompt
        assert "Focus on security" in prompt


class TestBuildPromptTemplateGeneratorPrompt:
    """Test prompt template generator prompt."""

    def test_basic_role(self):
        """Should generate prompt for basic role."""
        role_spec = {
            "id": "analyst",
            "name": "Data Analyst",
            "role_label": "ML Data Scientist",
            "description": "Analyzes data",
            "depends_on": [],
            "apply_diff": False,
            "expected_sections": ["# Analysis", "- Findings:"]
        }

        prompt = build_prompt_template_generator_prompt(
            role_spec=role_spec,
            all_roles=[role_spec],
            lang="de"
        )

        assert "analyst" in prompt
        assert "Data Analyst" in prompt
        assert "{task}" in prompt
        assert "{snapshot}" in prompt
        assert "# Analysis" in prompt

    def test_role_with_dependencies(self):
        """Should include dependency placeholders."""
        role_spec = {
            "id": "implementer",
            "name": "Implementer",
            "role_label": "Code Developer",
            "description": "Implements code",
            "depends_on": ["architect"],
            "apply_diff": True,
            "expected_sections": ["# Implementation", "```diff"]
        }

        prompt = build_prompt_template_generator_prompt(
            role_spec=role_spec,
            all_roles=[role_spec],
            lang="de"
        )

        assert "{architect_summary}" in prompt
        assert "{last_applied_diff}" in prompt
        assert "unified diff" in prompt.lower()


class TestFamilyCreator:
    """Test FamilyCreator class."""

    def test_validate_family_spec_valid(self):
        """Valid spec should not raise."""
        args = MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        )
        creator = FamilyCreator(args)

        spec = {
            "family_id": "test",
            "roles": [
                {"id": "a", "description": "Test", "depends_on": []},
                {"id": "b", "description": "Test", "depends_on": ["a"]}
            ],
            "final_role_id": "b"
        }

        creator._validate_family_spec(spec)  # Should not raise

    def test_validate_family_spec_missing_field(self):
        """Missing required field should raise."""
        args = MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        )
        creator = FamilyCreator(args)

        spec = {
            "family_id": "test",
            # Missing "roles"
            "final_role_id": "b"
        }

        with pytest.raises(FamilyValidationError, match="fehlt Feld"):
            creator._validate_family_spec(spec)

    def test_validate_family_spec_invalid_final_role(self):
        """Invalid final_role_id should raise."""
        args = MagicMock(
            codex_cmd=None,
            codex_timeout_sec=180,
            output_dir="config"
        )
        creator = FamilyCreator(args)

        spec = {
            "family_id": "test",
            "roles": [
                {"id": "a", "description": "Test", "depends_on": []}
            ],
            "final_role_id": "unknown"
        }

        with pytest.raises(FamilyValidationError, match="unbekannte Rolle"):
            creator._validate_family_spec(spec)


class TestParseArgs:
    """Test argument parsing."""

    def test_required_description(self):
        """Should require --description."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_basic_args(self):
        """Should parse basic arguments."""
        args = parse_args(["--description", "Test Family"])
        assert args.description == "Test Family"
        assert args.template_mode == "scratch"
        assert args.lang == "de"
        assert args.codex_timeout_sec == 180

    def test_all_args(self):
        """Should parse all arguments."""
        args = parse_args([
            "--description", "ML Team",
            "--family-id", "ml_custom",
            "--template-from", "developer",
            "--template-mode", "clone",
            "--optimize-roles",
            "--interactive",
            "--dry-run",
            "--lang", "en",
            "--role-count", "5"
        ])

        assert args.description == "ML Team"
        assert args.family_id == "ml_custom"
        assert args.template_from == "developer"
        assert args.template_mode == "clone"
        assert args.optimize_roles is True
        assert args.interactive is True
        assert args.dry_run is True
        assert args.lang == "en"
        assert args.role_count == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
