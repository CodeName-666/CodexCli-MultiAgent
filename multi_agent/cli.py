from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import List, Optional

from .config_loader import load_app_config
from .constants import DEFAULT_CONFIG_PATH, DEFAULT_MAX_FILE_BYTES, DEFAULT_MAX_FILES, DEFAULT_TIMEOUT_SEC
from .pipeline import build_pipeline


def parse_args(cfg, argv: Optional[List[str]] = None) -> argparse.Namespace:
    cli = cfg.cli
    args_cfg = cli["args"]
    p = argparse.ArgumentParser(description=str(cli["description"]))
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
    p.add_argument("--fail-fast", action="store_true", help=str(args_cfg["fail_fast"]["help"]))
    p.add_argument("--ignore-fail", action="store_true", help=str(args_cfg["ignore_fail"]["help"]))
    p.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES, help=str(args_cfg["max_files"]["help"]))
    p.add_argument(
        "--max-file-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=str(args_cfg["max_file_bytes"]["help"]),
    )
    return p.parse_args(argv)


def main() -> None:
    try:
        cfg = load_app_config(DEFAULT_CONFIG_PATH)
    except FileNotFoundError as e:
        print(f"Fehler: Konfigurationsdatei nicht gefunden: {e}", file=sys.stderr)
        sys.exit(2)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Fehler: Ungueltige Konfiguration: {e}", file=sys.stderr)
        sys.exit(2)

    args = parse_args(cfg)
    pipeline = build_pipeline()
    try:
        rc = asyncio.run(pipeline.run(args, cfg))
    except KeyboardInterrupt:
        print(f"\n{cfg.messages['interrupted']}", file=sys.stderr)
        rc = 130
    except FileNotFoundError as e:
        print(f"\n{cfg.messages['codex_not_found'].format(error=e)}", file=sys.stderr)
        print(cfg.messages["codex_tip"], file=sys.stderr)
        rc = 127
    sys.exit(rc)
