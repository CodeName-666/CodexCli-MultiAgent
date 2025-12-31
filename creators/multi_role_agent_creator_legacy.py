#!/usr/bin/env python3
"""
multi_role_agent_creator.py - create a new role JSON and register it in a main config.
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

from multi_agent.utils import get_codex_cmd, parse_cmd

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "developer_main.json"
DEFAULT_FORMAT_SECTIONS = ["- Aufgaben:", "- Entscheidungen:", "- Offene Punkte:"]
DEFAULT_RULE_LINES = [
    "Ausgabe muss exakt diese Abschnittsmarker enthalten.",
    "Wenn FEHLENDE SEKTIONEN angegeben sind, korrigiere das Format.",
]
DEFAULT_DIFF_TEXT = "Dann liefere einen UNIFIED DIFF (git-style) für alle Änderungen:"
DEFAULT_OPTIMIZE_TIMEOUT_SEC = 120


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def parse_context_entries(values: List[str]) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    for raw in values:
        if ":" in raw:
            key, label = raw.split(":", 1)
            key = key.strip()
            label = label.strip()
        else:
            key = raw.strip()
            label = key
        if not key:
            continue
        entries.append((key, label or key))
    return entries


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


def build_description_optimization_prompt(description: str, extra_instructions: str) -> str:
    instructions = [
        "Optimiere die folgende Rollenbeschreibung fuer einen Codex-CLI-Agenten.",
        "Ziel: klare, handlungsorientierte Beschreibung in 2-4 Saetzen.",
        "Behalte die Sprache des Inputs bei.",
        "Keine Aufzaehlungen, keine Ueberschriften, keine Anfuehrungszeichen.",
        "Gib nur den optimierten Text aus.",
    ]
    if extra_instructions:
        instructions.append(f"Zusatzhinweis: {extra_instructions.strip()}")
    instructions.append("")
    instructions.append("Beschreibung:")
    instructions.append(description.strip())
    return "\n".join(instructions).strip() + "\n"


def optimize_description(
    description: str,
    cfg: Dict[str, object],
    args: argparse.Namespace,
) -> str:
    codex_cfg = cfg.get("codex") if isinstance(cfg, dict) else None
    if not isinstance(codex_cfg, dict):
        raise ValueError("config codex section missing or invalid.")
    env_var = str(codex_cfg.get("env_var") or "CODEX_CMD")
    default_cmd = str(codex_cfg.get("default_cmd") or "codex exec -")
    if args.optimize_codex_cmd:
        cmd = parse_cmd(args.optimize_codex_cmd)
    else:
        cmd = get_codex_cmd(env_var, default_cmd)
    prompt = build_description_optimization_prompt(description, args.optimize_instructions or "")
    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=args.optimize_timeout_sec,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Codex CLI not found: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Codex CLI timed out after {args.optimize_timeout_sec}s.") from exc
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        reason = stderr or stdout or "unknown error"
        raise RuntimeError(f"Codex CLI failed (rc={proc.returncode}): {reason}")
    optimized = (proc.stdout or "").strip()
    if not optimized:
        raise RuntimeError("Codex CLI returned empty description.")
    return optimized


def resolve_role_path(base_dir: Path, role_file: str) -> Tuple[Path, str]:
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


def normalize_sections(values: List[str]) -> List[str]:
    raw = values or DEFAULT_FORMAT_SECTIONS
    normalized: List[str] = []
    for entry in raw:
        text = entry.strip()
        if not text:
            continue
        if text.startswith(("-", "#", "```")) or text.startswith("diff --") or text == "...":
            normalized.append(text)
        else:
            normalized.append(f"- {text}")
    return normalized


def normalize_rule_lines(values: List[str]) -> List[str]:
    raw = values
    normalized: List[str] = []
    for entry in raw:
        text = entry.strip()
        if not text:
            continue
        if text.startswith("-"):
            normalized.append(text)
        else:
            normalized.append(f"- {text}")
    return normalized


def format_has_diff_block(format_sections: List[str]) -> bool:
    for section in format_sections:
        text = section.strip().lower()
        if text.startswith("```diff") or text.startswith("diff --git") or text == "...":
            return True
    return False


def normalize_expected_section(line: str) -> str | None:
    text = line.strip()
    if not text:
        return None
    if text.startswith("#"):
        return text
    if text.startswith("-"):
        lower = text.lower()
        if "(optional" in lower or "diff" in lower:
            return None
        if lower.startswith("- plan"):
            return "- Plan"
        return text
    return None


def build_expected_sections(
    title: str,
    format_sections: List[str],
    expect_diff_block: bool,
    expected_override: List[str],
    allow_expected_diff: bool,
) -> List[str]:
    if expected_override:
        return [section for section in expected_override if section.strip()]
    expected = [f"# {title}"]
    for section in format_sections:
        normalized = normalize_expected_section(section)
        if normalized and normalized not in expected:
            expected.append(normalized)
    if expect_diff_block and allow_expected_diff and "```diff" not in expected:
        expected.append("```diff")
    if not allow_expected_diff:
        expected = [section for section in expected if section != "```diff"]
    return expected


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a new role JSON and update a main config file.")
    p.add_argument("--description", required=True, help="Role description used to build the prompt template.")
    p.add_argument("--id", dest="role_id", help="Role id (default: slugified description).")
    p.add_argument("--name", help="Role name (default: id).")
    p.add_argument("--role", dest="role_label", help="Role label (default: name).")
    p.add_argument("--title", help="Title used in the prompt header (default: role label).")
    p.add_argument(
        "--section",
        action="append",
        default=[],
        help="Section line in the FORMAT block (repeatable). Defaults to a generic 3-section list.",
    )
    p.add_argument(
        "--expected-section",
        action="append",
        default=[],
        help="Expected section marker (repeatable). Overrides auto-generated expected sections.",
    )
    p.add_argument(
        "--context",
        action="append",
        default=[],
        help="Extra placeholders to include (key or key:Label). Example: --context architect_summary:ARCH (Kurz).",
    )
    p.add_argument(
        "--rule",
        action="append",
        default=[],
        help="Rule line in the REGELN block (repeatable). Defaults to standard rule lines.",
    )
    p.add_argument(
        "--replace-rules",
        action="store_true",
        help="Use only the provided --rule lines (skip the defaults).",
    )
    p.add_argument(
        "--file",
        dest="role_file",
        help="Role file path relative to config/ (default: <family>_roles/<id>.json).",
    )
    p.add_argument("--apply-diff", action="store_true", help="Mark role as producing a diff to auto-apply.")
    p.add_argument("--diff-text", help="Custom diff instruction line for the prompt template.")
    diff_group = p.add_mutually_exclusive_group()
    diff_group.add_argument("--diff-instructions", dest="diff_instructions", action="store_true")
    diff_group.add_argument("--no-diff-instructions", dest="diff_instructions", action="store_false")
    p.set_defaults(diff_instructions=None)
    p.add_argument("--insert-after", help="Insert new role entry after this role id.")
    p.add_argument("--depends-on", action="append", default=[], help="Role id dependencies (repeatable).")
    p.add_argument("--instances", type=int, default=1, help="Number of instances (default: 1).")
    p.add_argument("--timeout-sec", type=int, help="Role timeout override in seconds.")
    p.add_argument("--max-output-chars", type=int, help="Max output chars for this role.")
    p.add_argument("--max-prompt-chars", type=int, help="Max prompt chars for this role.")
    p.add_argument("--max-prompt-tokens", type=int, help="Max prompt tokens for this role.")
    p.add_argument("--retries", type=int, help="Retry count for this role.")
    p.add_argument("--codex-cmd", help="Override Codex command for this role.")
    p.add_argument("--model", help="Model override for this role.")
    p.add_argument("--run-if-review-critical", action="store_true", help="Run only if review is critical.")
    p.add_argument(
        "--optimize-description",
        action="store_true",
        help="Optimize role description via Codex CLI before creating the role.",
    )
    p.add_argument(
        "--optimize-instructions",
        help="Optional extra instructions for description optimization.",
    )
    p.add_argument(
        "--optimize-timeout-sec",
        type=int,
        default=DEFAULT_OPTIMIZE_TIMEOUT_SEC,
        help="Timeout for description optimization via Codex CLI.",
    )
    p.add_argument(
        "--optimize-codex-cmd",
        help="Override Codex CLI command for description optimization.",
    )
    desc_group = p.add_mutually_exclusive_group()
    desc_group.add_argument("--description-block", dest="description_block", action="store_true")
    desc_group.add_argument("--no-description-block", dest="description_block", action="store_false")
    p.set_defaults(description_block=False)
    p.add_argument("--no-last-applied-diff", action="store_true", help="Skip the last applied diff block.")
    p.add_argument("--no-coordination", action="store_true", help="Skip the coordination block.")
    p.add_argument("--no-snapshot", action="store_true", help="Skip the workspace snapshot block.")
    p.add_argument("--no-expected-diff", action="store_true", help="Remove ```diff from expected sections.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to main config (e.g. config/developer_main.json).")
    p.add_argument("--force", action="store_true", help="Overwrite existing role file and id entry.")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        cfg = load_json(config_path)
    except FileNotFoundError as exc:
        print(f"Error: config not found: {exc}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid config JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    base_dir = config_path.parent
    roles = list(cfg.get("roles", []))
    if not isinstance(roles, list):
        print("Error: config roles must be a list.", file=sys.stderr)
        sys.exit(2)

    raw_description = args.description.strip()
    role_id = (args.role_id or slugify(raw_description)).strip()
    if not role_id:
        print("Error: role id is empty.", file=sys.stderr)
        sys.exit(2)

    if any(role.get("id") == role_id for role in roles):
        if not args.force:
            print(f"Error: role id already exists: {role_id}", file=sys.stderr)
            sys.exit(2)
        roles = [role for role in roles if role.get("id") != role_id]

    role_name = (args.name or role_id).strip()
    role_label = (args.role_label or role_name).strip()
    title = (args.title or role_label).strip()
    default_role_dir = "developer_roles"
    if args.config:
        stem = Path(args.config).stem
        if stem.endswith("_main"):
            prefix = stem[: -len("_main")]
            if prefix:
                default_role_dir = f"{prefix}_roles"
    role_file = args.role_file or f"{default_role_dir}/{role_id}.json"
    role_path, role_rel_path = resolve_role_path(base_dir, role_file)

    if role_path.exists() and not args.force:
        print(f"Error: role file already exists: {role_path}", file=sys.stderr)
        sys.exit(2)

    description = raw_description
    if args.optimize_description:
        try:
            description = optimize_description(raw_description, cfg, args)
            if not args.description_block:
                args.description_block = True
        except (RuntimeError, ValueError) as exc:
            print(f"Error: description optimization failed: {exc}", file=sys.stderr)
            sys.exit(2)

    context_entries = parse_context_entries(args.context)
    format_sections = normalize_sections(args.section)
    has_diff_block = format_has_diff_block(format_sections)
    if args.replace_rules:
        rule_values = args.rule
    else:
        rule_values = args.rule or DEFAULT_RULE_LINES
    rule_lines = normalize_rule_lines(rule_values)
    if args.diff_instructions is None:
        include_diff_instructions = args.apply_diff and not has_diff_block
    else:
        include_diff_instructions = args.diff_instructions
    diff_text = (args.diff_text or DEFAULT_DIFF_TEXT).strip()
    prompt_template = build_prompt_template(
        title=title,
        description=description,
        context_entries=context_entries,
        format_sections=format_sections,
        rule_lines=rule_lines,
        include_diff_instructions=include_diff_instructions,
        diff_text=diff_text,
        include_description=args.description_block,
        include_last_applied_diff=not args.no_last_applied_diff,
        include_coordination=not args.no_coordination,
        include_snapshot=not args.no_snapshot,
    )

    role_data = {
        "id": role_id,
        "name": role_name,
        "role": role_label,
        "prompt_template": prompt_template,
    }
    write_json(role_path, role_data)

    entry: Dict[str, object] = {"id": role_id, "file": role_rel_path}
    if args.apply_diff:
        entry["apply_diff"] = True
    if args.instances and args.instances > 0:
        entry["instances"] = args.instances
    if args.depends_on:
        entry["depends_on"] = [dep for dep in args.depends_on if dep.strip()]
    expect_diff_block = args.apply_diff or include_diff_instructions
    expected_sections = build_expected_sections(
        title=title,
        format_sections=format_sections,
        expect_diff_block=expect_diff_block,
        expected_override=args.expected_section,
        allow_expected_diff=not args.no_expected_diff,
    )
    if expected_sections:
        entry["expected_sections"] = expected_sections
    if args.timeout_sec is not None:
        entry["timeout_sec"] = args.timeout_sec
    if args.max_output_chars is not None:
        entry["max_output_chars"] = args.max_output_chars
    if args.max_prompt_chars is not None:
        entry["max_prompt_chars"] = args.max_prompt_chars
    if args.max_prompt_tokens is not None:
        entry["max_prompt_tokens"] = args.max_prompt_tokens
    if args.retries is not None:
        entry["retries"] = args.retries
    if args.codex_cmd:
        entry["codex_cmd"] = args.codex_cmd
    if args.model:
        entry["model"] = args.model
    if args.run_if_review_critical:
        entry["run_if_review_critical"] = True

    try:
        cfg["roles"] = insert_role_entry(roles, entry, args.insert_after, cfg.get("final_role_id"))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    write_json(config_path, cfg)
    print(f"Created role file: {role_path}")
    print(f"Registered role in: {config_path}")


if __name__ == "__main__":
    main()
