from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from .cli_adapter import CLIAdapter
from .cli_errors import print_error
from .constants import ExitCode, get_static_config_dir
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
from .utils import now_stamp, parse_cmd, summarize_text


async def run_split(pipeline, args: argparse.Namespace, cfg) -> int:
    workdir = Path(args.dir).resolve()
    try:
        task_text, task_source = load_task_text(args.task, workdir)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return int(ExitCode.VALIDATION_ERROR)
    split_cfg = cfg.task_split
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
                cli_config_path = get_static_config_dir() / "cli_config.json"
                cli_adapter = CLIAdapter(cli_config_path)
                codex_cmd, _, _ = cli_adapter.build_command_for_role(
                    provider_id=None,
                    prompt=None,
                    model=None,
                    timeout_sec=timeout_sec,
                )
            plan = plan_chunks_with_llm(headings, codex_cmd, timeout_sec, max_headings)
            chunks = build_chunks_from_plan(task_text, headings, plan)
        if not chunks:
            chunks = split_task_markdown(task_text, heading_level, min_chars, max_chars)
        if not chunks:
            print_error("Task-Splitting hat keine Chunks erzeugt.")
            return int(ExitCode.VALIDATION_ERROR)
        write_base_chunks(chunks, tasks_dir)
        manifest = init_manifest(split_id, task_source, chunks, tasks_dir)
        save_manifest(manifest_path, manifest)

    chunks_meta = manifest.get("chunks", [])
    if not chunks_meta:
        print_error("Task-Splitting Manifest ist leer.")
        return int(ExitCode.VALIDATION_ERROR)

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
            print_error(f"Base-Chunk fehlt: {base_file}")
            return int(ExitCode.VALIDATION_ERROR)
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
        entry["run_dir"] = str(workdir / str(cfg.paths.run_dir) / run_id)
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


def run_pipeline(args: argparse.Namespace, cfg) -> int:
    pipeline = build_pipeline()
    try:
        split_enabled = bool(args.task_split) or bool(cfg.task_split.get("enabled", False))
        if split_enabled:
            return asyncio.run(run_split(pipeline, args, cfg))
        return asyncio.run(pipeline.run(args, cfg))
    except KeyboardInterrupt:
        print(f"\n{cfg.messages['interrupted']}", file=sys.stderr)
        return int(ExitCode.INTERRUPTED)
    except FileNotFoundError as exc:
        print(f"\n{cfg.messages['codex_not_found'].format(error=exc)}", file=sys.stderr)
        print(cfg.messages["codex_tip"], file=sys.stderr)
        return 127
