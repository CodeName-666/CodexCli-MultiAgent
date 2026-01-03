#!/usr/bin/env python3
"""
multi_family_creator.py - Create complete agent families from natural language descriptions.

This tool generates:
- Main configuration file (<family>_main.json)
- All role definition files (<family>_agents/*.json)

Using Codex CLI for intelligent generation of role specs and prompt templates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

# Add parent directory to path so we can import multi_agent modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import common utilities
from multi_agent.common_utils import load_json, write_json, deep_merge, slugify
from multi_agent.constants import get_static_config_dir
from multi_agent.format_converter import FormatConversionError, build_default_converter
from creators.codex_client import call_codex, extract_payload_from_markdown

# Import from multi_role_agent_creator
from creators.multi_role_agent_creator import (
    load_config_with_defaults,
    build_description_optimization_prompt,
    resolve_output_format,
)

from multi_agent.cli_adapter import CLIAdapter
from multi_agent.utils import parse_cmd


# ============================================================================
# CLI Provider Configuration Utilities
# ============================================================================

# Provider recommendations (not automatically applied)
PROVIDER_RECOMMENDATIONS = {
    'architect': {
        'cli_provider': 'claude',
        'model': 'sonnet',
        'cli_parameters': {
            'max_turns': 3,
            'allowed_tools': 'Read,Glob,Grep'
        }
    },
    'designer': {
        'cli_provider': 'codex',
    },
    'implementer': {
        'cli_provider': 'codex',
    },
    'tester': {
        'cli_provider': 'gemini',
        'model': 'gemini-2.5-flash',
        'cli_parameters': {
            'temperature': 0.5
        }
    },
    'reviewer': {
        'cli_provider': 'claude',
        'model': 'opus',
        'cli_parameters': {
            'max_turns': 2,
            'append_system_prompt': 'Fokus: Security, Performance, Maintainability'
        }
    },
    'integrator': {
        'cli_provider': 'claude',
        'model': 'haiku',
        'cli_parameters': {
            'max_turns': 1
        }
    }
}


def detect_role_type(role_id: str) -> str:
    """Detect role type from role ID (for recommendations only)."""
    role_id_lower = role_id.lower()

    if 'architect' in role_id_lower:
        return 'architect'
    elif 'designer' in role_id_lower or 'implementer' in role_id_lower:
        return 'implementer'
    elif 'tester' in role_id_lower or 'test' in role_id_lower:
        return 'tester'
    elif 'reviewer' in role_id_lower or 'review' in role_id_lower:
        return 'reviewer'
    elif 'integrator' in role_id_lower or 'integration' in role_id_lower:
        return 'integrator'
    else:
        return 'unknown'


def get_recommendation_for_role(role_id: str) -> Dict | None:
    """Get recommended CLI configuration for a role (optional)."""
    role_type = detect_role_type(role_id)
    return PROVIDER_RECOMMENDATIONS.get(role_type)


def configure_provider_manually() -> Dict:
    """Manually configure CLI provider (interactive)."""

    # Select provider
    print("\nAvailable Providers:")
    print("  [1] codex (default)")
    print("  [2] claude")
    print("  [3] gemini")

    provider_choice = input("Select provider (1-3): ").strip()
    provider_map = {'1': 'codex', '2': 'claude', '3': 'gemini'}
    provider = provider_map.get(provider_choice, 'codex')

    config = {'cli_provider': provider}

    # Select model (if Claude or Gemini)
    model = None
    if provider == 'claude':
        print("\nClaude Models:")
        print("  [1] sonnet (balanced)")
        print("  [2] opus (highest quality)")
        print("  [3] haiku (fast & cheap)")
        model_choice = input("Select model (1-3): ").strip()
        model_map = {'1': 'sonnet', '2': 'opus', '3': 'haiku'}
        model = model_map.get(model_choice, 'sonnet')
        config['model'] = model

    elif provider == 'gemini':
        print("\nGemini Models:")
        print("  [1] gemini-2.5-flash (fast & cheap)")
        print("  [2] gemini-2.5-pro (balanced)")
        model_choice = input("Select model (1-2): ").strip()
        model_map = {'1': 'gemini-2.5-flash', '2': 'gemini-2.5-pro'}
        model = model_map.get(model_choice, 'gemini-2.5-flash')
        config['model'] = model

    # Parameters
    add_params = input("\nAdd custom parameters? (y/N): ").strip().lower()
    if add_params == 'y':
        parameters = {}
        print("Enter parameters (key=value, empty to finish):")
        while True:
            param = input("  > ").strip()
            if not param:
                break
            if '=' in param:
                key, value = param.split('=', 1)
                # Try to parse as number
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Keep as string
                parameters[key.strip()] = value

        if parameters:
            config['cli_parameters'] = parameters

    return config


# ============================================================================


class FamilyValidationError(Exception):
    """Custom exception for family validation errors."""
    pass


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        description="Create a complete agent family from natural language description."
    )

    # === REQUIRED INPUT ===
    p.add_argument(
        "--description",
        required=True,
        help="Natural language description of the family (e.g., 'A team for ML model development')"
    )

    # === FAMILY METADATA ===
    p.add_argument(
        "--family-id",
        help="Family ID (default: slugified description, e.g., 'ml_model')"
    )
    p.add_argument(
        "--family-name",
        help="Human-readable family name (default: family-id)"
    )
    p.add_argument(
        "--system-rules",
        help="Custom system rules (default: generated by Codex)"
    )

    # === TEMPLATE MODE ===
    p.add_argument(
        "--template-from",
        help="Base family to clone (e.g., 'developer', 'designer', or path to config)"
    )
    p.add_argument(
        "--template-mode",
        choices=["clone", "inspire", "scratch"],
        default="scratch",
        help="clone: Copy structure exactly; inspire: Use as reference; scratch: Start fresh (default)"
    )

    # === CODEX CONTROL ===
    p.add_argument(
        "--codex-cmd",
        help="Codex CLI command override (default: from env or 'codex exec -')"
    )
    p.add_argument(
        "--codex-timeout-sec",
        type=int,
        default=180,
        help="Timeout for Codex CLI calls (default: 180)"
    )
    p.add_argument(
        "--optimize-roles",
        action="store_true",
        help="Use Codex to optimize individual role descriptions after generation"
    )

    # === ROLE CONFIGURATION ===
    p.add_argument(
        "--role-count",
        type=int,
        help="Hint for number of roles (default: let Codex decide)"
    )
    p.add_argument(
        "--include-integrator",
        action="store_true",
        default=True,
        help="Always include an integrator/final role (default: true)"
    )
    p.add_argument(
        "--apply-diff-roles",
        help="Comma-separated role types that should apply diffs (e.g., 'implementer,tester')"
    )

    # === OUTPUT ===
    p.add_argument(
        "--output-dir",
        default="config",
        help="Output directory for family config (default: agent_families/)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate spec without writing files (outputs JSON to stdout)"
    )
    p.add_argument(
        "--interactive",
        action="store_true",
        help="Review and edit spec before writing files"
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing family files"
    )

    # === ADVANCED ===
    p.add_argument(
        "--extra-instructions",
        help="Additional instructions for Codex (e.g., 'Focus on security aspects')"
    )
    p.add_argument(
        "--lang",
        choices=["de", "en"],
        default="de",
        help="Language for prompts and outputs (default: de)"
    )

    return p.parse_args(argv)


def build_family_spec_prompt(
    description: str,
    template_config: Dict | None,
    template_mode: str,
    extra_instructions: str,
    role_count_hint: int | None,
    lang: str,
    output_format: str = "json",
    formatting: Dict[str, object] | None = None,
) -> str:
    """
    Generate prompt for Codex to create family specification.
    """
    formatting_cfg = formatting or {}
    output_label = "TOON" if output_format == "toon" else "JSON"
    template_obj = _family_spec_template(lang)
    converter = build_default_converter(formatting_cfg) if output_format == "toon" else None
    if output_format == "toon":
        template_text = converter.encode(template_obj, "toon")
        if lang == "de":
            format_note = "TOON ist eine lossless JSON-Notation. Nutze TOON, nicht JSON."
        else:
            format_note = "TOON is a lossless JSON notation. Use TOON, not JSON."
    else:
        template_text = json.dumps(template_obj, indent=2, ensure_ascii=True)
        format_note = ""

    if lang == "de":
        base_instructions = """Du bist ein Experte fuer Multi-Agent-Systeme. Erstelle eine vollstaendige Spezifikation fuer eine Agent-Familie.

AUFGABE:
Basierend auf der folgenden Beschreibung, generiere eine strukturierte Familie-Spezifikation im {output_label}-Format.

BESCHREIBUNG:
{description}

AUSGABE-FORMAT ({output_label}):
__TEMPLATE__
{format_note}

REGELN:
1. Rollen-Anzahl: {role_count_guidance}
2. Rollen-Muster: Folge typischen Workflows (Architect -> Implementer -> Validator -> Integrator)
3. Dependencies: Lineare oder Branch-Struktur (keine Zyklen!)
4. Apply-Diff: Nur fuer Rollen, die Code/Dateien aendern (Implementer, Tester, etc.)
5. Expected-Sections: Definiere klare Output-Struktur pro Rolle
6. Final-Role: Muss ein Integrator/Summarizer sein, der alle vorherigen Outputs zusammenfasst
7. Role-IDs: Lowercase mit Unterstrichen (z.B., "ml_data_analyst")
8. Instances: Default 1, nur erhoehen wenn explizit gewuenscht
9. System-Rules: Definiere klare Verhaltensregeln fuer alle Agenten dieser Familie"""
    else:
        base_instructions = """You are an expert in multi-agent systems. Create a complete specification for an agent family.

TASK:
Based on the following description, generate a structured family specification in {output_label} format.

DESCRIPTION:
{description}

OUTPUT FORMAT ({output_label}):
__TEMPLATE__
{format_note}

RULES:
1. Role count: {role_count_guidance}
2. Role patterns: Follow typical workflows (Architect -> Implementer -> Validator -> Integrator)
3. Dependencies: Linear or branching (no cycles!)
4. Apply-Diff: Only for roles that modify code/files
5. Expected-Sections: Define clear output structure per role
6. Final-Role: Must be integrator/summarizer combining all outputs
7. Role-IDs: Lowercase with underscores
8. Instances: Default 1, only increase if explicitly needed
9. System-Rules: Define clear behavioral rules for all agents in this family"""

    # Role count guidance
    if role_count_hint:
        role_count_guidance = f"{role_count_hint} Rollen" if lang == "de" else f"{role_count_hint} roles"
    else:
        role_count_guidance = "4-7 Rollen (typisch)" if lang == "de" else "4-7 roles (typical)"

    prompt_parts = [base_instructions.format(
        description=description,
        role_count_guidance=role_count_guidance,
        output_label=output_label,
        format_note=format_note,
    ).replace("__TEMPLATE__", template_text)]

    # Template mode handling
    if template_config and template_mode in ["clone", "inspire"]:
        if template_mode == "clone":
            template_text = "TEMPLATE ZUM KLONEN:\nNutze diese Struktur als Basis und passe sie an:\n" if lang == "de" else \
                          "TEMPLATE TO CLONE:\nUse this structure as base and adapt:\n"
        else:
            template_text = "TEMPLATE ALS INSPIRATION:\nLass dich davon inspirieren, aber erstelle eine neue Struktur:\n" if lang == "de" else \
                          "TEMPLATE AS INSPIRATION:\nDraw inspiration but create new structure:\n"

        template_payload = {
            "roles": [
                {
                    "id": role.get("id"),
                    "depends_on": role.get("depends_on", []),
                    "apply_diff": role.get("apply_diff", False),
                }
                for role in template_config.get("roles", [])
            ],
            "final_role_id": template_config.get("final_role_id"),
        }
        if output_format == "toon":
            template_text += converter.encode(template_payload, "toon")
        else:
            template_text += json.dumps(template_payload, indent=2)

        prompt_parts.append(template_text)

    # Extra instructions
    if extra_instructions:
        if lang == "de":
            prompt_parts.append(f"\nZUSÄTZLICHE ANFORDERUNGEN:\n{extra_instructions}")
        else:
            prompt_parts.append(f"\nADDITIONAL REQUIREMENTS:\n{extra_instructions}")

    # Final output reminder
    if lang == "de":
        prompt_parts.append(f"\nGIB NUR VALIDES {output_label} AUS. KEINE ERKLAERUNGEN AUSSERHALB DES {output_label}.")
    else:
        prompt_parts.append(f"\nOUTPUT ONLY VALID {output_label}. NO EXPLANATIONS OUTSIDE {output_label}.")

    return "\n\n".join(prompt_parts)


def build_prompt_template_generator_prompt(
    role_spec: Dict,
    all_roles: List[Dict],
    lang: str,
) -> str:
    """
    Generate prompt for Codex to create optimal prompt template for a role.
    """

    # Find dependencies
    deps = role_spec.get("depends_on", [])

    # Determine expected placeholders
    expected_placeholders = ["{task}", "{snapshot}"]
    if deps:
        expected_placeholders.extend([f"{{{dep}_summary}}" for dep in deps])
    if role_spec.get("apply_diff"):
        expected_placeholders.append("{last_applied_diff}")

    if lang == "de":
        prompt = f"""Erstelle ein Prompt-Template für folgende Agent-Rolle:

ROLLE:
ID: {role_spec['id']}
Name: {role_spec['name']}
Job Title: {role_spec['role_label']}
Beschreibung: {role_spec['description']}
Ändert Dateien: {"Ja" if role_spec.get('apply_diff') else "Nein"}

KONTEXT:
Diese Rolle ist Teil eines Multi-Agent-Workflows.
Dependencies (nutze deren Outputs): {', '.join(deps) if deps else 'Keine'}

VERFÜGBARE PLATZHALTER:
{chr(10).join(f'- {p}' for p in expected_placeholders)}

ERWARTETE OUTPUT-STRUKTUR:
{chr(10).join(role_spec.get('expected_sections', []))}

ANFORDERUNGEN AN DAS TEMPLATE:
1. Klare Struktur: FORMAT, REGELN, AUFGABE, KONTEXT-Sektionen
2. Nutze alle relevanten Platzhalter
3. Definiere explizit das erwartete Output-Format
4. Bei apply_diff=true: Fordere unified diff Format ein
5. Sei präzise und handlungsorientiert
6. Nutze die ERWARTETE OUTPUT-STRUKTUR als Grundlage für FORMAT
7. Füge {{repair_note}} Platzhalter in REGELN ein (für Fehlerbehandlung)

AUSGABE:
Gib NUR den Prompt-Template-Text aus. Keine Erklärungen, keine Anführungszeichen drumherum.
Der Text kann Platzhalter in geschweiften Klammern enthalten (z.B. {{task}})."""
    else:
        prompt = f"""Create a prompt template for the following agent role:

ROLE:
ID: {role_spec['id']}
Name: {role_spec['name']}
Job Title: {role_spec['role_label']}
Description: {role_spec['description']}
Modifies Files: {"Yes" if role_spec.get('apply_diff') else "No"}

CONTEXT:
This role is part of a multi-agent workflow.
Dependencies (use their outputs): {', '.join(deps) if deps else 'None'}

AVAILABLE PLACEHOLDERS:
{chr(10).join(f'- {p}' for p in expected_placeholders)}

EXPECTED OUTPUT STRUCTURE:
{chr(10).join(role_spec.get('expected_sections', []))}

TEMPLATE REQUIREMENTS:
1. Clear structure: FORMAT, RULES, TASK, CONTEXT sections
2. Use all relevant placeholders
3. Explicitly define expected output format
4. If apply_diff=true: Require unified diff format
5. Be precise and action-oriented
6. Use EXPECTED OUTPUT STRUCTURE as basis for FORMAT
7. Add {{repair_note}} placeholder in RULES (for error handling)

OUTPUT:
Output ONLY the prompt template text. No explanations, no quotes around it.
Text may contain placeholders in curly braces (e.g., {{task}})."""

    return prompt


def _has_cycle(node: str, graph: Dict[str, List[str]], visited: set[str], rec_stack: set[str]) -> bool:
    visited.add(node)
    rec_stack.add(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if _has_cycle(neighbor, graph, visited, rec_stack):
                return True
        elif neighbor in rec_stack:
            return True

    rec_stack.remove(node)
    return False


def validate_dependencies(roles: List[Dict]) -> None:
    """
    Validate dependency graph (no cycles, all deps exist).
    """
    role_ids = {role["id"] for role in roles}

    # Build adjacency list
    graph = {role["id"]: role.get("depends_on", []) for role in roles}

    visited: set[str] = set()
    rec_stack: set[str] = set()
    for role_id in graph:
        if role_id not in visited:
            if _has_cycle(role_id, graph, visited, rec_stack):
                raise FamilyValidationError(f"Dependency-Zyklus erkannt in Rolle: {role_id}")

    # Check if all dependencies exist
    for role in roles:
        for dep in role.get("depends_on", []):
            if dep not in role_ids:
                raise FamilyValidationError(f"Rolle {role['id']} hängt von unbekannter Rolle ab: {dep}")


def _family_spec_template(lang: str) -> Dict[str, object]:
    if lang == "de":
        role_description = "<2-4 Saetze: Was macht diese Rolle?>"
        workflow_description = "<2-3 Saetze: Wie arbeiten die Rollen zusammen?>"
        system_rules = "<System-Regeln fuer alle Agenten>"
    else:
        role_description = "<2-4 sentences: What does this role do?>"
        workflow_description = "<2-3 sentences: How do roles work together?>"
        system_rules = "<System rules for all agents>"
    return {
        "family_id": "<slug_name>",
        "family_name": "<Human Readable Name>",
        "system_rules": system_rules,
        "roles": [
            {
                "id": "<role_id>",
                "name": "<Role Name>",
                "role_label": "<Job Title>",
                "description": role_description,
                "depends_on": ["<other_role_id>"],
                "apply_diff": "<true_or_false>",
                "instances": 1,
                "expected_sections": ["# Title", "- Section 1:", "- Section 2:"],
                "timeout_sec": "<optional override>",
            }
        ],
        "final_role_id": "<id_of_last_role>",
        "workflow_description": workflow_description,
    }


class FamilyCreator:
    """
    Main class for family creation.
    """

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config_path = Path(args.output_dir).resolve()
        defaults_path = get_static_config_dir() / "defaults.json"
        defaults = load_json(defaults_path) if defaults_path.exists() else {}
        self.formatting_cfg = dict(defaults.get("formatting") or {})
        self.output_format = resolve_output_format({"formatting": self.formatting_cfg})

        # CLI Client Setup via CLIAdapter
        if args.codex_cmd:
            self.codex_cmd = parse_cmd(args.codex_cmd)
        else:
            cli_adapter = CLIAdapter(get_static_config_dir() / "cli_config.json")
            self.codex_cmd, _, _ = cli_adapter.build_command_for_role(
                provider_id=None, prompt=None, model=None, timeout_sec=None
            )

        self.timeout_sec = args.codex_timeout_sec

    def run(self) -> None:
        """
        Main workflow.
        """
        # PHASE 1: Load template (if requested)
        template_config = None
        if self.args.template_from:
            template_config = self._load_template(self.args.template_from)
            print(f"Template geladen: {self.args.template_from}")

        # PHASE 2: Generate family spec
        print("Generiere Familie-Spezifikation via Codex...")
        family_spec = self._generate_family_spec(template_config)

        # PHASE 3: Interactive review (optional)
        if self.args.interactive:
            family_spec = self._interactive_review(family_spec)

        # PHASE 4: Dry-run check
        if self.args.dry_run:
            print(json.dumps(family_spec, indent=2, ensure_ascii=False))
            return

        # PHASE 5: Optimize role descriptions (optional)
        if self.args.optimize_roles:
            print("Optimiere Rollen-Beschreibungen...")
            family_spec = self._optimize_role_descriptions(family_spec)

        # PHASE 6: Generate prompt templates
        print("Generiere Prompt-Templates für Rollen...")
        family_spec = self._generate_prompt_templates(family_spec)

        # PHASE 6.5: Configure CLI providers
        family_spec = self._configure_cli_providers(family_spec)

        # PHASE 7: Write files
        print("Schreibe Familie-Konfiguration...")
        self._write_family_files(family_spec)

    def _extract_json(self, text: str) -> str:
        return extract_payload_from_markdown(text, "json")

        print(f"\n✓ Familie erstellt: {family_spec['family_id']}")
        print(f"  Haupt-Config: {self.config_path}/{family_spec['family_id']}_main.json")
        print(f"  Rollen-Dir:   {self.config_path}/{family_spec['family_id']}_agents/")

    def _load_template(self, template_ref: str) -> Dict:
        """
        Load template config from known family or path.
        """
        # Known families
        known_families = ["developer", "designer", "docs", "qa", "devops",
                         "security", "product", "data", "research"]

        if template_ref in known_families:
            template_path = self.config_path / f"{template_ref}_main.json"
        else:
            template_path = Path(template_ref).resolve()

        if not template_path.exists():
            raise FileNotFoundError(f"Template nicht gefunden: {template_path}")

        return load_json(template_path)

    def _generate_family_spec(self, template_config: Dict | None) -> Dict:
        """
        Generate family spec via Codex.
        """
        prompt = build_family_spec_prompt(
            description=self.args.description,
            template_config=template_config,
            template_mode=self.args.template_mode,
            extra_instructions=self.args.extra_instructions or "",
            role_count_hint=self.args.role_count,
            lang=self.args.lang,
            output_format=self.output_format,
            formatting=self.formatting_cfg,
        )

        stdout = call_codex(prompt, self.codex_cmd, self.timeout_sec)

        # Parse output
        try:
            payload_text = extract_payload_from_markdown(stdout, self.output_format)
            if self.output_format == "toon":
                converter = build_default_converter(self.formatting_cfg)
                family_spec = converter.decode(payload_text, "toon")
            else:
                family_spec = json.loads(payload_text)
        except (FormatConversionError, json.JSONDecodeError, ValueError) as exc:
            print(f"Fehler: Codex lieferte invalides {self.output_format.upper()}:\n{stdout}", file=sys.stderr)
            raise RuntimeError(f"{self.output_format.upper()} Parse Error: {exc}") from exc

        # Apply overrides
        if self.args.family_id:
            family_spec["family_id"] = slugify(self.args.family_id)
        else:
            family_spec["family_id"] = slugify(family_spec.get("family_id", self.args.description))

        if self.args.family_name:
            family_spec["family_name"] = self.args.family_name

        if self.args.system_rules:
            family_spec["system_rules"] = self.args.system_rules

        # Validation
        self._validate_family_spec(family_spec)

        # Clone from template if mode is clone
        if template_config and self.args.template_mode == "clone":
            family_spec = self._clone_from_template(template_config, family_spec)

        return family_spec

    def _validate_family_spec(self, spec: Dict) -> None:
        """
        Validate family spec structure.
        """
        required = ["family_id", "roles", "final_role_id"]
        for field in required:
            if field not in spec:
                raise FamilyValidationError(f"Familie-Spec fehlt Feld: {field}")

        if not spec["roles"]:
            raise FamilyValidationError("Familie muss mindestens eine Rolle haben")

        # Validate roles
        role_ids = {role["id"] for role in spec["roles"]}

        for role in spec["roles"]:
            if "id" not in role or "description" not in role:
                raise FamilyValidationError(f"Rolle fehlt erforderliche Felder: {role}")

        # Validate dependencies
        validate_dependencies(spec["roles"])

        # Validate final_role_id
        if spec["final_role_id"] not in role_ids:
            raise FamilyValidationError(f"final_role_id verweist auf unbekannte Rolle: {spec['final_role_id']}")

    def _clone_from_template(self, template_config: Dict, spec: Dict) -> Dict:
        """
        Clone family structure from template.
        """
        # Map old role IDs to new
        role_id_map = {}
        cloned_roles = []

        for idx, template_role_entry in enumerate(template_config["roles"]):
            # Load template role
            template_role_path = self.config_path / template_role_entry["file"]

            if not template_role_path.exists():
                print(f"Warnung: Template-Rolle nicht gefunden: {template_role_path}", file=sys.stderr)
                continue

            template_role = load_json(template_role_path)

            # Create new role with mapped ID
            if idx < len(spec["roles"]):
                new_id = spec["roles"][idx]["id"]
            else:
                new_id = f"{spec['family_id']}_{template_role['id']}"

            role_id_map[template_role["id"]] = new_id

            cloned_role = {
                "id": new_id,
                "name": spec["roles"][idx].get("name", template_role["name"]) if idx < len(spec["roles"]) else template_role["name"],
                "role_label": spec["roles"][idx].get("role_label", template_role["role"]) if idx < len(spec["roles"]) else template_role["role"],
                "description": spec["roles"][idx]["description"] if idx < len(spec["roles"]) else template_role.get("description", ""),
                "prompt_template": "",  # Will be regenerated
                "apply_diff": template_role_entry.get("apply_diff", False),
                "depends_on": template_role_entry.get("depends_on", []),
                "instances": template_role_entry.get("instances", 1),
                "expected_sections": template_role_entry.get("expected_sections", []),
                "timeout_sec": template_role_entry.get("timeout_sec")
            }

            cloned_roles.append(cloned_role)

        # Map dependencies
        for role in cloned_roles:
            role["depends_on"] = [role_id_map.get(dep, dep) for dep in role["depends_on"]]

        spec["roles"] = cloned_roles
        spec["final_role_id"] = role_id_map.get(template_config["final_role_id"], spec["final_role_id"])

        return spec

    def _interactive_review(self, spec: Dict) -> Dict:
        """
        Interactive review with edit capability.
        """
        # Write spec to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)
            temp_path = f.name

        print(f"\nÖffne Editor für Review: {temp_path}")
        print("Speichere und schließe den Editor, um fortzufahren.")

        # Open editor (use EDITOR env var or fallback)
        editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")
        subprocess.run([editor, temp_path], check=True)

        # Load edited version
        with open(temp_path, 'r', encoding='utf-8') as f:
            edited_spec = json.load(f)

        os.unlink(temp_path)

        # Re-validate
        self._validate_family_spec(edited_spec)

        return edited_spec

    def _optimize_role_descriptions(self, spec: Dict) -> Dict:
        """
        Optimize role descriptions via Codex (uses existing function).
        """
        for role in spec["roles"]:
            print(f"  Optimiere: {role['id']}...")

            prompt = build_description_optimization_prompt(
                description=role["description"],
                extra_instructions=""
            )

            optimized = call_codex(prompt, self.codex_cmd, self.timeout_sec)
            role["description"] = optimized.strip()

        return spec

    def _generate_prompt_templates(self, spec: Dict) -> Dict:
        """
        Generate prompt templates for all roles.
        """
        for role in spec["roles"]:
            print(f"  Generiere Template: {role['id']}...")

            prompt = build_prompt_template_generator_prompt(
                role_spec=role,
                all_roles=spec["roles"],
                lang=self.args.lang,
            )

            template = call_codex(prompt, self.codex_cmd, self.timeout_sec)
            role["prompt_template"] = template.strip()

        return spec

    def _configure_cli_providers(self, spec: Dict) -> Dict:
        """
        Optionally configure CLI providers for all roles.

        Asks user if they want to configure CLI providers.
        - If yes: Interactive configuration for each role
        - If no: Set all roles to 'codex' (default)
        """
        print("\n" + "=" * 60)
        print("CLI Provider Configuration")
        print("=" * 60)
        print("\nWould you like to configure CLI providers for the roles?")
        print("  - codex (default): OpenAI Codex CLI")
        print("  - claude: Anthropic Claude Code CLI")
        print("  - gemini: Google Gemini CLI")
        print("\nIf you skip this, all roles will use 'codex' as default.")

        configure = input("\nConfigure CLI providers? (y/N): ").strip().lower()

        if configure != 'y':
            # Set all to codex (default)
            print("[INFO] Skipping CLI provider configuration. All roles will use default (codex).")
            for role in spec["roles"]:
                role['cli_provider'] = 'codex'
            return spec

        # Interactive configuration for each role
        print(f"\n{len(spec['roles'])} roles to configure.\n")

        for role in spec["roles"]:
            role_id = role['id']

            # Show role info
            print(f"\n{'=' * 60}")
            print(f"Role: {role_id}")
            print(f"Description: {role.get('description', 'N/A')[:80]}...")
            print(f"{'=' * 60}")

            # Show recommendation
            recommendation = get_recommendation_for_role(role_id)
            if recommendation:
                rec_provider = recommendation.get('cli_provider', 'codex')
                rec_model = recommendation.get('model', 'default')
                rec_params = recommendation.get('cli_parameters', {})
                rec_str = f"{rec_provider}"
                if rec_model != 'default':
                    rec_str += f"/{rec_model}"
                if rec_params:
                    param_strs = [f"{k}={v}" for k, v in rec_params.items()]
                    rec_str += f" ({', '.join(param_strs)})"
                print(f"Recommendation: {rec_str}")
            else:
                print(f"Recommendation: codex (default)")
                recommendation = {'cli_provider': 'codex'}

            # Options
            print("\nOptions:")
            print("  [1] Use codex (default)")
            print("  [2] Configure manually")
            if recommendation:
                print("  [3] Use recommendation")

            choice = input("\nSelect option (1-3): ").strip()

            if choice == '1':
                # Use codex
                role['cli_provider'] = 'codex'
                print("[OK] Using codex")

            elif choice == '2':
                # Configure manually
                config = configure_provider_manually()
                role.update(config)
                print(f"[OK] Configured: {config}")

            elif choice == '3' and recommendation:
                # Use recommendation
                role.update(recommendation)
                print("[OK] Using recommendation")

            else:
                # Default to codex
                role['cli_provider'] = 'codex'
                print("[WARNING] Invalid choice, using default (codex)")

        print(f"\n{'=' * 60}")
        print("[OK] CLI provider configuration complete")
        print(f"{'=' * 60}")

        return spec

    def _write_family_files(self, spec: Dict) -> None:
        """
        Write all files (main.json + role JSONs).
        """
        family_id = slugify(spec["family_id"])
        roles_dir = self.config_path / f"{family_id}_roles"
        main_path = self.config_path / f"{family_id}_main.json"

        # Check if family already exists
        if main_path.exists() and not self.args.force:
            raise FileExistsError(
                f"Familie existiert bereits: {main_path}\n"
                f"Nutze --force zum Überschreiben"
            )

        # Create roles directory
        roles_dir.mkdir(parents=True, exist_ok=True)

        # Write role JSONs
        role_entries = []
        for role in spec["roles"]:
            role_id = role["id"]
            role_file = roles_dir / f"{role_id}.json"

            role_json = {
                "id": role_id,
                "name": role.get("name", role_id),
                "role": role.get("role_label", role_id),
                "prompt_template": role["prompt_template"]
            }

            write_json(role_file, role_json)

            # Create entry for main.json
            entry = {
                "id": role_id,
                "file": f"{family_id}_agents/{role_id}.json",
                "instances": role.get("instances", 1),
                "depends_on": role.get("depends_on", [])
            }

            if role.get("apply_diff"):
                entry["apply_diff"] = True

            if role.get("expected_sections"):
                entry["expected_sections"] = role["expected_sections"]

            if role.get("timeout_sec"):
                entry["timeout_sec"] = role["timeout_sec"]

            # Add CLI provider configuration
            if role.get("cli_provider"):
                entry["cli_provider"] = role["cli_provider"]

            if role.get("model"):
                entry["model"] = role["model"]

            if role.get("cli_parameters"):
                entry["cli_parameters"] = role["cli_parameters"]

            role_entries.append(entry)

        # Write main.json
        main_config = self._build_main_config(spec, role_entries)
        write_json(main_path, main_config)

    def _build_main_config(self, spec: Dict, role_entries: List[Dict]) -> Dict:
        """
        Build family-specific main configuration.

        Requires defaults.json in static_config/ directory.
        Only family-specific values are written to the config file.
        """
        defaults_path = self.config_path.parent / "static_config" / "defaults.json"

        if not defaults_path.exists():
            raise FileNotFoundError(
                f"defaults.json not found at {defaults_path}. "
                "Please ensure static_config/defaults.json exists."
            )

        family_id = spec["family_id"]
        main_config = {
            "final_role_id": spec["final_role_id"],
            "roles": role_entries,
            "cli": {
                "description": f"Multi-Agent Orchestrator für {spec.get('family_name', family_id)}."
            },
            "diff_safety": {
                "allowlist": [
                    f"agent_families/{family_id}_main.json",
                    f"agent_families/{family_id}_agents/*"
                ]
            }
        }

        return main_config


def main(argv: List[str] | None = None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    try:
        creator = FamilyCreator(args)
        creator.run()
        return 0
    except (FamilyValidationError, RuntimeError, FileNotFoundError, FileExistsError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAbgebrochen.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
