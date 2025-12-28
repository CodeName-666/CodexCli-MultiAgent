#!/usr/bin/env python3
"""
multi_role_agent_creator.py - create a new role JSON and register it in config/main.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "main.json"


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
) -> str:
    safe_title = title.replace("{", "{{").replace("}", "}}")
    safe_description = description.replace("{", "{{").replace("}", "}}")
    lines: List[str] = []
    lines.append("FORMAT:")
    lines.append(f"# {safe_title}")
    lines.append("- Aufgaben:")
    lines.append("- Entscheidungen:")
    lines.append("- Offene Punkte:")
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
    lines.append("")
    lines.append("KONTEXT (Workspace Snapshot):")
    lines.append("{snapshot}")
    return "\n".join(lines) + "\n"


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


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create a new role JSON and update config/main.json.")
    p.add_argument("--description", required=True, help="Role description used to build the prompt template.")
    p.add_argument("--id", dest="role_id", help="Role id (default: slugified description).")
    p.add_argument("--name", help="Role name (default: id).")
    p.add_argument("--role", dest="role_label", help="Role label (default: name).")
    p.add_argument("--title", help="Title used in the prompt header (default: role label).")
    p.add_argument(
        "--context",
        action="append",
        default=[],
        help="Extra placeholders to include (key or key:Label). Example: --context architect_summary:ARCH (Kurz).",
    )
    p.add_argument("--file", dest="role_file", help="Role file path relative to config/ (default: roles/<id>.json).")
    p.add_argument("--apply-diff", action="store_true", help="Mark role as producing a diff to auto-apply.")
    p.add_argument("--insert-after", help="Insert new role entry after this role id.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to main.json config.")
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

    description = args.description.strip()
    role_id = (args.role_id or slugify(description)).strip()
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
    role_file = args.role_file or f"roles/{role_id}.json"
    role_path, role_rel_path = resolve_role_path(base_dir, role_file)

    if role_path.exists() and not args.force:
        print(f"Error: role file already exists: {role_path}", file=sys.stderr)
        sys.exit(2)

    context_entries = parse_context_entries(args.context)
    prompt_template = build_prompt_template(title, description, context_entries)

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
