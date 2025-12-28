from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .codex import AgentExecutor, CodexClient
from .coordination import CoordinationConfig, CoordinationLog, TaskBoard
from .diff_applier import BaseDiffApplier, UnifiedDiffApplier
from .models import AgentResult, AgentSpec, AppConfig
from .snapshot import BaseSnapshotter, WorkspaceSnapshotter
from .progress import ProgressReporter
from .utils import format_prompt, get_codex_cmd, get_status_text, now_stamp, summarize_text, write_text


class Pipeline:
    def __init__(
        self,
        snapshotter: BaseSnapshotter,
        diff_applier: BaseDiffApplier,
    ) -> None:
        self._snapshotter = snapshotter
        self._diff_applier = diff_applier

    async def run(self, args: argparse.Namespace, cfg: AppConfig) -> int:
        workdir = Path(args.dir).resolve()
        workdir.mkdir(parents=True, exist_ok=True)

        run_id = now_stamp()
        run_dir = workdir / str(cfg.paths["run_dir"]) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        task = (args.task or "").strip()
        if not task:
            print(cfg.messages["error_task_empty"], file=sys.stderr)
            return 2

        apply_roles = [role for role in cfg.roles if role.apply_diff]
        try:
            apply_role_ids = self._resolve_apply_role_ids(args, cfg)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        total_agents = sum(role.instances for role in cfg.roles)
        apply_instances = sum(role.instances for role in apply_roles if role.id in apply_role_ids)
        total_steps = 1 + total_agents + (apply_instances if args.apply else 0) + 1
        reporter = ProgressReporter(total_steps=total_steps)
        reporter.start(f"Workspace: {workdir} | Run-Ordner: {run_dir}")
        report_lock = asyncio.Lock()

        reporter.step("Snapshot", "Workspace wird gescannt", advance=1)
        snapshot = self._snapshotter.build_snapshot(
            workdir,
            cfg.snapshot,
            max_files=args.max_files,
            max_bytes_per_file=args.max_file_bytes,
        )
        write_text(run_dir / str(cfg.paths["snapshot_filename"]), snapshot)
        reporter.step("Snapshot", "Snapshot gespeichert", advance=0)

        codex_cmd = get_codex_cmd(cfg.codex_env_var, cfg.codex_default_cmd)
        client = CodexClient(codex_cmd, timeout_sec=args.timeout)
        executor = AgentExecutor(client, cfg.agent_output, cfg.messages)

        coordination_cfg = self._build_coordination_config(cfg.coordination)
        task_board_path = self._resolve_coordination_path(
            workdir, run_dir, coordination_cfg.task_board, run_id, default_name="task_board.json"
        )
        coordination_log_path = self._resolve_coordination_path(
            workdir, run_dir, coordination_cfg.channel, run_id, default_name="coordination.log"
        )
        task_board = TaskBoard(
            task_board_path,
            lock_mode=coordination_cfg.lock_mode,
            lock_timeout_sec=coordination_cfg.lock_timeout_sec,
        )
        coordination_log = CoordinationLog(coordination_log_path)

        context: Dict[str, str] = {
            "task": task,
            "snapshot": snapshot,
            "task_board_path": str(task_board_path),
            "coordination_log_path": str(coordination_log_path),
        }
        results: Dict[str, List[AgentResult]] = {}

        await task_board.initialize(self._build_task_board(cfg))
        coordination_log.append("orchestrator", "init", {"run_id": run_id})

        apply_log_lines: List[str] = []
        abort_run = False
        for role_cfg in cfg.roles:
            if abort_run:
                break
            role_results: List[AgentResult] = []
            validation_context = dict(context)
            validation_context["role_id"] = role_cfg.id
            validation_context["role_name"] = role_cfg.name
            validation_context["role_instance_id"] = "1"
            validation_context["role_instance"] = f"{role_cfg.id}#1"
            try:
                _ = format_prompt(role_cfg.prompt_template, validation_context, role_cfg.id, cfg.messages)
            except ValueError as exc:
                reporter.error(str(exc))
                print(str(exc), file=sys.stderr)
                return 2

            async def run_instance(instance_id: int) -> AgentResult:
                instance_label = f"{role_cfg.id}#{instance_id}"
                agent = AgentSpec(f"{role_cfg.name}#{instance_id}", role_cfg.role)
                local_context = dict(context)
                local_context["role_id"] = role_cfg.id
                local_context["role_name"] = role_cfg.name
                local_context["role_instance_id"] = str(instance_id)
                local_context["role_instance"] = instance_label
                async with report_lock:
                    reporter.step("Prompt-Build", f"Rolle: {instance_label}", advance=0)
                prompt_body = format_prompt(role_cfg.prompt_template, local_context, role_cfg.id, cfg.messages)
                prompt = cfg.system_rules + "\n\n" + prompt_body
                async with report_lock:
                    reporter.step("Prompt-Build", f"Rolle: {instance_label}, chars={len(prompt)}", advance=0)
                out_file = run_dir / self._build_output_filename(cfg, role_cfg, instance_id)
                await task_board.update_task(
                    instance_label,
                    {"status": "in_progress", "claimed_by": instance_label},
                )
                coordination_log.append(
                    instance_label,
                    "claim",
                    {"task": instance_label, "out_file": str(out_file)},
                )
                async with report_lock:
                    reporter.step("Agent-Lauf", f"Rolle: {instance_label}", advance=1)
                res = await executor.run_agent(
                    agent,
                    prompt,
                    workdir,
                    out_file,
                )
                await task_board.update_task(
                    instance_label,
                    {"status": "done", "claimed_by": instance_label, "returncode": res.returncode},
                )
                coordination_log.append(
                    instance_label,
                    "complete",
                    {"task": instance_label, "returncode": res.returncode},
                )
                async with report_lock:
                    reporter.step("Agent-Ende", f"Rolle: {instance_label}, rc={res.returncode}", advance=0)
                return res

            tasks = [asyncio.create_task(run_instance(idx)) for idx in range(1, role_cfg.instances + 1)]
            role_results = await asyncio.gather(*tasks)
            results[role_cfg.id] = role_results
            context[f"{role_cfg.id}_summary"] = self._combine_outputs(
                role_cfg.id,
                role_results,
                lambda text: summarize_text(text, max_chars=cfg.summary_max_chars),
            )
            context[f"{role_cfg.id}_output"] = self._combine_outputs(role_cfg.id, role_results, lambda text: text)

            if args.apply and args.apply_mode == "role" and role_cfg.apply_diff and role_cfg.id in apply_role_ids:
                applied_ok, had_error = await self._apply_role_diffs(
                    args,
                    cfg,
                    workdir,
                    role_cfg,
                    role_results,
                    reporter,
                    apply_log_lines,
                )
                if applied_ok:
                    snapshot = self._snapshotter.build_snapshot(
                        workdir,
                        cfg.snapshot,
                        max_files=args.max_files,
                        max_bytes_per_file=args.max_file_bytes,
                    )
                    snapshot_name = f"snapshot_after_{role_cfg.id}.txt"
                    write_text(run_dir / snapshot_name, snapshot)
                    context["snapshot"] = snapshot
                if args.fail_fast and had_error:
                    abort_run = True

        # Optional: apply diffs at end
        if args.apply and args.apply_mode == "end":
            for role_cfg in cfg.roles:
                if not role_cfg.apply_diff or role_cfg.id not in apply_role_ids:
                    continue
                role_results = results.get(role_cfg.id, [])
                if not role_results:
                    continue
                for res in role_results:
                    label = res.agent.name
                    reporter.step("Diff-Apply", f"Rolle: {label}", advance=1)
                    diff = self._diff_applier.extract_diff(res.stdout)
                    if not diff:
                        reporter.step("Diff-Apply", f"Rolle: {label}, kein diff", advance=0)
                        apply_log_lines.append(cfg.messages["apply_no_diff"].format(label=label))
                        continue
                    ok, msg = self._diff_applier.apply(workdir, diff, cfg.diff_messages)
                    if ok:
                        reporter.step("Diff-Apply", f"Rolle: {label}, ok", advance=0)
                        apply_log_lines.append(cfg.messages["apply_ok"].format(label=label, message=msg))
                    else:
                        reporter.step("Diff-Apply", f"Rolle: {label}, fehler", advance=0)
                        apply_log_lines.append(cfg.messages["apply_error"].format(label=label, message=msg))
                        if args.fail_fast:
                            reporter.error(f"Diff-Apply abgebrochen: {label}")
                            break
            write_text(run_dir / str(cfg.paths["apply_log_filename"]), "\n".join(apply_log_lines) + "\n")
        elif args.apply and apply_log_lines:
            write_text(run_dir / str(cfg.paths["apply_log_filename"]), "\n".join(apply_log_lines) + "\n")

        reporter.step("Summary", "Ausgaben werden zusammengefasst", advance=1)
        # Console Summary
        print("\n" + cfg.messages["run_complete"])
        print(cfg.messages["workspace_label"].format(workspace=workdir))
        print(cfg.messages["run_dir_label"].format(run_dir=run_dir))
        print("\n" + cfg.messages["status_header"])
        for role_cfg in cfg.roles:
            role_results = results.get(role_cfg.id, [])
            if not role_results:
                continue
            for res in role_results:
                line = cfg.messages["status_line"].format(
                    agent_name=res.agent.name,
                    rc=res.returncode,
                    status=get_status_text(res.returncode, res.stdout, cfg.messages),
                    ok=res.ok,
                    out_file=res.out_file.name,
                )
                print(line)

        if args.apply:
            print("\n" + cfg.messages["patch_apply_header"])
            for line in apply_log_lines:
                print("-", line)

        final_role_id = cfg.final_role_id or (cfg.roles[-1].id if cfg.roles else "")
        final_results = results.get(final_role_id, [])
        if final_results:
            print("\n" + cfg.messages["integrator_output_header"] + "\n")
            final_output = self._combine_outputs(final_role_id, final_results, lambda text: text)
            print(summarize_text(final_output, max_chars=cfg.final_summary_max_chars))
            print("")

        if args.ignore_fail:
            reporter.finish("Status ignoriert (ignore-fail)")
            return 0

        any_fail = any(not res.ok for res_list in results.values() for res in res_list)
        reporter.finish("Fertig")
        return 1 if any_fail else 0

    @staticmethod
    def _combine_outputs(
        role_id: str,
        results: List[AgentResult],
        transform,
    ) -> str:
        blocks: List[str] = []
        for res in results:
            content = (transform(res.stdout) or "").strip()
            if not content:
                continue
            blocks.append(f"[{res.agent.name}]\n{content}")
        return "\n\n".join(blocks).strip()

    @staticmethod
    def _build_coordination_config(raw: Dict[str, object]) -> CoordinationConfig:
        return CoordinationConfig(
            task_board=str(raw.get("task_board") or ""),
            channel=str(raw.get("channel") or ""),
            lock_mode=str(raw.get("lock_mode") or "file_lock"),
            claim_timeout_sec=int(raw.get("claim_timeout_sec", 300)),
            lock_timeout_sec=int(raw.get("lock_timeout_sec", 10)),
        )

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
        raw_pattern = str((cfg.outputs or {}).get("pattern") or "").strip()
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
        prev_role_ids: List[str] = []
        for role_cfg in cfg.roles:
            role_task_ids = []
            for instance_id in range(1, role_cfg.instances + 1):
                task_id = f"{role_cfg.id}#{instance_id}"
                role_task_ids.append(task_id)
                tasks.append(
                    {
                        "id": task_id,
                        "title": f"{role_cfg.id} instance {instance_id}",
                        "status": "open",
                        "claimed_by": "",
                        "deps": list(prev_role_ids),
                    }
                )
            prev_role_ids = role_task_ids
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
    ) -> tuple[bool, bool]:
        applied_ok = False
        had_error = False
        for res in role_results:
            label = res.agent.name
            reporter.step("Diff-Apply", f"Rolle: {label}", advance=1)
            diff = self._diff_applier.extract_diff(res.stdout)
            if not diff:
                reporter.step("Diff-Apply", f"Rolle: {label}, kein diff", advance=0)
                apply_log_lines.append(cfg.messages["apply_no_diff"].format(label=label))
                continue
            ok, msg = self._diff_applier.apply(workdir, diff, cfg.diff_messages)
            if ok:
                applied_ok = True
                reporter.step("Diff-Apply", f"Rolle: {label}, ok", advance=0)
                apply_log_lines.append(cfg.messages["apply_ok"].format(label=label, message=msg))
            else:
                had_error = True
                reporter.step("Diff-Apply", f"Rolle: {label}, fehler", advance=0)
                apply_log_lines.append(cfg.messages["apply_error"].format(label=label, message=msg))
                if args.fail_fast:
                    reporter.error(f"Diff-Apply abgebrochen: {label}")
                    break
        return applied_ok, had_error


def build_pipeline() -> Pipeline:
    return Pipeline(
        snapshotter=WorkspaceSnapshotter(),
        diff_applier=UnifiedDiffApplier(),
    )
