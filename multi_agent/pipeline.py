from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .codex import AgentExecutor, CodexClient
from .diff_applier import BaseDiffApplier, UnifiedDiffApplier
from .models import AgentResult, AgentSpec, AppConfig
from .snapshot import BaseSnapshotter, WorkspaceSnapshotter
from .progress import ProgressReporter
from .utils import format_prompt, get_codex_cmd, now_stamp, summarize_text, write_text


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

        run_dir = workdir / str(cfg.paths["run_dir"]) / now_stamp()
        run_dir.mkdir(parents=True, exist_ok=True)

        task = (args.task or "").strip()
        if not task:
            print(cfg.messages["error_task_empty"], file=sys.stderr)
            return 2

        apply_roles = [role for role in cfg.roles if role.apply_diff]
        total_steps = 1 + len(cfg.roles) + (len(apply_roles) if args.apply else 0) + 1
        reporter = ProgressReporter(total_steps=total_steps)
        reporter.start(f"Workspace: {workdir} | Run-Ordner: {run_dir}")

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
        executor = AgentExecutor(client, cfg.agent_output)

        context: Dict[str, str] = {
            "task": task,
            "snapshot": snapshot,
        }
        results: Dict[str, AgentResult] = {}

        for role_cfg in cfg.roles:
            agent = AgentSpec(role_cfg.name, role_cfg.role)
            reporter.step("Prompt-Build", f"Rolle: {role_cfg.id}", advance=0)
            try:
                prompt_body = format_prompt(role_cfg.prompt_template, context, role_cfg.id, cfg.messages)
            except ValueError as exc:
                reporter.error(str(exc))
                print(str(exc), file=sys.stderr)
                return 2
            prompt = cfg.system_rules + "\n\n" + prompt_body
            reporter.step("Prompt-Build", f"Rolle: {role_cfg.id}, chars={len(prompt)}", advance=0)
            out_file = run_dir / f"{role_cfg.id}.md"
            reporter.step("Agent-Lauf", f"Rolle: {role_cfg.id}", advance=1)
            res = await executor.run_agent(
                agent,
                prompt,
                workdir,
                out_file,
            )
            reporter.step("Agent-Ende", f"Rolle: {role_cfg.id}, rc={res.returncode}", advance=0)
            results[role_cfg.id] = res
            context[f"{role_cfg.id}_summary"] = summarize_text(res.stdout, max_chars=cfg.summary_max_chars)
            context[f"{role_cfg.id}_output"] = res.stdout

        # Optional: apply diffs
        apply_log_lines: List[str] = []
        if args.apply:
            for role_cfg in cfg.roles:
                if not role_cfg.apply_diff:
                    continue
                res = results.get(role_cfg.id)
                if not res:
                    continue
                reporter.step("Diff-Apply", f"Rolle: {role_cfg.id}", advance=1)
                diff = self._diff_applier.extract_diff(res.stdout)
                if not diff:
                    reporter.step("Diff-Apply", f"Rolle: {role_cfg.id}, kein diff", advance=0)
                    apply_log_lines.append(cfg.messages["apply_no_diff"].format(label=role_cfg.id))
                    continue
                ok, msg = self._diff_applier.apply(workdir, diff, cfg.diff_messages)
                if ok:
                    reporter.step("Diff-Apply", f"Rolle: {role_cfg.id}, ok", advance=0)
                    apply_log_lines.append(cfg.messages["apply_ok"].format(label=role_cfg.id, message=msg))
                else:
                    reporter.step("Diff-Apply", f"Rolle: {role_cfg.id}, fehler", advance=0)
                    apply_log_lines.append(cfg.messages["apply_error"].format(label=role_cfg.id, message=msg))
                    if args.fail_fast:
                        reporter.error(f"Diff-Apply abgebrochen: {role_cfg.id}")
                        break
            write_text(run_dir / str(cfg.paths["apply_log_filename"]), "\n".join(apply_log_lines) + "\n")

        reporter.step("Summary", "Ausgaben werden zusammengefasst", advance=1)
        # Console Summary
        print("\n" + cfg.messages["run_complete"])
        print(cfg.messages["workspace_label"].format(workspace=workdir))
        print(cfg.messages["run_dir_label"].format(run_dir=run_dir))
        print("\n" + cfg.messages["status_header"])
        for role_cfg in cfg.roles:
            res = results.get(role_cfg.id)
            if not res:
                continue
            line = cfg.messages["status_line"].format(
                agent_name=res.agent.name,
                rc=res.returncode,
                ok=res.ok,
                out_file=res.out_file.name,
            )
            print(line)

        if args.apply:
            print("\n" + cfg.messages["patch_apply_header"])
            for line in apply_log_lines:
                print("-", line)

        final_role_id = cfg.final_role_id or (cfg.roles[-1].id if cfg.roles else "")
        final_res = results.get(final_role_id)
        if final_res:
            print("\n" + cfg.messages["integrator_output_header"] + "\n")
            print(summarize_text(final_res.stdout, max_chars=cfg.final_summary_max_chars))
            print("")

        if args.ignore_fail:
            reporter.finish("Status ignoriert (ignore-fail)")
            return 0

        any_fail = any(not res.ok for res in results.values())
        reporter.finish("Fertig")
        return 1 if any_fail else 0


def build_pipeline() -> Pipeline:
    return Pipeline(
        snapshotter=WorkspaceSnapshotter(),
        diff_applier=UnifiedDiffApplier(),
    )
