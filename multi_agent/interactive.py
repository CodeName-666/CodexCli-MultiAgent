"""Interactive CLI flows for configuring and running tasks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .cli_errors import print_error
from .config_loader import load_app_config
from .constants import (
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILES,
    DEFAULT_TIMEOUT_SEC,
    ExitCode,
    get_agent_families_dir,
)
from .run_helpers import run_pipeline


def parse_args_run(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse arguments for the run subcommand (interactive/CLI hybrid)."""
    p = argparse.ArgumentParser(
        prog="multi_agent_codex run",
        description="Fuehre einen Multi-Agent-Task aus (interaktiv oder mit CLI-Argumenten)",
        epilog="""
Verwendungsmodi:

  INTERAKTIV (ohne Argumente):
    multi_agent_codex run

    Fuehrt durch einen gefuehrten Dialog durch alle Optionen.

  CLI-MODUS (mit Argumenten):
    multi_agent_codex run --family developer --task "Implementiere Feature X" --apply

    Nutzt alle angegebenen Parameter direkt, fehlende werden interaktiv abgefragt.

Beispiele:
  # Vollstaendig interaktiv
  multi_agent_codex run

  # Familie vorgeben, Rest interaktiv
  multi_agent_codex run --family developer

  # Vollstaendig per CLI
  multi_agent_codex run --family developer --task "Fix Bug in utils.py" --apply --dir ./myproject
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    p.add_argument("--family", help="Agent-Familie (z.B. developer, designer)")
    p.add_argument("--task", help="Task-Beschreibung (bei @datei.txt wird Inhalt gelesen)")
    p.add_argument("--resume-run", help="Resume a cancelled run (run_id or path)")
    p.add_argument("--dir", default=".", help="Working Directory (default: .)")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help=f"Timeout in Sekunden (default: {DEFAULT_TIMEOUT_SEC})")

    p.add_argument("--apply", action="store_true", help="Diff automatisch anwenden")
    p.add_argument("--apply-mode", choices=["end", "role"], default="end", help="Apply-Modus: end=am Ende, role=nach jeder Rolle (default: end)")
    p.add_argument("--apply-confirm", action="store_true", help="Vor jedem Apply bestaetigen")
    p.add_argument("--apply-roles", action="append", default=[], help="Nur fuer diese Rollen Apply ausfuehren (wiederholbar)")

    p.add_argument("--fail-fast", action="store_true", help="Bei Fehler sofort abbrechen")
    p.add_argument("--ignore-fail", action="store_true", help="Fehler ignorieren und weitermachen")
    p.add_argument("--task-split", action="store_true", help="Task-Splitting aktivieren")
    p.add_argument("--no-task-resume", action="store_true", help="Task-Splitting Resume deaktivieren")
    p.add_argument("--no-streaming", action="store_true", help="Disable real-time output streaming")

    p.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help=f"Max Dateien im Snapshot (default: {DEFAULT_MAX_FILES})")
    p.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES, help=f"Max Bytes pro Datei (default: {DEFAULT_MAX_FILE_BYTES})")

    p.add_argument("--non-interactive", action="store_true", help="Nicht-interaktiver Modus: Fehler bei fehlenden Parametern")
    p.add_argument("--yes", "-y", action="store_true", help="Alle Bestaetigungen automatisch mit Ja beantworten")

    return p.parse_args(argv)


def _select_family_interactive() -> Optional[Path]:
    """Interactively select a family from available options."""
    families_dir = get_agent_families_dir()
    if not families_dir.exists():
        print_error("agent_families/ Verzeichnis nicht gefunden.")
        return None

    families = sorted(families_dir.glob("*_main.json"))
    families = [f for f in families if f.name not in ["defaults.json", "multi_cli_example.json"]]

    if not families:
        print_error("Keine Agent-Familien gefunden.")
        print("Erstelle zuerst eine Familie mit: multi_agent_codex create-family", file=sys.stderr)
        return None

    print("Verfuegbare Familien:")
    for i, family in enumerate(families, 1):
        family_name = family.stem.replace("_main", "")
        print(f"  {i}. {family_name}")

    try:
        choice = input("\nWaehle Familie (Nummer oder Name): ").strip()
        if choice.isdigit():
            family_path = families[int(choice) - 1]
        else:
            matching = [f for f in families if choice in f.stem]
            if matching:
                family_path = matching[0]
            else:
                family_path = families_dir / f"{choice}_main.json"

        if not family_path.exists():
            print_error(f"Familie nicht gefunden: {choice}")
            return None

        print(f"[OK] Gewaehlt: {family_path.stem.replace('_main', '')}")
        return family_path
    except (ValueError, IndexError):
        print_error("Ungueltige Auswahl")
        return None


def _get_family_from_args(family_name: str) -> Optional[Path]:
    """Get family path from CLI argument."""
    families_dir = get_agent_families_dir()
    family_path = families_dir / f"{family_name}_main.json"
    if not family_path.exists():
        print_error(f"Familie nicht gefunden: {family_name}")
        return None
    return family_path


def _get_task_interactive() -> Optional[str]:
    """Get task description from interactive input."""
    print("\n--- Task-Beschreibung ---")
    print("Gib eine Beschreibung der Aufgabe ein (mehrere Zeilen moeglich).")
    print("Beende Eingabe mit einer leeren Zeile.\n")

    task_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        task_lines.append(line)

    if not task_lines:
        print_error("Keine Task-Beschreibung angegeben.")
        return None

    task = "\n".join(task_lines)
    suffix = "..." if len(task) > 100 else ""
    print(f"\n[OK] Task: {task[:100]}{suffix}")
    return task


def _get_options_interactive(args: argparse.Namespace) -> dict:
    """Get runtime options from interactive input."""
    print("\n--- Optionen ---")

    workdir = input(f"Working Directory (default: {args.dir}): ").strip() or args.dir

    apply_input = input("Diff automatisch anwenden? (y/N): ").strip().lower()
    apply = apply_input == "y"

    apply_mode = "end"
    apply_confirm = False
    if apply:
        mode_input = input("Apply-Modus (end/role, default: end): ").strip().lower()
        if mode_input in ["end", "role"]:
            apply_mode = mode_input

        confirm_input = input("Vor jedem Apply bestaetigen? (y/N): ").strip().lower()
        apply_confirm = confirm_input == "y"

    fail_fast_input = input("Bei Fehler sofort abbrechen? (y/N): ").strip().lower()
    fail_fast = fail_fast_input == "y"

    task_split_input = input("Task-Splitting aktivieren? (y/N): ").strip().lower()
    task_split = task_split_input == "y"

    streaming_input = input("Live-Streaming aktivieren? (Y/n): ").strip().lower()
    no_streaming = streaming_input == "n"

    return {
        "workdir": workdir,
        "apply": apply,
        "apply_mode": apply_mode,
        "apply_confirm": apply_confirm,
        "fail_fast": fail_fast,
        "task_split": task_split,
        "no_streaming": no_streaming,
    }


def _print_run_summary(family_path: Path, task: str, options: dict) -> None:
    """Print summary of the run configuration."""
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Familie:      {family_path.stem.replace('_main', '')}")
    print(f"Task:         {task[:80]}{'...' if len(task) > 80 else ''}")
    print(f"Verzeichnis:  {options['workdir']}")
    print(f"Auto-Apply:   {'Ja' if options['apply'] else 'Nein'}")
    if options["apply"]:
        print(f"  - Modus:    {options['apply_mode']}")
        print(f"  - Confirm:  {'Ja' if options['apply_confirm'] else 'Nein'}")
    print(f"Fail-Fast:    {'Ja' if options['fail_fast'] else 'Nein'}")
    print(f"Streaming:    {'Ja' if not options['no_streaming'] else 'Nein'}")
    print(f"Task-Split:   {'Ja' if options['task_split'] else 'Nein'}")
    if "resume_run" in options and options["resume_run"]:
        print(f"Resume:       {options['resume_run']}")
    print("=" * 60)


def interactive_run(argv: Optional[List[str]] = None) -> int:
    """
    Interactive/CLI hybrid mode.

    Prompts for missing inputs, summarizes options, and runs the pipeline.
    """
    args = parse_args_run(argv)

    has_family = args.family is not None
    has_task = args.task is not None
    has_resume = args.resume_run is not None
    is_interactive = not args.non_interactive

    # Validate required args in non-interactive mode
    if not has_family or (not has_task and not has_resume):
        if not is_interactive:
            print_error("--family und --task sind erforderlich im nicht-interaktiven Modus.")
            return int(ExitCode.VALIDATION_ERROR)
        print("\n=== Multi-Agent Codex - Interactive Mode ===\n")

    # Select family
    if not has_family:
        family_path = _select_family_interactive()
        if family_path is None:
            return int(ExitCode.CONFIG_ERROR)
    else:
        family_path = _get_family_from_args(args.family)
        if family_path is None:
            return int(ExitCode.VALIDATION_ERROR)

    # Get task
    if not has_task and not has_resume:
        task = _get_task_interactive()
        if task is None:
            return int(ExitCode.VALIDATION_ERROR)
    elif has_task:
        task = args.task
    else:
        task = f"[RESUME] {args.resume_run}"

    # Get options
    if not has_family and not has_task:
        options = _get_options_interactive(args)
    else:
        options = {
            "workdir": args.dir,
            "apply": args.apply,
            "apply_mode": args.apply_mode,
            "apply_confirm": args.apply_confirm,
            "fail_fast": args.fail_fast,
            "task_split": args.task_split,
            "no_streaming": args.no_streaming,
            "resume_run": args.resume_run,
        }

    # Build final args
    final_args = argparse.Namespace(
        config=str(family_path),
        task=task,
        dir=options["workdir"],
        timeout=args.timeout,
        apply=options["apply"],
        apply_mode=options["apply_mode"],
        apply_roles=args.apply_roles,
        apply_confirm=options["apply_confirm"],
        fail_fast=options["fail_fast"],
        ignore_fail=args.ignore_fail,
        task_split=options["task_split"],
        no_task_resume=args.no_task_resume,
        no_streaming=options["no_streaming"],
        resume_run=args.resume_run,
        max_files=args.max_files,
        max_file_bytes=args.max_file_bytes,
        validate_config=False,
    )

    # Load config
    try:
        cfg = load_app_config(family_path)
    except FileNotFoundError as exc:
        print_error(f"Konfigurationsdatei nicht gefunden: {exc}")
        return int(ExitCode.CONFIG_ERROR)
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print_error(f"Ungueltige Konfiguration: {exc}")
        return int(ExitCode.CONFIG_ERROR)

    # Print summary and confirm
    _print_run_summary(family_path, task, options)

    if not args.yes:
        confirm = input("\nTask starten? (Y/n): ").strip().lower()
        if confirm == "n":
            print("Abgebrochen.")
            return int(ExitCode.SUCCESS)

    print("\n" + "=" * 60)
    print("STARTE MULTI-AGENT PIPELINE")
    print("=" * 60 + "\n")

    return run_pipeline(final_args, cfg)
