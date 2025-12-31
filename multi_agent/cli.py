from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

from .config_loader import load_app_config
from .constants import DEFAULT_CONFIG_PATH, DEFAULT_MAX_FILE_BYTES, DEFAULT_MAX_FILES, DEFAULT_TIMEOUT_SEC
from .pipeline import build_pipeline
from .task_split import (
    build_chunk_payload,
    build_chunks_from_plan,
    build_split_id,
    extract_headings,
    init_manifest,
    load_manifest,
    load_task_text,
    needs_split,
    plan_chunks_with_llm,
    resolve_split_dirs,
    save_manifest,
    split_task_markdown,
    write_base_chunks,
)
from .utils import get_codex_cmd, now_stamp, parse_cmd, summarize_text

# Import creator modules for subcommands
try:
    from creators import multi_family_creator, multi_role_agent_creator
    CREATORS_AVAILABLE = True
except ImportError:
    CREATORS_AVAILABLE = False


def parse_args_task(cfg, argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse arguments for the task subcommand (original functionality)."""
    cli = cfg.cli
    args_cfg = cli["args"]
    p = argparse.ArgumentParser(description=str(cli["description"]))
    config_help = str(args_cfg.get("config", {}).get("help") or "Pfad zur Konfigurationsdatei.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help=config_help)
    p.add_argument("--task", required=True, help=str(args_cfg["task"]["help"]))
    p.add_argument("--dir", default=".", help=str(args_cfg["dir"]["help"]))
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help=str(args_cfg["timeout"]["help"]))
    p.add_argument("--apply", action="store_true", help=str(args_cfg["apply"]["help"]))
    p.add_argument(
        "--apply-mode",
        choices=["end", "role"],
        default="end",
        help=str(args_cfg["apply_mode"]["help"]),
    )
    p.add_argument(
        "--apply-roles",
        action="append",
        default=[],
        help=str(args_cfg["apply_roles"]["help"]),
    )
    p.add_argument("--apply-confirm", action="store_true", help=str(args_cfg["apply_confirm"]["help"]))
    p.add_argument("--fail-fast", action="store_true", help=str(args_cfg["fail_fast"]["help"]))
    p.add_argument("--ignore-fail", action="store_true", help=str(args_cfg["ignore_fail"]["help"]))
    p.add_argument("--task-split", action="store_true", help=str(args_cfg["task_split"]["help"]))
    p.add_argument("--no-task-resume", action="store_true", help=str(args_cfg["no_task_resume"]["help"]))
    p.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help=str(args_cfg["max_files"]["help"]))
    p.add_argument(
        "--max-file-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=str(args_cfg["max_file_bytes"]["help"]),
    )
    p.add_argument("--validate-config", action="store_true", help=str(args_cfg["validate_config"]["help"]))
    return p.parse_args(argv)


def _parse_config_path(argv: Optional[List[str]]) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args, _ = parser.parse_known_args(argv)
    return Path(args.config)


async def _run_split(pipeline, args: argparse.Namespace, cfg) -> int:
    workdir = Path(args.dir).resolve()
    try:
        task_text, task_source = load_task_text(args.task, workdir)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    split_cfg = cfg.task_split or {}
    decision_mode = str(split_cfg.get("decision_mode", "auto") or "auto").lower()
    if decision_mode != "always" and not needs_split(task_text, split_cfg):
        print("Task-Split: nicht notwendig, starte Single-Run.")
        return await pipeline.run(args, cfg)

    split_id = build_split_id(task_source, task_text)
    split_dir, tasks_dir = resolve_split_dirs(workdir, split_cfg, split_id)
    tasks_dir.mkdir(parents=True, exist_ok=True)
    manifest_name = str(split_cfg.get("manifest_filename") or "task_split.json")
    manifest_path = split_dir / manifest_name
    auto_resume = bool(split_cfg.get("auto_resume", True))
    resume = auto_resume and not args.no_task_resume

    if resume and manifest_path.exists():
        manifest = load_manifest(manifest_path)
    else:
        heading_level = int(split_cfg.get("heading_level", 2) or 2)
        min_chars = int(split_cfg.get("chunk_min_chars", 600) or 600)
        max_chars = int(split_cfg.get("chunk_max_chars", 4000) or 4000)
        chunks = []
        llm_enabled = bool(split_cfg.get("llm_enabled", True))
        if llm_enabled:
            headings = extract_headings(task_text, heading_level)
            max_headings = int(split_cfg.get("llm_max_headings", 60) or 60)
            timeout_sec = int(split_cfg.get("llm_timeout_sec", 120) or 120)
            raw_cmd = str(split_cfg.get("llm_cmd") or "").strip()
            if raw_cmd:
                codex_cmd = parse_cmd(raw_cmd)
            else:
                codex_cmd = get_codex_cmd(cfg.codex_env_var, cfg.codex_default_cmd)
            plan = plan_chunks_with_llm(headings, codex_cmd, timeout_sec, max_headings)
            chunks = build_chunks_from_plan(task_text, headings, plan)
        if not chunks:
            chunks = split_task_markdown(task_text, heading_level, min_chars, max_chars)
        if not chunks:
            print("Fehler: Task-Splitting hat keine Chunks erzeugt.", file=sys.stderr)
            return 2
        write_base_chunks(chunks, tasks_dir)
        manifest = init_manifest(split_id, task_source, chunks, tasks_dir)
        save_manifest(manifest_path, manifest)

    chunks_meta = manifest.get("chunks", [])
    if not chunks_meta:
        print("Fehler: Task-Splitting Manifest ist leer.", file=sys.stderr)
        return 2

    print(f"Task-Split aktiv: {len(chunks_meta)} Chunks -> {split_dir}")
    carry_over = ""
    any_fail = False
    carry_max = int(split_cfg.get("carry_over_max_chars", 1200) or 1200)
    carry_file = str(split_cfg.get("carry_over_filename") or "carry_over.md")

    for entry in chunks_meta:
        status = entry.get("status") or "pending"
        if status == "done":
            summary = str(entry.get("summary") or "").strip()
            if summary:
                carry_over = summary
            continue
        base_file = tasks_dir / str(entry.get("base_file") or "")
        if not base_file.exists():
            print(f"Fehler: Base-Chunk fehlt: {base_file}", file=sys.stderr)
            return 2
        base_text = base_file.read_text(encoding="utf-8")
        task_payload = build_chunk_payload(base_text, carry_over, carry_max)
        task_file = tasks_dir / str(entry.get("task_file") or "")
        task_file.write_text(task_payload, encoding="utf-8")

        chunk_args = argparse.Namespace(**vars(args))
        chunk_args.task = f"@{task_file}"
        chunk_args.task_split = False
        chunk_args.no_task_resume = False

        run_id = f"{split_id}-chunk-{int(entry.get('index', 0)):03d}-{now_stamp()}"
        rc = await pipeline.run(chunk_args, cfg, run_id_override=run_id)
        entry["run_id"] = run_id
        entry["run_dir"] = str(workdir / str(cfg.paths["run_dir"]) / run_id)
        entry["returncode"] = rc
        entry["status"] = "done" if rc == 0 else "failed"
        if rc != 0:
            any_fail = True

        summary_path = Path(entry["run_dir"]) / "final_summary.txt"
        if summary_path.exists():
            summary_text = summary_path.read_text(encoding="utf-8").strip()
            summary_text = summarize_text(summary_text, max_chars=carry_max)
            entry["summary"] = summary_text
            carry_over = summary_text
            split_dir.mkdir(parents=True, exist_ok=True)
            (split_dir / carry_file).write_text(summary_text + "\n", encoding="utf-8")
        else:
            entry["summary"] = entry.get("summary") or ""
        save_manifest(manifest_path, manifest)

    return 1 if any_fail else 0


def main_task() -> None:
    """Original main function - now a subcommand handler."""
    config_path = _parse_config_path(None)
    try:
        cfg = load_app_config(config_path)
    except FileNotFoundError as e:
        print(f"Fehler: Konfigurationsdatei nicht gefunden: {e}", file=sys.stderr)
        sys.exit(2)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Fehler: Ungueltige Konfiguration: {e}", file=sys.stderr)
        sys.exit(2)

    args = parse_args_task(cfg)
    if args.validate_config:
        from .schema_validator import validate_config

        ok, error = validate_config(Path(args.config))
        if not ok:
            print(f"Fehler: Konfiguration ungueltig: {error}", file=sys.stderr)
            sys.exit(2)
        print("Konfiguration ist gueltig.")
        sys.exit(0)
    pipeline = build_pipeline()
    try:
        split_enabled = bool(args.task_split) or bool(getattr(cfg, "task_split", {}).get("enabled", False))
        if split_enabled:
            rc = asyncio.run(_run_split(pipeline, args, cfg))
        else:
            rc = asyncio.run(pipeline.run(args, cfg))
    except KeyboardInterrupt:
        print(f"\n{cfg.messages['interrupted']}", file=sys.stderr)
        rc = 130
    except FileNotFoundError as e:
        print(f"\n{cfg.messages['codex_not_found'].format(error=e)}", file=sys.stderr)
        print(cfg.messages["codex_tip"], file=sys.stderr)
        rc = 127
    sys.exit(rc)


def main() -> None:
    """Main entry point with subcommand support."""
    # Check if we have a subcommand
    if len(sys.argv) > 1 and sys.argv[1] in ['create-family', 'create-role']:
        if not CREATORS_AVAILABLE:
            print("Fehler: Creator-Module nicht verfügbar.", file=sys.stderr)
            print("Stelle sicher, dass das 'creators' Verzeichnis im Python-Path ist.", file=sys.stderr)
            sys.exit(2)

        subcommand = sys.argv[1]
        # Remove subcommand from argv for the creator's argparse
        creator_argv = sys.argv[2:]

        if subcommand == 'create-family':
            # Call multi_family_creator.main() with remaining args
            sys.exit(multi_family_creator.main(creator_argv))
        elif subcommand == 'create-role':
            # Call multi_role_agent_creator with modified sys.argv
            # The creator's main() uses sys.argv internally
            sys.argv = [sys.argv[0]] + creator_argv
            try:
                multi_role_agent_creator.main()
            except SystemExit as e:
                sys.exit(e.code if e.code else 0)

    # If no recognized subcommand, check for --help to show available commands
    elif len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Multi-Agent Codex CLI")
        print("=" * 50)
        print("\nDieses CLI bietet mehrere Funktionen zum Arbeiten mit Multi-Agent-Systemen.\n")
        print("Verwendung:")
        print("  multi_agent_codex --task <description> [options]          # Rückwärtskompatibel")
        print("  multi_agent_codex create-family --description <text> [...]")
        print("  multi_agent_codex create-role --nl-description <text> [...]\n")
        print("Unterkommandos:")
        print("  create-family   Erstelle eine neue Agent-Familie von einer")
        print("                  natürlichsprachlichen Beschreibung")
        print("  create-role     Erstelle eine neue Agent-Rolle in einer bestehenden Familie\n")
        print("Standard-Verhalten (ohne Unterkommando):")
        print("  Führt einen Multi-Agent-Task aus (benötigt --task Argument)\n")
        print("Hilfe zu Unterkommandos:")
        print("  multi_agent_codex create-family --help")
        print("  multi_agent_codex create-role --help\n")
        print("Beispiele:")
        print("  # Familie erstellen")
        print("  multi_agent_codex create-family --description \"Ein Team für ML-Entwicklung\"")
        print("")
        print("  # Rolle erstellen")
        print("  multi_agent_codex create-role --nl-description \"Ein Code Reviewer\"")
        print("")
        print("  # Task ausführen (rückwärtskompatibel)")
        print("  multi_agent_codex --task \"Implementiere Feature X\" --apply")
        sys.exit(0)

    # Default: run task command (backwards compatibility)
    else:
        main_task()
