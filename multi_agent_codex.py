#!/usr/bin/env python3
"""
multi_agent_codex.py — Multi-Agent Orchestrator for Codex CLI

Dieses Skript orchestriert mehrere "Agenten" (separate Codex-CLI Aufrufe), die
gemeinsam eine Software-Aufgabe bearbeiten:

1) Architect    -> Architektur & Plan
2) Implementer  -> Implementierung (liefert Unified Diff)
3) Tester       -> Tests (liefert Unified Diff)
4) Reviewer     -> Review + optionale Fixes (Unified Diff)
5) Integrator   -> Zusammenführung + finale Schritte (optional Unified Diff)

Optional kann das Skript die von Agenten gelieferten Unified-Diffs auf das
Arbeitsverzeichnis anwenden (--apply). Das Patch-Apply ist bewusst konservativ
und bricht bei Context-Mismatches ab.

Voraussetzungen:
- Python 3.10+
- Codex CLI im PATH (Befehl: `codex`) oder via ENV `CODEX_CMD="codex ..."`

Beispiele:
  python multi_agent_codex.py --task "Baue ein FastAPI CRUD für Todos" --dir . --apply
  CODEX_CMD="codex --model gpt-5-codex" python multi_agent_codex.py --task "Refactor Modul X" --apply

Hinweise:
- Das Skript macht KEINE Hintergrundarbeit; alles läuft im Vordergrund.
- Für robuste Patch-Anwendung kannst du alternativ `git apply` nutzen, aber dieses
  Skript hat einen eingebauten "good-enough" Applier für viele Fälle.
"""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Defaults
# -----------------------------

DEFAULT_TIMEOUT_SEC = 20 * 60  # 20 Minuten pro Agent
DEFAULT_MAX_FILES = 350        # Snapshot: max Dateien
DEFAULT_MAX_FILE_BYTES = 90_000  # Snapshot: max bytes pro Datei
DEFAULT_CONCURRENCY = 2        # Parallelität (optional)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "main.json"


@dataclasses.dataclass(frozen=True)
class RoleConfig:
    id: str
    name: str
    role: str
    prompt_template: str
    apply_diff: bool


@dataclasses.dataclass(frozen=True)
class AppConfig:
    system_rules: str
    roles: List[RoleConfig]
    final_role_id: str
    summary_max_chars: int
    final_summary_max_chars: int
    codex_env_var: str
    codex_default_cmd: str
    paths: Dict[str, str]
    snapshot: Dict[str, object]
    agent_output: Dict[str, str]
    messages: Dict[str, str]
    diff_messages: Dict[str, str]
    cli: Dict[str, object]


# -----------------------------
# Helpers
# -----------------------------

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_safe(path: Path, limit_bytes: int) -> str:
    if not path.exists() or not path.is_file():
        return ""
    data = path.read_bytes()
    if len(data) > limit_bytes:
        data = data[:limit_bytes]
    return data.decode("utf-8", errors="replace")


def get_codex_cmd(env_var: str, default_cmd: str) -> List[str]:
    """
    Erlaubt Overrides via ENV:
      CODEX_CMD="codex --model xyz"
    """
    raw = os.environ.get(env_var, default_cmd)
    return shlex.split(raw)


def summarize_text(text: str, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2].rstrip()
    tail = text[- max_chars // 2 :].lstrip()
    return head + "\n...\n" + tail


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_role_config(role_entry: Dict[str, object], base_dir: Path) -> RoleConfig:
    role_path = base_dir / str(role_entry["file"])
    data = load_json(role_path)
    role_id = str(role_entry.get("id") or data.get("id") or "")
    if not role_id:
        raise ValueError(f"Role file missing id: {role_path}")
    return RoleConfig(
        id=role_id,
        name=str(data.get("name") or role_id),
        role=str(data["role"]),
        prompt_template=str(data["prompt_template"]),
        apply_diff=bool(role_entry.get("apply_diff", False)),
    )


def load_app_config(config_path: Path) -> AppConfig:
    data = load_json(config_path)
    base_dir = config_path.parent
    roles = [load_role_config(role_entry, base_dir) for role_entry in data["roles"]]
    final_role_id = str(data.get("final_role_id") or (roles[-1].id if roles else ""))
    return AppConfig(
        system_rules=str(data["system_rules"]),
        roles=roles,
        final_role_id=final_role_id,
        summary_max_chars=int(data.get("summary_max_chars", 1400)),
        final_summary_max_chars=int(data.get("final_summary_max_chars", 2400)),
        codex_env_var=str(data["codex"]["env_var"]),
        codex_default_cmd=str(data["codex"]["default_cmd"]),
        paths=data["paths"],
        snapshot=data["snapshot"],
        agent_output=data["agent_output"],
        messages=data["messages"],
        diff_messages=data["diff_messages"],
        cli=data["cli"],
    )


def format_prompt(template: str, context: Dict[str, str], role_id: str, messages: Dict[str, str]) -> str:
    try:
        return template.format(**context)
    except KeyError as exc:
        key = exc.args[0] if exc.args else "unknown"
        raise ValueError(messages["error_prompt_missing_key"].format(role_id=role_id, key=key)) from exc


def list_workspace_snapshot(
    root: Path,
    snapshot_cfg: Dict[str, object],
    max_files: int = DEFAULT_MAX_FILES,
    max_bytes_per_file: int = DEFAULT_MAX_FILE_BYTES,
) -> str:
    """
    Snapshot des Workspaces:
    - Liste der Dateien
    - Inhalte von Textdateien (gekürzt)
    """
    root = root.resolve()
    files: List[Path] = []
    skip_dirs = set(snapshot_cfg.get("skip_dirs", []))
    skip_exts = set(snapshot_cfg.get("skip_exts", []))

    for p in root.rglob("*"):
        if p.is_dir():
            continue
        parts = set(p.parts)
        if parts & skip_dirs:
            continue
        files.append(p)

    files = sorted(files)[:max_files]

    lines: List[str] = []
    lines.append(str(snapshot_cfg["workspace_header"]).format(root=root))
    lines.append("")
    lines.append(str(snapshot_cfg["files_header"]))
    for p in files:
        rel = p.relative_to(root)
        try:
            size = p.stat().st_size
        except OSError:
            size = -1
        lines.append(str(snapshot_cfg["file_line"]).format(rel=rel, size=size))

    lines.append("")
    lines.append(str(snapshot_cfg["content_header"]))
    for p in files:
        if p.suffix.lower() in skip_exts:
            continue
        rel = p.relative_to(root)
        content = read_text_safe(p, limit_bytes=max_bytes_per_file)
        if not content.strip():
            continue
        header = str(snapshot_cfg["file_section_header"]).format(rel=rel)
        lines.append(f"\n{header}\n")
        lines.append(content)
    return "\n".join(lines)


# -----------------------------
# Diff / Patch apply (conservative)
# -----------------------------

DIFF_GIT_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*$", re.MULTILINE)


def extract_diff(text: str) -> str:
    """
    Extrahiert ab erstem 'diff --git ...' bis Ende.
    """
    m = DIFF_GIT_HEADER_RE.search(text or "")
    if not m:
        return ""
    return (text or "")[m.start():].strip()


def split_diff_by_file(diff_text: str, diff_messages: Dict[str, str]) -> List[Tuple[str, str]]:
    matches = list(DIFF_GIT_HEADER_RE.finditer(diff_text))
    if not matches:
        raise ValueError(str(diff_messages["no_git_header"]))
    blocks: List[Tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(diff_text)
        block = diff_text[start:end].strip("\n")
        b_path = m.group(2)
        blocks.append((b_path, block))
    return blocks


def apply_unified_diff(workdir: Path, diff_text: str, diff_messages: Dict[str, str]) -> Tuple[bool, str]:
    """
    Sehr konservativer Unified-Diff Applier:
    - Erwartet git-style: diff --git a/... b/...
    - Erwartet, dass Kontextzeilen passen
    - Unterstützt Datei-Neuanlage, Änderungen, Löschungen (eingeschränkt)
    """
    try:
        blocks = split_diff_by_file(diff_text, diff_messages)
        for rel_path, file_block in blocks:
            ok, msg = apply_file_block(workdir, rel_path, file_block, diff_messages)
            if not ok:
                return False, msg
        return True, str(diff_messages["patch_applied"])
    except Exception as e:
        return False, str(diff_messages["patch_exception"]).format(error=e)


def _parse_old_new_paths(file_block: str) -> Tuple[str, str]:
    # sucht --- a/... und +++ b/...
    old = ""
    new = ""
    for line in file_block.splitlines():
        if line.startswith("--- "):
            old = line[4:].strip()
        elif line.startswith("+++ "):
            new = line[4:].strip()
        if old and new:
            break
    return old, new


def apply_file_block(
    workdir: Path,
    rel_path: str,
    file_block: str,
    diff_messages: Dict[str, str],
) -> Tuple[bool, str]:
    target = workdir / rel_path

    old_marker, new_marker = _parse_old_new_paths(file_block)
    # /dev/null handling
    is_new_file = old_marker.endswith("/dev/null")
    is_deleted = new_marker.endswith("/dev/null")

    original_lines: List[str]
    if target.exists() and target.is_file():
        original_lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        original_lines = []

    out = original_lines[:]

    hunks = list(HUNK_RE.finditer(file_block))
    if not hunks:
        # Kein Hunk: akzeptieren
        if is_deleted and target.exists():
            try:
                target.unlink()
            except OSError as e:
                return False, str(diff_messages["delete_file_error"]).format(rel_path=rel_path, error=e)
        return True, str(diff_messages["no_hunks"]).format(rel_path=rel_path)

    # spans für hunk content
    spans: List[Tuple[int, int]] = []
    for i, hm in enumerate(hunks):
        start = hm.end()
        end = hunks[i + 1].start() if i + 1 < len(hunks) else len(file_block)
        spans.append((start, end))

    line_offset = 0

    for hm, (hs, he) in zip(hunks, spans):
        new_start = int(hm.group(3))
        hunk_lines = file_block[hs:he].splitlines()

        pos = (new_start - 1) + line_offset
        check_pos = pos
        consumed_old = 0
        new_block: List[str] = []

        for hl in hunk_lines:
            if not hl:
                prefix, text = " ", ""
            else:
                prefix, text = hl[0], hl[1:] if len(hl) > 1 else ""

            if prefix == " ":
                if check_pos >= len(out) or out[check_pos] != text:
                    got = out[check_pos] if check_pos < len(out) else "EOF"
                    return False, str(diff_messages["context_mismatch"]).format(
                        rel_path=rel_path,
                        line=check_pos + 1,
                        expected=text,
                        got=got,
                    )
                new_block.append(text)
                check_pos += 1
                consumed_old += 1
            elif prefix == "-":
                if check_pos >= len(out) or out[check_pos] != text:
                    got = out[check_pos] if check_pos < len(out) else "EOF"
                    return False, str(diff_messages["delete_mismatch"]).format(
                        rel_path=rel_path,
                        line=check_pos + 1,
                        expected=text,
                        got=got,
                    )
                check_pos += 1
                consumed_old += 1
            elif prefix == "+":
                new_block.append(text)
            elif prefix == "\\":
                # "\ No newline at end of file"
                continue
            else:
                return False, str(diff_messages["unknown_prefix"]).format(rel_path=rel_path, prefix=prefix)

        out[pos:pos + consumed_old] = new_block
        line_offset += (len(new_block) - consumed_old)

    # Apply results
    if is_deleted:
        # wenn Diff eine Löschung signalisiert, löschen wir (wenn existiert)
        if target.exists():
            try:
                target.unlink()
            except OSError as e:
                return False, str(diff_messages["delete_file_error"]).format(rel_path=rel_path, error=e)
        return True, str(diff_messages["file_deleted"]).format(rel_path=rel_path)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
        if is_new_file:
            return True, str(diff_messages["file_created"]).format(rel_path=rel_path)
        return True, str(diff_messages["file_updated"]).format(rel_path=rel_path)


@dataclasses.dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str


@dataclasses.dataclass
class AgentResult:
    agent: AgentSpec
    returncode: int
    stdout: str
    stderr: str
    out_file: Path

    @property
    def ok(self) -> bool:
        return self.returncode == 0


async def run_codex(
    prompt: str,
    workdir: Path,
    timeout_sec: int,
    codex_cmd: List[str],
) -> Tuple[int, str, str]:
    cmd = codex_cmd
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workdir),
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(prompt.encode("utf-8")),
            timeout=timeout_sec,
        )
        rc = proc.returncode or 0
        return rc, stdout_b.decode("utf-8", "replace"), stderr_b.decode("utf-8", "replace")
    except asyncio.TimeoutError:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        stdout_b, stderr_b = await proc.communicate()
        return 124, stdout_b.decode("utf-8", "replace"), (stderr_b.decode("utf-8", "replace") + "\nTIMEOUT")


async def run_agent(
    agent: AgentSpec,
    prompt: str,
    workdir: Path,
    out_file: Path,
    timeout_sec: int,
    codex_cmd: List[str],
    agent_output_cfg: Dict[str, str],
) -> AgentResult:
    rc, out, err = await run_codex(prompt, workdir=workdir, timeout_sec=timeout_sec, codex_cmd=codex_cmd)
    content = (
        f"{agent_output_cfg['agent_header'].format(name=agent.name, role=agent.role)}\n\n"
        f"{agent_output_cfg['returncode_header']}\n{rc}\n\n"
        f"{agent_output_cfg['stdout_header']}\n{out}\n\n"
        f"{agent_output_cfg['stderr_header']}\n{err}\n"
    )
    write_text(out_file, content)
    return AgentResult(agent=agent, returncode=rc, stdout=out, stderr=err, out_file=out_file)


# -----------------------------
# Main pipeline
# -----------------------------

async def pipeline(args: argparse.Namespace, cfg: AppConfig) -> int:
    workdir = Path(args.dir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    run_dir = workdir / str(cfg.paths["run_dir"]) / now_stamp()
    run_dir.mkdir(parents=True, exist_ok=True)

    task = (args.task or "").strip()
    if not task:
        print(cfg.messages["error_task_empty"], file=sys.stderr)
        return 2

    snapshot = list_workspace_snapshot(
        workdir,
        cfg.snapshot,
        max_files=args.max_files,
        max_bytes_per_file=args.max_file_bytes,
    )
    write_text(run_dir / str(cfg.paths["snapshot_filename"]), snapshot)

    codex_cmd = get_codex_cmd(cfg.codex_env_var, cfg.codex_default_cmd)

    context: Dict[str, str] = {
        "task": task,
        "snapshot": snapshot,
    }
    results: Dict[str, AgentResult] = {}

    for role_cfg in cfg.roles:
        agent = AgentSpec(role_cfg.name, role_cfg.role)
        try:
            prompt_body = format_prompt(role_cfg.prompt_template, context, role_cfg.id, cfg.messages)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        prompt = cfg.system_rules + "\n\n" + prompt_body
        out_file = run_dir / f"{role_cfg.id}.md"
        res = await run_agent(
            agent,
            prompt,
            workdir,
            out_file,
            args.timeout,
            codex_cmd,
            cfg.agent_output,
        )
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
            diff = extract_diff(res.stdout)
            if not diff:
                apply_log_lines.append(cfg.messages["apply_no_diff"].format(label=role_cfg.id))
                continue
            ok, msg = apply_unified_diff(workdir, diff, cfg.diff_messages)
            if ok:
                apply_log_lines.append(cfg.messages["apply_ok"].format(label=role_cfg.id, message=msg))
            else:
                apply_log_lines.append(cfg.messages["apply_error"].format(label=role_cfg.id, message=msg))
                if args.fail_fast:
                    break
        write_text(run_dir / str(cfg.paths["apply_log_filename"]), "\n".join(apply_log_lines) + "\n")

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
        return 0

    any_fail = any(not res.ok for res in results.values())
    return 1 if any_fail else 0


def parse_args(cfg: AppConfig, argv: Optional[List[str]] = None) -> argparse.Namespace:
    cli = cfg.cli
    args_cfg = cli["args"]
    p = argparse.ArgumentParser(description=str(cli["description"]))
    p.add_argument("--task", required=True, help=str(args_cfg["task"]["help"]))
    p.add_argument("--dir", default=".", help=str(args_cfg["dir"]["help"]))
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SEC, help=str(args_cfg["timeout"]["help"]))
    p.add_argument("--apply", action="store_true", help=str(args_cfg["apply"]["help"]))
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
    try:
        rc = asyncio.run(pipeline(args, cfg))
    except KeyboardInterrupt:
        print(f"\n{cfg.messages['interrupted']}", file=sys.stderr)
        rc = 130
    except FileNotFoundError as e:
        print(f"\n{cfg.messages['codex_not_found'].format(error=e)}", file=sys.stderr)
        print(cfg.messages["codex_tip"], file=sys.stderr)
        rc = 127
    sys.exit(rc)


if __name__ == "__main__":
    main()