from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .cli_errors import print_error
from .config_loader import load_app_config
from .constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILES,
    DEFAULT_TIMEOUT_SEC,
    ExitCode,
)
from .interactive import interactive_run
from .run_helpers import run_pipeline

try:
    from creators import multi_family_creator, multi_role_agent_creator
    CREATORS_AVAILABLE = True
except Exception:  # noqa: BLE001
    multi_family_creator = None
    multi_role_agent_creator = None
    CREATORS_AVAILABLE = False


class Command:
    name = ""

    def run(self, argv: List[str]) -> int:
        raise NotImplementedError


class CommandDispatcher:
    def __init__(self, commands: List[Command], default_command: str, fallback_command: str) -> None:
        self._commands = {cmd.name: cmd for cmd in commands}
        self._default = default_command
        self._fallback = fallback_command

    def dispatch(self, argv: List[str]) -> int:
        if not argv:
            return self._commands[self._default].run([])
        subcommand = argv[0]
        if subcommand in self._commands:
            return self._commands[subcommand].run(argv[1:])
        return self._commands[self._fallback].run(argv)


def _parse_config_path(argv: Optional[List[str]]) -> Path:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args, _ = parser.parse_known_args(argv)
    return Path(args.config)


def parse_args_task(cfg, argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse arguments for the task subcommand (original functionality)."""
    cli = cfg.cli
    args_cfg = cli.args
    p = argparse.ArgumentParser(description=str(cli.description))
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


class TaskCommand(Command):
    name = "task"

    def run(self, argv: List[str]) -> int:
        config_path = _parse_config_path(argv)
        try:
            cfg = load_app_config(config_path)
        except FileNotFoundError as exc:
            print_error(f"Konfigurationsdatei nicht gefunden: {exc}")
            return int(ExitCode.CONFIG_ERROR)
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print_error(f"Ungueltige Konfiguration: {exc}")
            return int(ExitCode.CONFIG_ERROR)

        args = parse_args_task(cfg, argv)
        if args.validate_config:
            from .schema_validator import validate_config

            ok, error = validate_config(Path(args.config))
            if not ok:
                print_error(f"Konfiguration ungueltig: {error}")
                return int(ExitCode.VALIDATION_ERROR)
            print("Konfiguration ist gueltig.")
            return int(ExitCode.SUCCESS)
        return run_pipeline(args, cfg)


class RunCommand(Command):
    name = "run"

    def run(self, argv: List[str]) -> int:
        return interactive_run(argv)


class CreateFamilyCommand(Command):
    name = "create-family"

    def run(self, argv: List[str]) -> int:
        if not CREATORS_AVAILABLE or multi_family_creator is None:
            print_error("Creator-Module nicht verfuegbar.")
            print("Stelle sicher, dass das 'creators' Verzeichnis im Python-Path ist.", file=sys.stderr)
            return int(ExitCode.CONFIG_ERROR)
        return int(multi_family_creator.main(argv))


class CreateRoleCommand(Command):
    name = "create-role"

    def run(self, argv: List[str]) -> int:
        if not CREATORS_AVAILABLE or multi_role_agent_creator is None:
            print_error("Creator-Module nicht verfuegbar.")
            print("Stelle sicher, dass das 'creators' Verzeichnis im Python-Path ist.", file=sys.stderr)
            return int(ExitCode.CONFIG_ERROR)
        original_argv = sys.argv
        try:
            sys.argv = [sys.argv[0]] + list(argv)
            try:
                multi_role_agent_creator.main()
            except SystemExit as exc:
                return int(exc.code or 0)
        finally:
            sys.argv = original_argv
        return int(ExitCode.SUCCESS)


def build_dispatcher() -> CommandDispatcher:
    commands: List[Command] = [
        TaskCommand(),
        RunCommand(),
        CreateFamilyCommand(),
        CreateRoleCommand(),
    ]
    return CommandDispatcher(commands, default_command="run", fallback_command="task")
