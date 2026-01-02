from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .cli_adapter import CLIAdapter
from .constants import get_static_config_dir, DEFAULT_TOKEN_CHARS
from .executor import AgentExecutor, CLIClient
from .coordination import CoordinationLog, TaskBoard
from .diff_applier import BaseDiffApplier, UnifiedDiffApplier
from .diff_utils import detect_file_overlaps, extract_touched_files_from_unified_diff, validate_touched_files_against_allowed_paths
from .models import AgentResult, AgentSpec, AppConfig, RoleConfig, ShardPlan
from .progress import ProgressReporter
from .run_logger import JsonRunLogger
from .sharding import create_shard_plan, save_shard_plan
from .snapshot import BaseSnapshotter, WorkspaceSnapshotter
from .utils import (
    extract_error_reason,
    estimate_tokens,
    format_prompt,
    get_status_text,
    normalize_output_text,
    now_stamp,
    summarize_text,
    truncate_text,
    validate_output_sections,
    write_text,
)


@dataclass
class PipelineRunContext:
    args: argparse.Namespace
    cfg: AppConfig
    workdir: Path
    run_id: str
    run_dir: Path
    task_payload: Dict[str, object]
    task_display: str
    task_full: str
    apply_role_ids: set[str]
    reporter: ProgressReporter
    report_lock: asyncio.Lock
    context_lock: asyncio.Lock
    apply_lock: asyncio.Lock
    meta_lock: asyncio.Lock
    run_meta: Dict[str, object]
    json_logger: JsonRunLogger
    context: Dict[str, str] = field(default_factory=dict)
    results: Dict[str, List[AgentResult]] = field(default_factory=dict)
    apply_log_lines: List[str] = field(default_factory=list)
    task_board: TaskBoard | None = None
    coordination_log: CoordinationLog | None = None
    abort_run: bool = False


class Pipeline:
    def __init__(
        self,
        snapshotter: BaseSnapshotter,
        diff_applier: BaseDiffApplier,
    ) -> None:
        self._snapshotter = snapshotter
        self._diff_applier = diff_applier

    async def run(self, args: argparse.Namespace, cfg: AppConfig, run_id_override: str | None = None) -> int:
        workdir = Path(args.dir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)

        run_id = run_id_override or now_stamp()
        run_dir = workdir / str(cfg.paths.run_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        raw_task = (args.task or "").strip()
        if not raw_task:
            print(cfg.messages["error_task_empty"], file=sys.stderr)
            return 2
        try:
            task_payload = self._prepare_task(raw_task, workdir, run_dir, cfg.task_limits)
        except (FileNotFoundError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2

        try:
            apply_role_ids = self._resolve_apply_role_ids(args, cfg)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        reporter = self._build_reporter(args, cfg, apply_role_ids, workdir, run_dir)
        report_lock = asyncio.Lock()
        context_lock = asyncio.Lock()
        apply_lock = asyncio.Lock()
        meta_lock = asyncio.Lock()

        run_meta = self._build_run_meta(
            run_id=run_id,
            workdir=workdir,
            args=args,
            task_payload=task_payload,
            task_full=str(task_payload.get("full") or ""),
            task_display=str(task_payload.get("display") or ""),
        )
        json_logger = self._build_json_logger(cfg, workdir, run_id, run_dir)
        json_logger.log("run_start", {"run_id": run_id})

        ctx = PipelineRunContext(
            args=args,
            cfg=cfg,
            workdir=workdir,
            run_id=run_id,
            run_dir=run_dir,
            task_payload=task_payload,
            task_display=str(task_payload.get("display") or ""),
            task_full=str(task_payload.get("full") or ""),
            apply_role_ids=apply_role_ids,
            reporter=reporter,
            report_lock=report_lock,
            context_lock=context_lock,
            apply_lock=apply_lock,
            meta_lock=meta_lock,
            run_meta=run_meta,
            json_logger=json_logger,
        )

        status = "ok"
        error_detail = ""
        try:
            return await self._execute_run(ctx)
        except Exception as exc:  # noqa: BLE001
            status = "error"
            error_detail = str(exc)
            raise
        finally:
            self._finalize_run(ctx, status, error_detail)

    def _build_reporter(
        self,
        args: argparse.Namespace,
        cfg: AppConfig,
        apply_role_ids: set[str],
        workdir: Path,
        run_dir: Path,
    ) -> ProgressReporter:
        apply_roles = [role for role in cfg.roles if role.apply_diff]
        total_agents = sum(role.instances for role in cfg.roles)
        apply_instances = sum(role.instances for role in apply_roles if role.id in apply_role_ids)
        total_steps = 1 + total_agents + (apply_instances if args.apply else 0) + 1
        reporter = ProgressReporter(total_steps=total_steps)
        reporter.start(f"Workspace: {workdir} | Run-Ordner: {run_dir}")
        return reporter

    @staticmethod
    def _build_run_meta(
        run_id: str,
        workdir: Path,
        args: argparse.Namespace,
        task_payload: Dict[str, object],
        task_full: str,
        task_display: str,
    ) -> Dict[str, object]:
        return {
            "run_id": run_id,
            "start_time": time.time(),
            "workspace": str(workdir),
            "args": vars(args),
            "roles": {},
            "snapshot": {},
            "task": {
                "source": task_payload.get("source", ""),
                "full_length": len(task_full),
                "display_length": len(task_display),
                "truncated": bool(task_payload.get("truncated", False)),
                "file_ref": task_payload.get("file_ref", ""),
            },
        }

    async def _execute_run(self, ctx: PipelineRunContext) -> int:
        snapshot_text = self._snapshot_workspace(ctx)
        await self._initialize_coordination(ctx, snapshot_text)
        await self._run_roles(ctx)
        if ctx.args.apply and ctx.args.apply_mode == "end":
            self._apply_end_diffs(ctx)
        self._write_apply_log(ctx)
        self._render_summary(ctx)
        return self._final_exit_code(ctx)

    def _snapshot_workspace(self, ctx: PipelineRunContext) -> str:
        ctx.reporter.step("Snapshot", "Workspace wird gescannt", advance=1)
        snapshot_result = self._snapshotter.build_snapshot(
            ctx.workdir,
            ctx.cfg.snapshot,
            max_files=ctx.args.max_files,
            max_bytes_per_file=ctx.args.max_file_bytes,
            task=ctx.task_full,
        )
        snapshot_text = snapshot_result.text
        write_text(ctx.run_dir / str(ctx.cfg.paths.snapshot_filename), snapshot_text)
        ctx.reporter.step("Snapshot", "Snapshot gespeichert", advance=0)

        ctx.run_meta["snapshot"] = {
            "files_count": len(snapshot_result.files),
            "cache_hit": snapshot_result.cache_hit,
            "delta_used": snapshot_result.delta_used,
            "max_bytes_per_file": snapshot_result.max_bytes_per_file,
            "total_bytes": snapshot_result.total_bytes,
        }
        ctx.json_logger.log("snapshot", ctx.run_meta["snapshot"])
        return snapshot_text

    async def _initialize_coordination(self, ctx: PipelineRunContext, snapshot_text: str) -> None:
        coordination_cfg = ctx.cfg.coordination
        task_board_path = self._resolve_coordination_path(
            ctx.workdir, ctx.run_dir, coordination_cfg.task_board, ctx.run_id, default_name="task_board.json"
        )
        coordination_log_path = self._resolve_coordination_path(
            ctx.workdir, ctx.run_dir, coordination_cfg.channel, ctx.run_id, default_name="coordination.log"
        )
        task_board = TaskBoard(
            task_board_path,
            lock_mode=coordination_cfg.lock_mode,
            lock_timeout_sec=coordination_cfg.lock_timeout_sec,
        )
        coordination_log = CoordinationLog(coordination_log_path)

        ctx.task_board = task_board
        ctx.coordination_log = coordination_log
        ctx.context = {
            "task": ctx.task_display,
            "task_full_path": str(ctx.task_payload.get("file_ref") or ""),
            "snapshot": snapshot_text,
            "task_board_path": str(task_board_path),
            "coordination_log_path": str(coordination_log_path),
            "last_applied_diff": "",
            "repair_note": "",
        }
        for role in ctx.cfg.roles:
            ctx.context.setdefault(f"{role.id}_summary", "")
            ctx.context.setdefault(f"{role.id}_output", "")

        await task_board.initialize(self._build_task_board(ctx.cfg))
        coordination_log.append("orchestrator", "init", {"run_id": ctx.run_id})

    async def _run_roles(self, ctx: PipelineRunContext) -> None:
        pending_roles: Dict[str, RoleConfig] = {role.id: role for role in ctx.cfg.roles}
        completed_roles: set[str] = set()

        while pending_roles and not ctx.abort_run:
            ready_roles = [
                role
                for role in pending_roles.values()
                if all(dep in completed_roles for dep in self._effective_deps(ctx.cfg, role))
            ]
            if not ready_roles:
                ctx.reporter.error("Abhaengigkeiten blockieren die Ausfuehrung (Zyklus?)")
                break
            tasks = [asyncio.create_task(self._run_role(ctx, role)) for role in ready_roles]
            completed = await asyncio.gather(*tasks)
            for role_id in completed:
                completed_roles.add(role_id)
                pending_roles.pop(role_id, None)

    async def _run_role(self, ctx: PipelineRunContext, role_cfg: RoleConfig) -> str:
        if ctx.task_board is None or ctx.coordination_log is None:
            raise RuntimeError("Coordination not initialized")
        task_board = ctx.task_board
        coordination_log = ctx.coordination_log

        role_start = time.monotonic()
        ctx.json_logger.log("role_start", {"role": role_cfg.id})

        shard_plan: ShardPlan | None = None
        if role_cfg.shard_mode != "none" and role_cfg.instances > 1:
            async with ctx.context_lock:
                current_task = ctx.context.get("task", ctx.task_display)
            shard_plan = create_shard_plan(role_cfg, current_task)
            if shard_plan:
                shard_plan_path = ctx.run_dir / f"{role_cfg.id}_shard_plan.json"
                save_shard_plan(shard_plan, shard_plan_path)
                ctx.json_logger.log(
                    "shard_plan_created",
                    {
                        "role": role_cfg.id,
                        "shard_count": shard_plan.shard_count,
                        "shard_mode": shard_plan.shard_mode,
                    },
                )

        if role_cfg.run_if_review_critical:
            async with ctx.context_lock:
                reviewer_output = ctx.context.get("reviewer_output", "")
            if not self._review_has_critical(ctx.cfg.feedback_loop, reviewer_output):
                await self._mark_role_skipped(role_cfg, task_board, coordination_log)
                ctx.json_logger.log("role_skip", {"role": role_cfg.id, "reason": "no_critical_review"})
                async with ctx.meta_lock:
                    ctx.run_meta["roles"][role_cfg.id] = {
                        "instances_total": role_cfg.instances,
                        "status": "skipped",
                        "duration_sec": 0.0,
                        "returncodes": [],
                    }
                async with ctx.context_lock:
                    ctx.context[f"{role_cfg.id}_summary"] = ""
                    ctx.context[f"{role_cfg.id}_output"] = ""
                ctx.results[role_cfg.id] = []
                return role_cfg.id

        validation_context = dict(ctx.context)
        validation_context["role_id"] = role_cfg.id
        validation_context["role_name"] = role_cfg.name
        validation_context["role_instance_id"] = "1"
        validation_context["role_instance"] = f"{role_cfg.id}#1"
        validation_context["repair_note"] = ""
        try:
            _ = format_prompt(role_cfg.prompt_template, validation_context, role_cfg.id, ctx.cfg.messages)
        except ValueError as exc:
            ctx.reporter.error(str(exc))
            print(str(exc), file=sys.stderr)
            ctx.abort_run = True
            return role_cfg.id

        role_executor = self._build_executor(ctx.cfg, role_cfg, ctx.args.timeout)
        tasks = [
            asyncio.create_task(self._run_role_instance(ctx, role_cfg, idx, shard_plan, role_executor))
            for idx in range(1, role_cfg.instances + 1)
        ]
        role_results = await asyncio.gather(*tasks)
        ctx.results[role_cfg.id] = role_results

        if shard_plan:
            validation_ok, validation_msg = await self._validate_shard_results(
                role_cfg,
                shard_plan,
                role_results,
                ctx.run_dir,
                ctx.json_logger,
            )
            if not validation_ok:
                async with ctx.report_lock:
                    ctx.reporter.error(f"Shard validation failed for {role_cfg.id}: {validation_msg}")
                if role_cfg.overlap_policy == "forbid":
                    ctx.abort_run = True
                elif role_cfg.overlap_policy == "warn":
                    async with ctx.report_lock:
                        ctx.reporter.step("Warning", f"Overlaps detected in {role_cfg.id}", advance=0)

        summary_text = self._combine_outputs(
            role_cfg,
            role_results,
            lambda text: summarize_text(normalize_output_text(text), max_chars=ctx.cfg.summary_max_chars),
        )
        output_text = self._combine_outputs(
            role_cfg,
            role_results,
            lambda text: normalize_output_text(text),
        )

        async with ctx.context_lock:
            ctx.context[f"{role_cfg.id}_summary"] = summary_text
            ctx.context[f"{role_cfg.id}_output"] = output_text

        if (
            ctx.args.apply
            and ctx.args.apply_mode == "role"
            and role_cfg.apply_diff
            and role_cfg.id in ctx.apply_role_ids
        ):
            async with ctx.apply_lock:
                applied_ok, had_error, last_diff = await self._apply_role_diffs(
                    ctx.args,
                    ctx.cfg,
                    ctx.workdir,
                    role_cfg,
                    role_results,
                    ctx.reporter,
                    ctx.apply_log_lines,
                    confirm=ctx.args.apply_confirm,
                )
            if applied_ok:
                snapshot_result = self._snapshotter.build_snapshot(
                    ctx.workdir,
                    ctx.cfg.snapshot,
                    max_files=ctx.args.max_files,
                    max_bytes_per_file=ctx.args.max_file_bytes,
                    task=ctx.task_full,
                )
                snapshot_name = f"snapshot_after_{role_cfg.id}.txt"
                write_text(ctx.run_dir / snapshot_name, snapshot_result.text)
                async with ctx.context_lock:
                    ctx.context["snapshot"] = snapshot_result.text
                    if last_diff:
                        ctx.context["last_applied_diff"] = last_diff
            if ctx.args.fail_fast and had_error:
                ctx.abort_run = True

        role_end = time.monotonic()
        async with ctx.meta_lock:
            role_meta = ctx.run_meta["roles"].setdefault(role_cfg.id, {"instances": {}})
            role_meta["instances_total"] = role_cfg.instances
            role_meta["duration_sec"] = role_end - role_start
            role_meta["returncodes"] = [res.returncode for res in role_results]
        ctx.json_logger.log("role_end", {"role": role_cfg.id, "duration_sec": role_end - role_start})
        return role_cfg.id

    async def _run_role_instance(
        self,
        ctx: PipelineRunContext,
        role_cfg: RoleConfig,
        instance_id: int,
        shard_plan: ShardPlan | None,
        role_executor: AgentExecutor,
    ) -> AgentResult:
        if ctx.task_board is None or ctx.coordination_log is None:
            raise RuntimeError("Coordination not initialized")
        task_board = ctx.task_board
        coordination_log = ctx.coordination_log

        instance_label = f"{role_cfg.id}#{instance_id}"
        agent = AgentSpec(f"{role_cfg.name}#{instance_id}", role_cfg.role)
        async with ctx.context_lock:
            local_context = dict(ctx.context)
        local_context["role_id"] = role_cfg.id
        local_context["role_name"] = role_cfg.name
        local_context["role_instance_id"] = str(instance_id)
        local_context["role_instance"] = instance_label

        shard_index = instance_id - 1
        if shard_plan and shard_index < len(shard_plan.shards):
            shard = shard_plan.shards[shard_index]
            local_context["task"] = shard.content
            local_context["shard_id"] = shard.id
            local_context["shard_title"] = shard.title
            local_context["shard_goal"] = shard.goal
            local_context["allowed_paths"] = ", ".join(shard.allowed_paths)

        prompt, prompt_chars, truncated, prompt_tokens, max_prompt_tokens = self._build_prompt(
            role_cfg,
            local_context,
            ctx.cfg,
        )
        out_file = ctx.run_dir / self._build_output_filename(ctx.cfg, role_cfg, instance_id)

        await task_board.update_task(
            instance_label,
            {"status": "in_progress", "claimed_by": instance_label},
        )
        coordination_log.append(
            instance_label,
            "claim",
            {"task": instance_label, "out_file": str(out_file)},
        )

        retries_left = max(0, role_cfg.retries)
        attempt = 0
        backoff_sec = float(ctx.cfg.role_defaults.get("retry_backoff_sec", 1.0))
        last_result: AgentResult | None = None

        while True:
            async with ctx.report_lock:
                ctx.reporter.step("Agent-Lauf", f"Rolle: {instance_label}, attempt {attempt + 1}", advance=1)
            res = await role_executor.run_agent(
                agent,
                prompt,
                ctx.workdir,
                out_file,
            )
            last_result = res
            ctx.json_logger.log(
                "agent_result",
                {
                    "role": role_cfg.id,
                    "instance": instance_id,
                    "returncode": res.returncode,
                    "prompt_chars": prompt_chars,
                    "prompt_tokens": prompt_tokens,
                    "prompt_max_tokens": max_prompt_tokens or 0,
                    "truncated": truncated,
                    "stdout_chars": len(res.stdout),
                    "stderr_chars": len(res.stderr),
                },
            )
            async with ctx.meta_lock:
                role_meta = ctx.run_meta["roles"].setdefault(role_cfg.id, {"instances": {}})
                role_meta["instances"][instance_label] = {
                    "returncode": res.returncode,
                    "prompt_chars": prompt_chars,
                    "prompt_tokens": prompt_tokens,
                    "prompt_max_tokens": max_prompt_tokens or 0,
                    "stdout_chars": len(res.stdout),
                    "stderr_chars": len(res.stderr),
                    "attempts": role_cfg.retries + 1 - retries_left,
                }
            if self._output_ok(res, role_cfg):
                break
            if retries_left <= 0:
                break
            if not self._should_retry(res, role_cfg):
                break
            retries_left -= 1
            attempt += 1
            shrink = ctx.cfg.role_defaults.get("retry_prompt_shrink", 0.85)
            local_context = dict(local_context)
            prompt, prompt_chars, truncated, prompt_tokens, max_prompt_tokens = self._build_prompt(
                role_cfg,
                local_context,
                ctx.cfg,
                shrink_factor=float(shrink),
                repair_missing=self._repair_note(role_cfg, res.stdout),
            )
            await asyncio.sleep(backoff_sec)
        if last_result is None:
            raise RuntimeError("Agent did not run")
        await task_board.update_task(
            instance_label,
            {"status": "done", "claimed_by": instance_label, "returncode": last_result.returncode},
        )
        coordination_log.append(
            instance_label,
            "complete",
            {"task": instance_label, "returncode": last_result.returncode},
        )
        async with ctx.report_lock:
            ctx.reporter.step("Agent-Ende", f"Rolle: {instance_label}, rc={last_result.returncode}", advance=0)
        return last_result

    def _apply_end_diffs(self, ctx: PipelineRunContext) -> None:
        for role_cfg in ctx.cfg.roles:
            if not role_cfg.apply_diff or role_cfg.id not in ctx.apply_role_ids:
                continue
            role_results = ctx.results.get(role_cfg.id, [])
            if not role_results:
                continue
            for res in role_results:
                label = res.agent.name
                ctx.reporter.step("Diff-Apply", f"Rolle: {label}", advance=1)
                diff = self._diff_applier.extract_diff(res.stdout)
                if not diff:
                    ctx.reporter.step("Diff-Apply", f"Rolle: {label}, kein diff", advance=0)
                    ctx.apply_log_lines.append(ctx.cfg.messages["apply_no_diff"].format(label=label))
                    continue
                if ctx.args.apply_confirm and not self._confirm_diff(label, diff):
                    ctx.apply_log_lines.append(ctx.cfg.messages["apply_skipped"].format(label=label))
                    continue
                ok, msg = self._diff_applier.apply(
                    ctx.workdir, diff, ctx.cfg.diff_messages, ctx.cfg.diff_safety, ctx.cfg.diff_apply
                )
                if ok:
                    ctx.reporter.step("Diff-Apply", f"Rolle: {label}, ok", advance=0)
                    ctx.apply_log_lines.append(ctx.cfg.messages["apply_ok"].format(label=label, message=msg))
                else:
                    ctx.reporter.step("Diff-Apply", f"Rolle: {label}, fehler", advance=0)
                    ctx.apply_log_lines.append(ctx.cfg.messages["apply_error"].format(label=label, message=msg))
                    if ctx.args.fail_fast:
                        ctx.reporter.error(f"Diff-Apply abgebrochen: {label}")
                        break

    def _write_apply_log(self, ctx: PipelineRunContext) -> None:
        if ctx.args.apply and ctx.args.apply_mode == "end":
            write_text(
                ctx.run_dir / str(ctx.cfg.paths.apply_log_filename),
                "\n".join(ctx.apply_log_lines) + "\n",
            )
        elif ctx.args.apply and ctx.apply_log_lines:
            write_text(
                ctx.run_dir / str(ctx.cfg.paths.apply_log_filename),
                "\n".join(ctx.apply_log_lines) + "\n",
            )

    def _render_summary(self, ctx: PipelineRunContext) -> None:
        ctx.reporter.step("Summary", "Ausgaben werden zusammengefasst", advance=1)
        print("\n" + ctx.cfg.messages["run_complete"])
        print(ctx.cfg.messages["workspace_label"].format(workspace=ctx.workdir))
        print(ctx.cfg.messages["run_dir_label"].format(run_dir=ctx.run_dir))
        print("\n" + ctx.cfg.messages["status_header"])
        for role_cfg in ctx.cfg.roles:
            role_results = ctx.results.get(role_cfg.id, [])
            if not role_results:
                continue
            for res in role_results:
                line = ctx.cfg.messages["status_line"].format(
                    agent_name=res.agent.name,
                    rc=res.returncode,
                    status=get_status_text(res.returncode, res.stdout, ctx.cfg.messages),
                    ok=res.ok,
                    out_file=res.out_file.name,
                )
                print(line)
                if res.returncode != 0:
                    reason = extract_error_reason(res.stdout, res.stderr)
                    print(ctx.cfg.messages["status_reason"].format(reason=reason))

        if ctx.args.apply:
            print("\n" + ctx.cfg.messages["patch_apply_header"])
            for line in ctx.apply_log_lines:
                print("-", line)

        final_role_id = ctx.cfg.final_role_id or (ctx.cfg.roles[-1].id if ctx.cfg.roles else "")
        final_results = ctx.results.get(final_role_id, [])
        if final_results:
            print("\n" + ctx.cfg.messages["integrator_output_header"] + "\n")
            final_role_cfg = next((role for role in ctx.cfg.roles if role.id == final_role_id), None)
            final_output = self._combine_outputs(final_role_cfg or final_role_id, final_results, lambda text: text)
            final_summary = summarize_text(final_output, max_chars=ctx.cfg.final_summary_max_chars)
            print(final_summary)
            write_text(ctx.run_dir / "final_summary.txt", final_summary + "\n")
            print("")

    def _final_exit_code(self, ctx: PipelineRunContext) -> int:
        if ctx.args.ignore_fail:
            ctx.reporter.finish("Status ignoriert (ignore-fail)")
            return 0
        any_fail = any(not res.ok for res_list in ctx.results.values() for res in res_list)
        ctx.reporter.finish("Fertig")
        return 1 if any_fail else 0

    @staticmethod
    def _finalize_run(ctx: PipelineRunContext, status: str, error_detail: str) -> None:
        ctx.run_meta["status"] = status
        if error_detail:
            ctx.run_meta["error"] = error_detail
        ctx.run_meta["end_time"] = time.time()
        ctx.run_meta["duration_sec"] = ctx.run_meta["end_time"] - ctx.run_meta["start_time"]
        write_text(ctx.run_dir / "run.json", json.dumps(ctx.run_meta, indent=2, ensure_ascii=True) + "\n")
        ctx.json_logger.log("run_end", {"run_id": ctx.run_id, "duration_sec": ctx.run_meta["duration_sec"]})

    @staticmethod
    def _combine_outputs(
        role_cfg: RoleConfig | str,
        results: List[AgentResult],
        transform,
    ) -> str:
        blocks: List[str] = []
        max_output_chars = None
        if isinstance(role_cfg, RoleConfig):
            max_output_chars = role_cfg.max_output_chars
        for res in results:
            content = (transform(res.stdout) or "").strip()
            if not content:
                continue
            if max_output_chars:
                content = truncate_text(content, max_output_chars)
            blocks.append(f"[{res.agent.name}]\n{content}")
        return "\n\n".join(blocks).strip()

    @staticmethod
    def _resolve_coordination_path(
        workdir: Path,
        run_dir: Path,
        template: str,
        run_id: str,
        default_name: str,
    ) -> Path:
        raw = (template or "").strip()
        if not raw:
            return run_dir / default_name
        raw = raw.replace("<run_id>", run_id)
        path = Path(raw)
        if path.is_absolute():
            return path
        return workdir / path

    @staticmethod
    def _build_output_filename(cfg: AppConfig, role_cfg, instance_id: int) -> str:
        raw_pattern = str(cfg.outputs.pattern or "").strip()
        if not raw_pattern:
            if role_cfg.instances > 1:
                raw_pattern = "<role>_<instance>.md"
            else:
                raw_pattern = "<role>.md"
        pattern = raw_pattern
        if "{role}" in pattern or "{instance}" in pattern:
            return pattern.format(role=role_cfg.id, instance=instance_id)
        return pattern.replace("<role>", role_cfg.id).replace("<instance>", str(instance_id))

    @staticmethod
    def _build_task_board(cfg: AppConfig) -> List[Dict[str, object]]:
        tasks: List[Dict[str, object]] = []
        role_instance_ids = {
            role.id: [f"{role.id}#{idx}" for idx in range(1, role.instances + 1)]
            for role in cfg.roles
        }
        for role_cfg in cfg.roles:
            deps = []
            for dep in role_cfg.depends_on:
                deps.extend(role_instance_ids.get(dep, []))
            for instance_id in range(1, role_cfg.instances + 1):
                task_id = f"{role_cfg.id}#{instance_id}"
                tasks.append(
                    {
                        "id": task_id,
                        "title": f"{role_cfg.id} instance {instance_id}",
                        "status": "open",
                        "claimed_by": "",
                        "deps": deps,
                    }
                )
        return tasks

    @staticmethod
    def _resolve_apply_role_ids(args: argparse.Namespace, cfg: AppConfig) -> set[str]:
        if not args.apply_roles:
            return {role.id for role in cfg.roles if role.apply_diff}
        raw: List[str] = []
        for entry in args.apply_roles:
            raw.extend([item.strip() for item in entry.split(",") if item.strip()])
        valid = {role.id for role in cfg.roles}
        unknown = sorted(set(raw) - valid)
        if unknown:
            raise ValueError(cfg.messages["error_apply_roles_unknown"].format(roles=", ".join(unknown)))
        return set(raw)

    async def _apply_role_diffs(
        self,
        args: argparse.Namespace,
        cfg: AppConfig,
        workdir: Path,
        role_cfg,
        role_results: List[AgentResult],
        reporter: ProgressReporter,
        apply_log_lines: List[str],
        confirm: bool,
    ) -> tuple[bool, bool, str]:
        applied_ok = False
        had_error = False
        last_diff_text = ""
        for res in role_results:
            label = res.agent.name
            reporter.step("Diff-Apply", f"Rolle: {label}", advance=1)
            diff = self._diff_applier.extract_diff(res.stdout)
            if not diff:
                reporter.step("Diff-Apply", f"Rolle: {label}, kein diff", advance=0)
                apply_log_lines.append(cfg.messages["apply_no_diff"].format(label=label))
                continue
            if confirm and not self._confirm_diff(label, diff):
                apply_log_lines.append(cfg.messages["apply_skipped"].format(label=label))
                continue
            ok, msg = self._diff_applier.apply(workdir, diff, cfg.diff_messages, cfg.diff_safety, cfg.diff_apply)
            if ok:
                applied_ok = True
                last_diff_text = diff
                reporter.step("Diff-Apply", f"Rolle: {label}, ok", advance=0)
                apply_log_lines.append(cfg.messages["apply_ok"].format(label=label, message=msg))
            else:
                had_error = True
                reporter.step("Diff-Apply", f"Rolle: {label}, fehler", advance=0)
                apply_log_lines.append(cfg.messages["apply_error"].format(label=label, message=msg))
                if args.fail_fast:
                    reporter.error(f"Diff-Apply abgebrochen: {label}")
                    break
        return applied_ok, had_error, last_diff_text

    @staticmethod
    def _output_ok(res: AgentResult, role_cfg: RoleConfig) -> bool:
        if res.returncode != 0:
            return False
        if not res.stdout.strip():
            return False
        if role_cfg.expected_sections:
            ok, _ = validate_output_sections(res.stdout, role_cfg.expected_sections)
            return ok
        return True

    @staticmethod
    def _should_retry(res: AgentResult, role_cfg: RoleConfig) -> bool:
        if res.returncode == 124:
            return True
        if not res.stdout.strip():
            return True
        if role_cfg.expected_sections:
            ok, _ = validate_output_sections(res.stdout, role_cfg.expected_sections)
            return not ok
        return False

    @staticmethod
    def _repair_note(role_cfg: RoleConfig, stdout: str) -> str:
        if not role_cfg.expected_sections:
            return ""
        ok, missing = validate_output_sections(stdout, role_cfg.expected_sections)
        if ok:
            return ""
        return "FEHLENDE SEKTIONEN: " + ", ".join(missing)

    @staticmethod
    def _prepare_task(
        raw_task: str,
        workdir: Path,
        run_dir: Path,
        task_limits: Dict[str, object],
    ) -> Dict[str, object]:
        task = (raw_task or "").strip()
        task_source = ""
        task_full = task
        if task.startswith("@"):
            path_raw = task[1:].strip()
            if not path_raw:
                raise ValueError("Fehler: Task-Datei ist leer (nutze '@pfad').")
            task_path = Path(path_raw).expanduser()
            if not task_path.is_absolute():
                task_path = (workdir / task_path).resolve()
            try:
                task_full = task_path.read_text(encoding="utf-8")
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Fehler: Task-Datei nicht gefunden: {task_path}") from exc
            task_source = str(task_path)

        if not task_full.strip():
            raise ValueError("Fehler: --task ist leer.")

        inline_max = int(task_limits.get("inline_max_chars", 2400) or 2400)
        summary_max = int(task_limits.get("summary_max_chars", 1600) or 1600)
        full_name = str(task_limits.get("full_text_filename") or "task_full.md")

        truncated = False
        task_display = task_full
        if inline_max > 0 and len(task_full) > inline_max:
            truncated = True
            if summary_max <= 0:
                summary_max = inline_max
            summary_max = max(256, min(summary_max, inline_max))
            task_display = summarize_text(task_full, max_chars=summary_max)

        needs_full_file = bool(task_source) or truncated
        task_file_ref = ""
        if needs_full_file:
            full_path = run_dir / full_name
            write_text(full_path, task_full)
            try:
                task_file_ref = str(full_path.relative_to(workdir))
            except ValueError:
                task_file_ref = str(full_path)
            task_display = f"{task_display}\n\n[VOLLTEXT: {task_file_ref}]"

        return {
            "display": task_display,
            "full": task_full,
            "file_ref": task_file_ref,
            "source": task_source,
            "truncated": truncated,
        }

    def _build_prompt(
        self,
        role_cfg: RoleConfig,
        context: Dict[str, str],
        cfg: AppConfig,
        shrink_factor: float = 1.0,
        repair_missing: str = "",
    ) -> tuple[str, int, bool, int, int]:
        max_prompt_chars = role_cfg.max_prompt_chars or int(cfg.role_defaults.get("max_prompt_chars", 0) or 0)
        prompt_limits = cfg.prompt_limits or {}
        token_chars = int(prompt_limits.get("token_chars", DEFAULT_TOKEN_CHARS) or DEFAULT_TOKEN_CHARS)
        max_prompt_tokens = role_cfg.max_prompt_tokens or int(cfg.role_defaults.get("max_prompt_tokens", 0) or 0)
        if max_prompt_tokens <= 0:
            model_name = role_cfg.model or ""
            model_max_tokens = (prompt_limits.get("model_max_tokens") or {}).get(model_name)
            if model_max_tokens is not None:
                max_prompt_tokens = int(model_max_tokens)
            else:
                max_prompt_tokens = int(prompt_limits.get("default_max_tokens", 0) or 0)
        prompt_context = dict(context)
        if repair_missing:
            prompt_context["repair_note"] = repair_missing
        else:
            prompt_context["repair_note"] = ""
        prompt_body = format_prompt(role_cfg.prompt_template, prompt_context, role_cfg.id, cfg.messages)
        prompt = cfg.system_rules + "\n\n" + prompt_body
        prompt_tokens = estimate_tokens(prompt, token_chars) if max_prompt_tokens > 0 else 0
        if max_prompt_chars <= 0 and max_prompt_tokens <= 0:
            return prompt, len(prompt), False, prompt_tokens, max_prompt_tokens
        if self._prompt_within_limits(prompt, max_prompt_chars, max_prompt_tokens, token_chars):
            return prompt, len(prompt), False, prompt_tokens, max_prompt_tokens

        compressed = dict(prompt_context)
        for key, value in list(compressed.items()):
            if key.endswith("_output"):
                compressed[key] = summarize_text(value, max_chars=cfg.summary_max_chars)
        snapshot_limit = int(cfg.role_defaults.get("snapshot_max_chars", 0) or 0)
        if snapshot_limit > 0 and "snapshot" in compressed:
            compressed["snapshot"] = summarize_text(compressed["snapshot"], max_chars=snapshot_limit)
        prompt_body = format_prompt(role_cfg.prompt_template, compressed, role_cfg.id, cfg.messages)
        prompt = cfg.system_rules + "\n\n" + prompt_body
        prompt_tokens = estimate_tokens(prompt, token_chars) if max_prompt_tokens > 0 else 0

        if shrink_factor < 1.0:
            target = int(self._effective_prompt_chars(max_prompt_chars, max_prompt_tokens, token_chars) * shrink_factor)
            if "snapshot" in compressed:
                compressed["snapshot"] = summarize_text(compressed["snapshot"], max_chars=target)
            prompt_body = format_prompt(role_cfg.prompt_template, compressed, role_cfg.id, cfg.messages)
            prompt = cfg.system_rules + "\n\n" + prompt_body
            prompt_tokens = estimate_tokens(prompt, token_chars) if max_prompt_tokens > 0 else 0

        if self._prompt_within_limits(prompt, max_prompt_chars, max_prompt_tokens, token_chars):
            return prompt, len(prompt), True, prompt_tokens, max_prompt_tokens

        overflow = self._prompt_overflow(prompt, max_prompt_chars, max_prompt_tokens, token_chars)
        if "snapshot" in compressed and overflow > 0:
            compressed["snapshot"] = truncate_text(compressed["snapshot"], max(len(compressed["snapshot"]) - overflow, 256))
            prompt_body = format_prompt(role_cfg.prompt_template, compressed, role_cfg.id, cfg.messages)
            prompt = cfg.system_rules + "\n\n" + prompt_body
        prompt_tokens = estimate_tokens(prompt, token_chars) if max_prompt_tokens > 0 else 0
        if not self._prompt_within_limits(prompt, max_prompt_chars, max_prompt_tokens, token_chars):
            overflow = self._prompt_overflow(prompt, max_prompt_chars, max_prompt_tokens, token_chars)
            if "task" in compressed and overflow > 0:
                compressed["task"] = truncate_text(compressed["task"], max(len(compressed["task"]) - overflow, 256))
                prompt_body = format_prompt(role_cfg.prompt_template, compressed, role_cfg.id, cfg.messages)
                prompt = cfg.system_rules + "\n\n" + prompt_body
                prompt_tokens = estimate_tokens(prompt, token_chars) if max_prompt_tokens > 0 else 0
        return prompt, len(prompt), True, prompt_tokens, max_prompt_tokens

    @staticmethod
    def _effective_prompt_chars(max_prompt_chars: int, max_prompt_tokens: int, token_chars: int) -> int:
        token_limit_chars = max_prompt_tokens * max(1, token_chars) if max_prompt_tokens > 0 else 0
        if max_prompt_chars > 0 and token_limit_chars > 0:
            return min(max_prompt_chars, token_limit_chars)
        return max_prompt_chars or token_limit_chars

    @staticmethod
    def _prompt_within_limits(
        prompt: str, max_prompt_chars: int, max_prompt_tokens: int, token_chars: int
    ) -> bool:
        if max_prompt_chars > 0 and len(prompt) > max_prompt_chars:
            return False
        if max_prompt_tokens > 0 and estimate_tokens(prompt, token_chars) > max_prompt_tokens:
            return False
        return True

    @staticmethod
    def _prompt_overflow(
        prompt: str, max_prompt_chars: int, max_prompt_tokens: int, token_chars: int
    ) -> int:
        overflow_chars = 0
        if max_prompt_chars > 0 and len(prompt) > max_prompt_chars:
            overflow_chars = len(prompt) - max_prompt_chars
        if max_prompt_tokens > 0:
            prompt_tokens = estimate_tokens(prompt, token_chars)
            if prompt_tokens > max_prompt_tokens:
                overflow_chars = max(overflow_chars, (prompt_tokens - max_prompt_tokens) * max(1, token_chars))
        return overflow_chars

    @staticmethod
    def _build_executor(cfg: AppConfig, role_cfg: RoleConfig, default_timeout: int) -> AgentExecutor:
        """
        Build executor for a role using CLIAdapter.

        All CLI providers (codex, claude, gemini) are configured via cli_config.json.
        The role can specify cli_provider, model, and cli_parameters.
        """
        timeout_sec = role_cfg.timeout_sec or int(default_timeout)
        if timeout_sec <= 0:
            timeout_sec = int(cfg.role_defaults.get("timeout_sec", 1200))

        # Load CLI adapter (single source of truth for all providers)
        cli_config_path = get_static_config_dir() / "cli_config.json"
        cli_adapter = CLIAdapter(cli_config_path)

        # Determine provider: role-specific or default
        provider_id = role_cfg.cli_provider  # None means use default from cli_config.json

        # Build command
        cmd, stdin_content, multiplier = cli_adapter.build_command_for_role(
            provider_id=provider_id,
            prompt=None,  # Prompt provided later in run_agent
            model=role_cfg.model,
            timeout_sec=timeout_sec,
            custom_params=role_cfg.cli_parameters or {}
        )

        # Apply timeout multiplier and determine stdin mode
        adjusted_timeout = int(timeout_sec * multiplier)
        provider = cli_adapter.get_provider(provider_id)
        stdin_mode = stdin_content is not None or provider.input_mode != "flag"

        client = CLIClient(cmd, timeout_sec=adjusted_timeout, stdin_mode=stdin_mode)
        return AgentExecutor(client, cfg.agent_output, cfg.messages)

    @staticmethod
    def _review_has_critical(feedback_cfg: Dict[str, object], reviewer_output: str) -> bool:
        if not feedback_cfg.get("enabled", False):
            return False
        patterns = [str(pat) for pat in feedback_cfg.get("critical_patterns", [])]
        lowered = reviewer_output.lower()
        return any(pat.lower() in lowered for pat in patterns)

    @staticmethod
    async def _mark_role_skipped(role_cfg: RoleConfig, task_board: TaskBoard, coordination_log: CoordinationLog) -> None:
        for instance_id in range(1, role_cfg.instances + 1):
            instance_label = f"{role_cfg.id}#{instance_id}"
            await task_board.update_task(
                instance_label,
                {"status": "skipped", "claimed_by": ""},
            )
            coordination_log.append(
                instance_label,
                "skip",
                {"task": instance_label},
            )

    @staticmethod
    def _effective_deps(cfg: AppConfig, role_cfg: RoleConfig) -> List[str]:
        if role_cfg.depends_on:
            return role_cfg.depends_on
        deps = []
        for role in cfg.roles:
            if role.id == role_cfg.id:
                break
            deps.append(role.id)
        return deps

    @staticmethod
    def _confirm_diff(label: str, diff_text: str) -> bool:
        print(f"\n--- Diff Preview ({label}) ---\n{diff_text}\n")
        answer = input("Apply this diff? [y/N]: ").strip().lower()
        return answer == "y"

    @staticmethod
    def _build_json_logger(cfg: AppConfig, workdir: Path, run_id: str, run_dir: Path) -> JsonRunLogger:
        logging_cfg = cfg.logging or {}
        enabled = bool(logging_cfg.get("jsonl_enabled", False))
        raw_path = str(logging_cfg.get("jsonl_path") or "").replace("<run_id>", run_id)
        if raw_path:
            path = Path(raw_path)
            if not path.is_absolute():
                path = workdir / path
        else:
            path = run_dir / "events.jsonl"
        return JsonRunLogger(path, enabled=enabled)

    @staticmethod
    async def _validate_shard_results(
        role_cfg: RoleConfig,
        shard_plan: ShardPlan,
        role_results: List[AgentResult],
        run_dir: Path,
        json_logger: JsonRunLogger,
    ) -> tuple[bool, str]:
        """
        Validate shard results for overlaps and allowed paths violations.

        Returns:
            Tuple of (is_valid, error_message)
        """
        from .diff_applier import UnifiedDiffApplier

        diff_applier = UnifiedDiffApplier()
        instance_diffs: dict[str, set[str]] = {}

        # Extract touched files from each instance's diff
        for i, result in enumerate(role_results, start=1):
            instance_label = f"{role_cfg.id}#{i}"
            diff_text = diff_applier.extract_diff(result.stdout)

            if not diff_text:
                instance_diffs[instance_label] = set()
                continue

            touched_files = extract_touched_files_from_unified_diff(diff_text)
            instance_diffs[instance_label] = touched_files

            # Validate against allowed paths if enforced
            shard_index = i - 1
            if shard_plan.enforce_allowed_paths and shard_index < len(shard_plan.shards):
                shard = shard_plan.shards[shard_index]
                is_valid, violations = validate_touched_files_against_allowed_paths(
                    touched_files,
                    shard.allowed_paths,
                )
                if not is_valid:
                    violation_list = ", ".join(violations)
                    json_logger.log("shard_validation_error", {
                        "role": role_cfg.id,
                        "instance": instance_label,
                        "shard_id": shard.id,
                        "error": "allowed_paths_violation",
                        "violations": violations,
                    })
                    return False, f"{instance_label} violated allowed_paths: {violation_list}"

        # Detect overlaps
        overlaps = detect_file_overlaps(instance_diffs)

        if overlaps:
            overlap_report = {
                "role": role_cfg.id,
                "overlap_count": len(overlaps),
                "overlapping_files": {
                    filepath: instances
                    for filepath, instances in overlaps.items()
                },
            }
            json_logger.log("shard_overlaps_detected", overlap_report)

            # Save overlap report
            overlap_path = run_dir / f"{role_cfg.id}_overlaps.json"
            overlap_path.write_text(
                json.dumps(overlap_report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            overlap_summary = "; ".join([f"{f} ({', '.join(insts)})" for f, insts in list(overlaps.items())[:3]])
            if len(overlaps) > 3:
                overlap_summary += f" ... (+{len(overlaps) - 3} more)"

            return False, f"Overlaps detected: {overlap_summary}"

        # Save successful validation summary
        summary = {
            "role": role_cfg.id,
            "shard_count": shard_plan.shard_count,
            "instances": {
                instance_label: list(touched)
                for instance_label, touched in instance_diffs.items()
            },
            "overlaps": {},
            "validation": "passed",
        }
        summary_path = run_dir / f"{role_cfg.id}_shard_summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        json_logger.log("shard_validation_success", {
            "role": role_cfg.id,
            "shard_count": shard_plan.shard_count,
        })

        return True, ""


def build_pipeline() -> Pipeline:
    return Pipeline(
        snapshotter=WorkspaceSnapshotter(),
        diff_applier=UnifiedDiffApplier(),
    )
