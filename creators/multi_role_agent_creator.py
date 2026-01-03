#!/usr/bin/env python3
"""
multi_role_agent_creator.py - create a new role JSON and register it in a main config.

Uses Natural Language mode to generate role specifications via LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path so we can import multi_agent modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from multi_agent.cli_adapter import CLIAdapter
from multi_agent.common_utils import load_json, write_json, deep_merge, slugify
from multi_agent.constants import get_static_config_dir, DEFAULT_CONFIG_PATH
from multi_agent.format_converter import FormatConversionError, build_default_converter
from multi_agent.utils import parse_cmd
from creators.codex_client import call_codex, extract_payload_from_markdown

# Constants
DEFAULT_FORMAT_SECTIONS = ["- Aufgaben:", "- Entscheidungen:", "- Offene Punkte:"]
DEFAULT_RULE_LINES = [
    "Ausgabe muss exakt diese Abschnittsmarker enthalten.",
    "Wenn FEHLENDE SEKTIONEN angegeben sind, korrigiere das Format.",
]
DEFAULT_DIFF_TEXT = "Dann liefere einen UNIFIED DIFF (git-style) für alle Änderungen:"


def load_config_with_defaults(config_path: Path) -> Dict[str, object]:
    """
    Load config with defaults.json merge support.

    Requires defaults.json in static_config/ directory.
    Family config values override defaults.
    """
    defaults_path = get_static_config_dir() / "defaults.json"

    if not defaults_path.exists():
        raise FileNotFoundError(
            f"defaults.json not found at {defaults_path}. "
            "Please ensure static_config/defaults.json exists."
        )

    defaults = load_json(defaults_path)
    family_config = load_json(config_path)
    return deep_merge(defaults, family_config)


def resolve_output_format(config: Dict[str, object]) -> str:
    formatting_cfg = config.get("formatting") or {}
    if isinstance(formatting_cfg, dict):
        if bool(formatting_cfg.get("enabled", False)) and bool(formatting_cfg.get("output_json_as_toon", False)):
            return "toon"
    return "json"


def _role_spec_template(lang: str) -> Dict[str, object]:
    if lang == "de":
        description = "<2-4 Saetze: Was macht diese Rolle?>"
        diff_text = "<Text fuer Diff-Anweisung> (optional)"
        format_sections = ["- Aufgaben:", "- Entscheidungen:", "- Offene Punkte:"]
        rule_lines = ["Regel 1", "Regel 2"]
        arch_label = "ARCHITEKTUR (Kurz)"
    else:
        description = "<2-4 sentences: What does this role do?>"
        diff_text = "<Text for diff instructions> (optional)"
        format_sections = ["- Tasks:", "- Decisions:", "- Open Points:"]
        rule_lines = ["Rule 1", "Rule 2"]
        arch_label = "ARCHITECTURE (Short)"
    return {
        "id": "<role_id>",
        "name": "<Role Name>",
        "role_label": "<Job Title>",
        "title": "<Prompt Title>",
        "description": description,
        "apply_diff": "<true_or_false>",
        "expected_sections": ["# Title", "- Section 1:", "- Section 2:"],
        "format_sections": format_sections,
        "rule_lines": rule_lines,
        "context_entries": [
            {"key": "architect_summary", "label": arch_label},
            {"key": "snapshot", "label": "WORKSPACE"},
        ],
        "diff_instructions": diff_text,
        "depends_on": ["<other_role_id>"],
        "timeout_sec": "<optional override>",
        "max_output_chars": "<optional override>",
    }


def resolve_role_path(base_dir: Path, role_file: str) -> Tuple[Path, str]:
    """Resolve role file path to absolute and relative paths."""
    raw_path = Path(role_file)
    if raw_path.is_absolute():
        file_path = raw_path
        try:
            rel_path = str(file_path.relative_to(base_dir))
        except ValueError:
            rel_path = str(file_path)
    else:
        file_path = base_dir / raw_path
        rel_path = str(raw_path)
    return file_path, rel_path.replace("\\", "/")


def insert_role_entry(
    roles: List[Dict[str, object]],
    entry: Dict[str, object],
    insert_after: str | None,
    final_role_id: str | None,
) -> List[Dict[str, object]]:
    """Insert role entry into roles list at appropriate position."""
    if insert_after:
        for idx, role in enumerate(roles):
            if role.get("id") == insert_after:
                return roles[: idx + 1] + [entry] + roles[idx + 1 :]
        raise ValueError(f"insert-after role id not found: {insert_after}")
    if final_role_id:
        for idx, role in enumerate(roles):
            if role.get("id") == final_role_id:
                return roles[:idx] + [entry] + roles[idx:]
    return roles + [entry]


def build_prompt_template(
    title: str,
    description: str,
    context_entries: List[Tuple[str, str]],
    format_sections: List[str],
    rule_lines: List[str],
    include_diff_instructions: bool,
    diff_text: str,
    include_description: bool,
    include_last_applied_diff: bool,
    include_coordination: bool,
    include_snapshot: bool,
) -> str:
    """Build prompt template from role specification."""
    safe_title = title.replace("{", "{{").replace("}", "}}")
    safe_description = description.replace("{", "{{").replace("}", "}}")
    lines: List[str] = []
    lines.append("FORMAT (STRICT):")
    lines.append(f"# {safe_title}")
    lines.extend(format_sections)
    if include_diff_instructions:
        safe_diff_text = diff_text.replace("{", "{{").replace("}", "}}").strip()
        lines.append("")
        lines.append(safe_diff_text or DEFAULT_DIFF_TEXT)
        lines.append("```diff")
        lines.append("diff --git a/<path> b/<path>")
        lines.append("...")
        lines.append("```")
    lines.append("")
    lines.append("REGELN:")
    lines.extend(rule_lines)
    lines.append("{repair_note}")
    if include_description:
        lines.append("")
        lines.append("BESCHREIBUNG:")
        lines.append(safe_description.strip())
    lines.append("")
    lines.append("AUFGABE:")
    lines.append("{task}")
    for key, label in context_entries:
        safe_label = label.replace("{", "{{").replace("}", "}}")
        lines.append("")
        lines.append(f"{safe_label}:")
        lines.append(f"{{{key}}}")
    if include_last_applied_diff:
        lines.append("")
        lines.append("LAST APPLIED DIFF (optional):")
        lines.append("{last_applied_diff}")
    if include_coordination:
        lines.append("")
        lines.append("KOORDINATION (Task-Board & Log):")
        lines.append("Task-Board: {task_board_path}")
        lines.append("Log: {coordination_log_path}")
    if include_snapshot:
        lines.append("")
        lines.append("KONTEXT (Workspace Snapshot):")
        lines.append("{snapshot}")
    return "\n".join(lines) + "\n"


def build_role_spec_prompt(
    description: str,
    family_context: str,
    lang: str,
    extra_instructions: str,
    output_format: str = "json",
    formatting: Dict[str, object] | None = None,
) -> str:
    """
    Generate prompt for Codex to create role specification from natural language.

    Similar to build_family_spec_prompt but for a single role.
    """
    formatting_cfg = formatting or {}
    output_label = "TOON" if output_format == "toon" else "JSON"
    template_obj = _role_spec_template(lang)
    if output_format == "toon":
        converter = build_default_converter(formatting_cfg)
        template_text = converter.encode(template_obj, "toon")
        if lang == "de":
            format_note = "TOON ist eine lossless JSON-Notation. Nutze TOON, nicht JSON."
        else:
            format_note = "TOON is a lossless JSON notation. Use TOON, not JSON."
    else:
        template_text = json.dumps(template_obj, indent=2, ensure_ascii=True)
        format_note = ""

    if lang == "de":
        base_instructions = """Du bist ein Experte fuer Multi-Agent-Systeme. Erstelle eine vollstaendige Spezifikation fuer eine einzelne Agent-Rolle.

AUFGABE:
Basierend auf der folgenden Beschreibung, generiere eine strukturierte Rollen-Spezifikation im {output_label}-Format.

BESCHREIBUNG:
{description}

KONTEXT (Familie):
{family_context}

AUSGABE-FORMAT ({output_label}):
__TEMPLATE__
{format_note}

REGELN:
1. Role-ID: Lowercase mit Unterstrichen (z.B., "code_reviewer")
2. Apply-Diff: true nur wenn diese Rolle Code/Dateien aendert
3. Expected-Sections: Definiere klare Output-Struktur
4. Format-Sections: Strukturiere das erwartete Output-Format
5. Context-Entries: Welche Inputs benoetigt die Rolle? (task + snapshot sind immer dabei)
6. Dependencies: Falls die Rolle Output anderer Rollen braucht
7. Diff-Instructions: Falls apply_diff=true, definiere Diff-Format-Anweisungen
8. Description: Handlungsorientiert, praezise in 2-4 Saetzen"""
    else:
        base_instructions = """You are an expert in multi-agent systems. Create a complete specification for a single agent role.

TASK:
Based on the following description, generate a structured role specification in {output_label} format.

DESCRIPTION:
{description}

CONTEXT (Family):
{family_context}

OUTPUT FORMAT ({output_label}):
__TEMPLATE__
{format_note}

RULES:
1. Role-ID: Lowercase with underscores (e.g., "code_reviewer")
2. Apply-Diff: true only if role modifies code/files
3. Expected-Sections: Define clear output structure
4. Format-Sections: Structure the expected output format
5. Context-Entries: What inputs does the role need? (task + snapshot always included)
6. Dependencies: If role needs output from other roles
7. Diff-Instructions: If apply_diff=true, define diff format instructions
8. Description: Action-oriented, precise in 2-4 sentences"""

    prompt_parts = [base_instructions.format(
        description=description,
        family_context=family_context,
        output_label=output_label,
        format_note=format_note,
    ).replace("__TEMPLATE__", template_text)]

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


def generate_role_spec_via_codex(
    description: str,
    config: Dict,
    args: argparse.Namespace,
) -> Dict:
    """
    Generate role specification via Codex from natural language description.
    """
    # Get family context
    family_name = Path(args.config).stem.replace("_main", "")
    family_context = f"Familie: {family_name}"

    output_format = resolve_output_format(config)
    formatting_cfg = dict(config.get("formatting") or {})

    # Build prompt
    prompt = build_role_spec_prompt(
        description=description,
        family_context=family_context,
        lang=args.lang,
        extra_instructions=args.extra_instructions or "",
        output_format=output_format,
        formatting=formatting_cfg,
    )

    # Get CLI command via CLIAdapter
    if args.codex_cmd_override:
        codex_cmd = parse_cmd(args.codex_cmd_override)
    else:
        cli_adapter = CLIAdapter(get_static_config_dir() / "cli_config.json")
        codex_cmd, _, _ = cli_adapter.build_command_for_role(
            provider_id=None, prompt=None, model=None, timeout_sec=None
        )

    # Call Codex
    stdout = call_codex(prompt, codex_cmd, args.nl_timeout_sec)

    # Parse output
    try:
        payload_text = extract_payload_from_markdown(stdout, output_format)
        if output_format == "toon":
            converter = build_default_converter(formatting_cfg)
            role_spec = converter.decode(payload_text, "toon")
        else:
            role_spec = json.loads(payload_text)
    except (FormatConversionError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fehler: Codex lieferte invalides {output_format.upper()}:\n{stdout}", file=sys.stderr)
        raise RuntimeError(f"{output_format.upper()} Parse Error: {exc}") from exc

    return role_spec


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for Natural Language mode."""
    p = argparse.ArgumentParser(
        description="Create a new role JSON and update a main config file.\n\n"
                    "Uses Natural Language mode to automatically generate role specifications via LLM.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # === NATURAL LANGUAGE MODE ===
    nl_group = p.add_argument_group("Natural Language Mode")
    nl_group.add_argument(
        "--nl-description",
        help="Natural language description of the role (e.g., 'A code reviewer that checks for bugs'). "
             "Activates automatic generation via Codex."
    )
    nl_group.add_argument(
        "--lang",
        choices=["de", "en"],
        default="de",
        help="Language for prompts (default: de)"
    )
    nl_group.add_argument(
        "--extra-instructions",
        help="Additional instructions for Codex generation"
    )
    nl_group.add_argument(
        "--nl-timeout-sec",
        type=int,
        default=180,
        help="Timeout for Codex CLI in NL mode (default: 180)"
    )
    nl_group.add_argument(
        "--codex-cmd-override",
        help="Override Codex CLI command for NL generation"
    )
    nl_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show generated spec without writing files"
    )

    # === COMMON OPTIONS ===
    common_group = p.add_argument_group("Common options")
    common_group.add_argument("--file", dest="role_file", help="Role file path relative to agent_families/ (default: <family>_agents/<id>.json).")
    common_group.add_argument("--apply-diff", action="store_true", help="Mark role as producing a diff to auto-apply.")
    common_group.add_argument("--diff-text", help="Custom diff instruction line for the prompt template.")

    diff_group = p.add_mutually_exclusive_group()
    diff_group.add_argument("--diff-instructions", dest="diff_instructions", action="store_true")
    diff_group.add_argument("--no-diff-instructions", dest="diff_instructions", action="store_false")
    p.set_defaults(diff_instructions=True)

    common_group.add_argument("--insert-after", help="Insert new role entry after this role id.")
    common_group.add_argument("--depends-on", action="append", default=[], help="Role id dependencies (repeatable).")
    common_group.add_argument("--instances", type=int, help="Number of instances (default: 1).")
    common_group.add_argument("--timeout-sec", type=int, help="Role timeout override in seconds.")
    common_group.add_argument("--max-output-chars", type=int, help="Max output chars for this role.")
    common_group.add_argument("--max-prompt-chars", type=int, help="Max prompt chars for this role.")
    common_group.add_argument("--max-prompt-tokens", type=int, help="Max prompt tokens for this role.")
    common_group.add_argument("--retries", type=int, help="Retry count for this role.")
    common_group.add_argument("--codex-cmd", help="Override Codex command for this role.")
    common_group.add_argument("--model", help="Model override for this role.")
    common_group.add_argument("--run-if-review-critical", action="store_true", help="Run only if review is critical.")

    # === CONFIG & OUTPUT ===
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to main config (e.g. agent_families/developer_main.json).")
    p.add_argument("--force", action="store_true", help="Overwrite existing role file and id entry.")

    return p.parse_args(argv)


def main_natural_language(args: argparse.Namespace, config: Dict, config_path: Path) -> None:
    """
    Natural Language mode - similar to family creator.
    """
    print(f"Generiere Rollen-Spezifikation via Codex (Natural Language Mode)...")

    # Generate role spec via Codex
    try:
        role_spec = generate_role_spec_via_codex(args.nl_description, config, args)
    except RuntimeError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        sys.exit(2)

    # Dry-run check
    if args.dry_run:
        print(json.dumps(role_spec, indent=2, ensure_ascii=False))
        return

    # Extract fields from spec
    role_id = role_spec.get("id", slugify(args.nl_description))
    role_name = role_spec.get("name", role_id)
    role_label = role_spec.get("role_label", role_name)
    title = role_spec.get("title", role_label)
    description = role_spec.get("description", args.nl_description)
    apply_diff = role_spec.get("apply_diff", False)
    format_sections = role_spec.get("format_sections", DEFAULT_FORMAT_SECTIONS)
    expected_sections = role_spec.get("expected_sections", [])
    rule_lines = role_spec.get("rule_lines", DEFAULT_RULE_LINES)
    context_entries_raw = role_spec.get("context_entries", [])
    diff_instructions_text = role_spec.get("diff_instructions", DEFAULT_DIFF_TEXT)
    depends_on = role_spec.get("depends_on", [])
    timeout_sec = role_spec.get("timeout_sec")
    max_output_chars = role_spec.get("max_output_chars")

    # Parse context entries
    context_entries = []
    for entry in context_entries_raw:
        if isinstance(entry, dict):
            context_entries.append((entry.get("key", ""), entry.get("label", "")))
        elif isinstance(entry, str):
            if ":" in entry:
                key, label = entry.split(":", 1)
                context_entries.append((key.strip(), label.strip()))
            else:
                context_entries.append((entry.strip(), entry.strip()))

    # Build prompt template
    prompt_template = build_prompt_template(
        title=title,
        description=description,
        context_entries=context_entries,
        format_sections=format_sections,
        rule_lines=rule_lines,
        include_diff_instructions=apply_diff,
        diff_text=diff_instructions_text,
        include_description=True,
        include_last_applied_diff=True,
        include_coordination=True,
        include_snapshot=True,
    )

    # Determine role file path
    base_dir = config_path.parent
    default_role_dir = "developer_roles"
    stem = config_path.stem
    if stem.endswith("_main"):
        prefix = stem[:-len("_main")]
        if prefix:
            default_role_dir = f"{prefix}_roles"

    role_file = args.role_file or f"{default_role_dir}/{role_id}.json"
    role_path, role_rel_path = resolve_role_path(base_dir, role_file)

    # Check if exists
    roles = list(config.get("roles", []))
    if any(role.get("id") == role_id for role in roles):
        if not args.force:
            print(f"Fehler: Rolle existiert bereits: {role_id}", file=sys.stderr)
            print("Nutze --force zum Überschreiben", file=sys.stderr)
            sys.exit(2)
        roles = [role for role in roles if role.get("id") != role_id]

    if role_path.exists() and not args.force:
        print(f"Fehler: Rollen-Datei existiert bereits: {role_path}", file=sys.stderr)
        sys.exit(2)

    # Write role JSON
    role_data = {
        "id": role_id,
        "name": role_name,
        "role": role_label,
        "prompt_template": prompt_template,
    }

    write_json(role_path, role_data)
    print(f"✓ Rollen-Datei erstellt: {role_path}")

    # Build entry for main config
    entry: Dict[str, object] = {
        "id": role_id,
        "file": role_rel_path,
    }

    if apply_diff or args.apply_diff:
        entry["apply_diff"] = True

    if args.instances:
        entry["instances"] = args.instances

    if depends_on or args.depends_on:
        entry["depends_on"] = list(set(depends_on + args.depends_on))

    if timeout_sec or args.timeout_sec:
        entry["timeout_sec"] = args.timeout_sec or timeout_sec

    if max_output_chars or args.max_output_chars:
        entry["max_output_chars"] = args.max_output_chars or max_output_chars

    if expected_sections:
        entry["expected_sections"] = expected_sections

    # Insert into config
    final_role_id = config.get("final_role_id")
    roles = insert_role_entry(roles, entry, args.insert_after, final_role_id)
    config["roles"] = roles

    write_json(config_path, config)
    print(f"✓ Rolle registriert in: {config_path}")
    print(f"\nRolle erstellt: {role_id}")
    print(f"  Name: {role_name}")
    print(f"  Datei: {role_rel_path}")
    print(f"  Apply-Diff: {'Ja' if apply_diff else 'Nein'}")


def main() -> None:
    """Main entry point with mode detection."""
    args = parse_args()
    config_path = Path(args.config).resolve()

    try:
        cfg = load_config_with_defaults(config_path)
    except FileNotFoundError as exc:
        print(f"Error: config not found: {exc}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid config JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    # Natural Language Mode
    if not args.nl_description:
        print("Fehler: --nl-description ist erforderlich", file=sys.stderr)
        print("\nBeispiel:", file=sys.stderr)
        print("  python multi_role_agent_creator.py --nl-description 'Ein Code Reviewer der auf Bugs prüft'", file=sys.stderr)
        sys.exit(1)

    main_natural_language(args, cfg, config_path)


if __name__ == "__main__":
    main()
