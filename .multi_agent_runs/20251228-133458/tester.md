## AGENT: tester (Senior QA / Test Engineer)

### Returncode
0

### STDOUT
# Tests
- Teststrategie: Smoke-Tests der CLI-Pipeline (manuell), keine neuen automatisierten Tests erforderlich.
- Testfälle: `python multi_agent_codex.py --task "Smoke" --dir .`; `python multi_agent_codex.py --task "Smoke" --dir . --apply`; ungültige `config/main.json` (Syntaxfehler) prüfen; fehlender Platzhalter im Prompt provozieren.
- UNIFIED DIFF für Tests/Anpassungen:
```diff
diff --git a/README.md b/README.md
```


### STDERR
OpenAI Codex v0.77.0 (research preview)
--------
workdir: /mnt/c/Users/Christof/Projects/Python/MultiAgent
model: gpt-5.2-codex
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR]
reasoning effort: none
reasoning summaries: auto
session id: 019b64fc-66f3-7dd3-a57c-bf887da084a2
--------
user
Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgeführt wird.

Wichtige Regeln:
- Antworte strikt im geforderten FORMAT.
- Keine unnötigen Erklärungen außerhalb des Formats.
- Sei präzise, umsetzungsorientiert und konsistent.
- Wenn du Annahmen triffst, liste sie.


FORMAT:
# Tests
- Teststrategie:
- Testfälle:
- UNIFIED DIFF für Tests/Anpassungen:
```diff
diff --git a/<path> b/<path>
...
```

AUFGABE:
Überarbeite die muti_agent_codex.py mit dem Fokus auf die architektur. Erstelle dafür entsprechnede Klassen und vererbung wo sinnvoll und daraus entsprechende Klassen python files um den Code in seperate strukturierte dateinen aufzuteilen

IMPLEMENTIERUNG (Kurz):
# Implementierung
- Dateien neu/ändern (Liste): multi_agent_codex.py; multi_agent/__init__.py; multi_agent/constants.py; multi_agent/models.py; multi_agent/utils.py; multi_agent/config_loader.py; multi_agent/snapshot.py; multi_agent/diff_applier.py; multi_agent/codex.py; multi_agent/pipeline.py; multi_agent/cli.py
- Entscheidungen: Orchestrierung in `Pipeline` gekapselt; Snapshot- und Diff-Logik über Basisklassen (`BaseSnapshotter`, `BaseDiffApplier`) mit konkreten Implementierungen; Codex-Aufrufe in `CodexClient` + `AgentExecutor`; `multi_agent_codex.py` als dünner Entry-Point
- Offene Punkte: Annahme: keine externen Importe der bisherigen Funktionen aus `multi_agent_codex.py` (nur CLI-Nutz
...
onfigurationsdatei nicht gefunden: {e}", file=sys.stderr)
+        sys.exit(2)
+    except (json.JSONDecodeError, KeyError, ValueError) as e:
+        print(f"Fehler: Ungueltige Konfiguration: {e}", file=sys.stderr)
+        sys.exit(2)
+
+    args = parse_args(cfg)
+    pipeline = build_pipeline()
+    try:
+        rc = asyncio.run(pipeline.run(args, cfg))
+    except KeyboardInterrupt:
+        print(f"\n{cfg.messages['interrupted']}", file=sys.stderr)
+        rc = 130
+    except FileNotFoundError as e:
+        print(f"\n{cfg.messages['codex_not_found'].format(error=e)}", file=sys.stderr)
+        print(cfg.messages["codex_tip"], file=sys.stderr)
+        rc = 127
+    sys.exit(rc)
```

KONTEXT (Workspace Snapshot):
WORKSPACE: /mnt/c/Users/Christof/Projects/Python/MultiAgent

FILES:
  - .multi_agent_runs/20251228-124437/snapshot.txt (42202 bytes)
  - .multi_agent_runs/20251228-132824/snapshot.txt (85690 bytes)
  - .multi_agent_runs/20251228-133313/architect.md (113 bytes)
  - .multi_agent_runs/20251228-133313/implementer.md (124 bytes)
  - .multi_agent_runs/20251228-133313/integrator.md (128 bytes)
  - .multi_agent_runs/20251228-133313/reviewer.md (127 bytes)
  - .multi_agent_runs/20251228-133313/snapshot.txt (169288 bytes)
  - .multi_agent_runs/20251228-133313/tester.md (120 bytes)
  - README.md (6473 bytes)
  - config/main.json (4081 bytes)
  - config/roles/architect.json (289 bytes)
  - config/roles/implementer.json (451 bytes)
  - config/roles/integrator.json (423 bytes)
  - config/roles/reviewer.json (458 bytes)
  - config/roles/tester.json (368 bytes)
  - multi_agent_codex.py (20889 bytes)
  - multi_role_agent_creator.py (6953 bytes)

FILE CONTENT (truncated):

--- .multi_agent_runs/20251228-124437/snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config\roles\architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config\roles\reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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

--- multi_role_agent_creator.py ---

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


--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- .multi_agent_runs/20251228-132824/snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - .multi_agent_runs\20251228-124437\snapshot.txt (42202 bytes)
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- .multi_agent_runs\20251228-124437\snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config\roles\architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config\roles\reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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

--- multi_role_agent_creator.py ---

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


--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config\roles\architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config\roles\reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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

--- multi_role_agent_creator.py ---

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


--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- .multi_agent_runs/20251228-133313/architect.md ---

## AGENT: architect (Systemarchitekt)

### Returncode
1

### STDOUT


### STDERR
Error: stdin is not a terminal



--- .multi_agent_runs/20251228-133313/implementer.md ---

## AGENT: implementer (Senior Software Engineer)

### Returncode
1

### STDOUT


### STDERR
Error: stdin is not a terminal



--- .multi_agent_runs/20251228-133313/integrator.md ---

## AGENT: integrator (Integrator / Release Engineer)

### Returncode
1

### STDOUT


### STDERR
Error: stdin is not a terminal



--- .multi_agent_runs/20251228-133313/reviewer.md ---

## AGENT: reviewer (Staff Engineer (Code Reviewer))

### Returncode
1

### STDOUT


### STDERR
Error: stdin is not a terminal



--- .multi_agent_runs/20251228-133313/snapshot.txt ---

WORKSPACE: /mnt/c/Users/Christof/Projects/Python/MultiAgent

FILES:
  - .multi_agent_runs/20251228-124437/snapshot.txt (42202 bytes)
  - .multi_agent_runs/20251228-132824/snapshot.txt (85690 bytes)
  - README.md (6473 bytes)
  - config/main.json (4074 bytes)
  - config/roles/architect.json (289 bytes)
  - config/roles/implementer.json (451 bytes)
  - config/roles/integrator.json (423 bytes)
  - config/roles/reviewer.json (458 bytes)
  - config/roles/tester.json (368 bytes)
  - multi_agent_codex.py (20889 bytes)
  - multi_role_agent_creator.py (6953 bytes)

FILE CONTENT (truncated):

--- .multi_agent_runs/20251228-124437/snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config\roles\architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config\roles\reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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

--- multi_role_agent_creator.py ---

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


--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- .multi_agent_runs/20251228-132824/snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - .multi_agent_runs\20251228-124437\snapshot.txt (42202 bytes)
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- .multi_agent_runs\20251228-124437\snapshot.txt ---

WORKSPACE: C:\Users\Christof\Projects\Python\MultiAgent

FILES:
  - config\main.json (4074 bytes)
  - config\roles\architect.json (289 bytes)
  - config\roles\implementer.json (451 bytes)
  - config\roles\integrator.json (423 bytes)
  - config\roles\reviewer.json (458 bytes)
  - config\roles\tester.json (368 bytes)
  - multi_agent_codex.py (20787 bytes)
  - multi_role_agent_creator.py (6953 bytes)
  - README.md (6473 bytes)

FILE CONTENT (truncated):

--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config\roles\architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config\roles\reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config\roles\tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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

--- multi_role_agent_creator.py ---

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


--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- config\main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path

--- .multi_agent_runs/20251228-133313/tester.md ---

## AGENT: tester (Senior QA / Test Engineer)

### Returncode
1

### STDOUT


### STDERR
Error: stdin is not a terminal



--- README.md ---

# Multi-Agent Codex CLI Orchestrator

## Überblick
Dieses Projekt stellt ein vollständiges Python-basiertes Multi-Agent-System dar,
das mithilfe der **Codex CLI** mehrere spezialisierte Agenten parallel oder sequentiell
auf eine Software-Entwicklungsaufgabe ansetzt.

### Enthaltene Agenten
- **Architect** – entwirft Architektur & Plan
- **Implementer** – implementiert Features (liefert Unified Diff)
- **Tester** – erzeugt Tests
- **Reviewer** – Code-Review & Fixes
- **Integrator** – finaler Merge & Zusammenfassung

## Voraussetzungen
- Python **3.10+**
- Codex CLI im PATH
- Optional: Git (für robustes Patch-Handling)

## Installation
```bash
git clone <repo>
cd <repo>
python multi_agent_codex.py --task "Deine Aufgabe"
```

## Quickstart
Minimaler Lauf (ohne Patch-Apply):
```bash
python multi_agent_codex.py --task "Analysiere Modul X"
```
Erwartete Artefakte (pro Run):
- `config/main.json` steuert, welche Rollen laufen.
- `config/roles/*.json` enthalten die Rollen-Prompts.
- `.multi_agent_runs/<timestamp>/` mit `*.md` Outputs und `snapshot.txt`.

## Nutzung
```bash
python multi_agent_codex.py \
  --task "Baue ein CRUD mit FastAPI" \
  --dir . \
  --apply
```

## Wichtige Flags
### multi_agent_codex.py
| Flag | Beschreibung |
|-----|--------------|
| --task | Zentrale Aufgabe (Pflicht) |
| --dir | Arbeitsverzeichnis/Repo-Root (default: current dir) |
| --timeout | Timeout pro Agent in Sekunden |
| --apply | Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden |
| --fail-fast | Bei Patch-Fehler sofort abbrechen (nur mit --apply) |
| --ignore-fail | Exitcode immer 0, auch wenn Agenten fehlschlagen |
| --max-files | Max Dateien im Snapshot |
| --max-file-bytes | Max Bytes pro Datei im Snapshot |

### multi_role_agent_creator.py
| Flag | Beschreibung |
|-----|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Struktur
```text
.multi_agent_runs/
  └── TIMESTAMP/
      ├── architect.md
      ├── implementer.md
      ├── tester.md
      ├── reviewer.md
      └── integrator.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `roles`: Liste der Rollen mit `id`, `file` und optional `apply_diff`.
- `snapshot`: Steuerung des Workspace-Snapshots (Skip-Listen, Header, Format).
- `agent_output`: Header-Strings fuer Agent-Output Dateien.
- `messages`: Konsolen-Ausgaben und Fehlermeldungen.
- `diff_messages`: Meldungen fuer das Patch-Apply.
- `cli`: Beschreibung und Hilfe-Texte fuer argparse.

### Rollen: `config/roles/*.json`
Jede Rolle ist eine eigene JSON-Datei mit:
- `id`: Rollen-ID (muss zu `config/main.json` passen).
- `name`: Name des Agents (default: id).
- `role`: Rollenbezeichnung fuer die Ausgabe.
- `prompt_template`: Prompt-Template mit Platzhaltern wie `{task}`, `{snapshot}`,
  `{architect_summary}`, `{implementer_summary}`, `{tester_summary}` oder
  `{<rolle>_output}`.

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Sicherheit
- Standardmäßig **Dry-Run**
- Patches nur via `--apply`
- Kein Löschen bestehender Dateien ohne Diff

## Fehlerfaelle (Beispiele)
- `Fehler: Codex CLI nicht gefunden`: `codex` ist nicht im PATH oder `CODEX_CMD` fehlt.
- `Kein 'diff --git' Header`: Agent-Output enthaelt keinen git-style Unified Diff.
- `Fehler: Prompt fuer Rolle ...`: Platzhalter im `prompt_template` fehlt im Kontext.

## Performance-Tuning
- `--timeout`: Laengere Laufzeit pro Agent erlauben.
- `--max-files` / `--max-file-bytes`: Snapshot-Groesse begrenzen.

## Beispielrolle
Beispiel fuer eine neue Rolle in `config/roles/qa_guard.json`:
```json
{
  "id": "qa_guard",
  "name": "qa_guard",
  "role": "QA Guard",
  "prompt_template": "FORMAT:\n# QA Guard\n- Findings:\n- Risiken:\n- Vorschlaege:\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}
```

## Erweiterung
- Weitere Agenten in `config/main.json` registrieren und eigenes JSON in `config/roles/` anlegen
- Planner/Worker-Pattern möglich
- CI-Integration empfohlen

## Multi Role Agent Creator
Mit `multi_role_agent_creator.py` kannst du aus einer Beschreibung eine neue Rolle erzeugen
und automatisch in `config/main.json` registrieren lassen.

### Beispiel
```bash
python3 multi_role_agent_creator.py \
  --description "Analysiert Risiken und liefert konkrete Verbesserungen." \
  --id risk_analyst \
  --role "Risk Analyst" \
  --context architect_summary:ARCH\ (Kurz) \
  --insert-after reviewer
```

### Wichtige Optionen
| Option | Beschreibung |
|--------|--------------|
| --description | Beschreibung fuer die Rolle (Pflicht) |
| --id | Rollen-ID (default: aus Beschreibung generiert) |
| --name | Anzeigename (default: id) |
| --role | Rollenlabel (default: name) |
| --title | Titel im Prompt (default: role) |
| --context | Zus. Platzhalter (key oder key:Label) |
| --apply-diff | Markiert Rolle als Diff-Lieferant |
| --insert-after | Fuegt Rolle nach einer Rolle ein |
| --config | Pfad zu `config/main.json` |
| --force | Ueberschreibt vorhandene Rolle/Datei |

## Lizenz
MIT – freie Nutzung auf eigene Verantwortung


--- config/main.json ---

{
  "system_rules": "Du bist ein separater Agent in einem Multi-Agent-Workflow, der via Codex CLI ausgef\u00fchrt wird.\n\nWichtige Regeln:\n- Antworte strikt im geforderten FORMAT.\n- Keine unn\u00f6tigen Erkl\u00e4rungen au\u00dferhalb des Formats.\n- Sei pr\u00e4zise, umsetzungsorientiert und konsistent.\n- Wenn du Annahmen triffst, liste sie.\n",
  "final_role_id": "integrator",
  "summary_max_chars": 1400,
  "final_summary_max_chars": 2400,
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex exec -"
  },
  "paths": {
    "run_dir": ".multi_agent_runs",
    "snapshot_filename": "snapshot.txt",
    "apply_log_filename": "apply.log"
  },
  "roles": [
    {"id": "architect", "file": "roles/architect.json"},
    {"id": "implementer", "file": "roles/implementer.json", "apply_diff": true},
    {"id": "tester", "file": "roles/tester.json", "apply_diff": true},
    {"id": "reviewer", "file": "roles/reviewer.json", "apply_diff": true},
    {"id": "integrator", "file": "roles/integrator.json"}
  ],
  "snapshot": {
    "skip_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".idea", ".pytest_cache"],
    "skip_exts": [".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib"],
    "workspace_header": "WORKSPACE: {root}",
    "files_header": "FILES:",
    "content_header": "FILE CONTENT (truncated):",
    "file_line": "  - {rel} ({size} bytes)",
    "file_section_header": "--- {rel} ---"
  },
  "agent_output": {
    "agent_header": "## AGENT: {name} ({role})",
    "returncode_header": "### Returncode",
    "stdout_header": "### STDOUT",
    "stderr_header": "### STDERR"
  },
  "messages": {
    "error_task_empty": "Fehler: --task ist leer.",
    "error_prompt_missing_key": "Fehler: Prompt f\u00fcr Rolle '{role_id}' braucht fehlenden Platzhalter '{key}'.",
    "run_complete": "=== Multi-Agent Run fertig ===",
    "workspace_label": "Workspace:  {workspace}",
    "run_dir_label": "Run-Ordner: {run_dir}",
    "status_header": "Status:",
    "status_line": "- {agent_name:<11} rc={rc:<3} ok={ok} -> {out_file}",
    "patch_apply_header": "Patch Apply:",
    "integrator_output_header": "Integrator Output (Kurz):",
    "apply_no_diff": "[{label}] Kein diff gefunden \u2013 \u00fcbersprungen.",
    "apply_ok": "[{label}] {message}",
    "apply_error": "[{label}] FEHLER: {message}",
    "interrupted": "Abgebrochen.",
    "codex_not_found": "Fehler: Codex CLI nicht gefunden: {error}",
    "codex_tip": "Tipp: Stelle sicher, dass `codex` im PATH ist oder setze CODEX_CMD."
  },
  "diff_messages": {
    "no_git_header": "Kein 'diff --git' Header im Diff gefunden.",
    "patch_applied": "Patch angewendet.",
    "patch_exception": "Patch apply exception: {error}",
    "delete_file_error": "{rel_path}: konnte Datei nicht l\u00f6schen: {error}",
    "no_hunks": "{rel_path}: keine Hunks (nichts zu tun).",
    "context_mismatch": "{rel_path}: Kontext-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "delete_mismatch": "{rel_path}: Delete-Mismatch bei Zeile {line}: erwartet '{expected}', got '{got}'",
    "unknown_prefix": "{rel_path}: Unbekanntes Prefix '{prefix}'",
    "file_deleted": "{rel_path}: gel\u00f6scht.",
    "file_updated": "{rel_path}: aktualisiert.",
    "file_created": "{rel_path}: erstellt."
  },
  "cli": {
    "description": "Multi-Agent Orchestrator f\u00fcr Codex CLI (Architect/Implementer/Tester/Reviewer/Integrator).",
    "args": {
      "task": {"help": "Gesamtaufgabe / Problemstatement."},
      "dir": {"help": "Arbeitsverzeichnis/Repo-Root (default: current dir)."},
      "timeout": {"help": "Timeout pro Agent in Sekunden."},
      "apply": {"help": "Versucht Diffs aus Agent-Outputs auf Workspace anzuwenden."},
      "fail_fast": {"help": "Bei Patch-Fehler sofort abbrechen (nur mit --apply)."},
      "ignore_fail": {"help": "Exitcode immer 0, auch wenn Agenten fehlschlagen."},
      "max_files": {"help": "Max Dateien im Snapshot."},
      "max_file_bytes": {"help": "Max Bytes pro Datei im Snapshot."}
    }
  }
}


--- config/roles/architect.json ---

{
  "id": "architect",
  "name": "architect",
  "role": "Systemarchitekt",
  "prompt_template": "FORMAT:\n# Architektur\n- Ziele:\n- Komponenten:\n- Datenmodell:\n- API/Interfaces:\n- Risiken:\n- Plan (max 8 Schritte):\n\nAUFGABE:\n{task}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config/roles/implementer.json ---

{
  "id": "implementer",
  "name": "implementer",
  "role": "Senior Software Engineer",
  "prompt_template": "FORMAT:\n# Implementierung\n- Dateien neu/\u00e4ndern (Liste):\n- Entscheidungen:\n- Offene Punkte:\n\nDann liefere einen UNIFIED DIFF (git-style) f\u00fcr alle \u00c4nderungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCHITEKTUR (Kurz):\n{architect_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config/roles/integrator.json ---

{
  "id": "integrator",
  "name": "integrator",
  "role": "Integrator / Release Engineer",
  "prompt_template": "FORMAT:\n# Final\n- Zusammenfassung:\n- N\u00e4chste Schritte:\n- (Optional) Finaler UNIFIED DIFF:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH:\n{architect_output}\n\nIMPL OUTPUT:\n{implementer_output}\n\nTEST OUTPUT:\n{tester_output}\n\nREVIEW OUTPUT:\n{reviewer_output}\n"
}


--- config/roles/reviewer.json ---

{
  "id": "reviewer",
  "name": "reviewer",
  "role": "Staff Engineer (Code Reviewer)",
  "prompt_template": "FORMAT:\n# Review\n- Findings:\n- Risiko/Impact:\n- Empfohlene \u00c4nderungen:\n- Optionaler UNIFIED DIFF mit Fixes:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nARCH (Kurz):\n{architect_summary}\n\nIMPL (Kurz):\n{implementer_summary}\n\nTESTS (Kurz):\n{tester_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- config/roles/tester.json ---

{
  "id": "tester",
  "name": "tester",
  "role": "Senior QA / Test Engineer",
  "prompt_template": "FORMAT:\n# Tests\n- Teststrategie:\n- Testf\u00e4lle:\n- UNIFIED DIFF f\u00fcr Tests/Anpassungen:\n```diff\ndiff --git a/<path> b/<path>\n...\n```\n\nAUFGABE:\n{task}\n\nIMPLEMENTIERUNG (Kurz):\n{implementer_summary}\n\nKONTEXT (Workspace Snapshot):\n{snapshot}\n"
}


--- multi_agent_codex.py ---

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
    # On Windows, use non-POSIX splitting to keep backslashes/paths intact.
    return shlex.split(raw, posix=(os.name != "nt"))


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


--- multi_role_agent_creator.py ---

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


mcp startup: no servers

thinking
**Preparing test implementation plan**
exec
/bin/bash -lc 'rg --files' in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 242ms:
README.md
multi_role_agent_creator.py
multi_agent_codex.py
multi_agent/codex.py
multi_agent/models.py
multi_agent/cli.py
multi_agent/snapshot.py
multi_agent/pipeline.py
multi_agent/utils.py
multi_agent/__init__.py
multi_agent/constants.py
multi_agent/config_loader.py
multi_agent/diff_applier.py
config/main.json
config/roles/integrator.json
config/roles/reviewer.json
config/roles/implementer.json
config/roles/architect.json
config/roles/tester.json

thinking
**Checking existing multi_agent directory**
exec
/bin/bash -lc "sed -n '1,220p' multi_agent/pipeline.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 175ms:
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .codex import AgentExecutor, CodexClient
from .diff_applier import BaseDiffApplier, UnifiedDiffApplier
from .models import AgentResult, AgentSpec, AppConfig
from .snapshot import BaseSnapshotter, WorkspaceSnapshotter
from .utils import format_prompt, get_codex_cmd, now_stamp, summarize_text, write_text


class Pipeline:
    def __init__(
        self,
        snapshotter: BaseSnapshotter,
        diff_applier: BaseDiffApplier,
    ) -> None:

thinking
**Verifying existing refactor**
exec
/bin/bash -lc "sed -n '1,240p' multi_agent/diff_applier.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 38ms:
from __future__ import annotations

import abc
import re
from pathlib import Path
from typing import Dict, List, Tuple


class BaseDiffApplier(abc.ABC):
    @abc.abstractmethod
    def extract_diff(self, text: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def apply(self, workdir: Path, diff_text: str, diff_messages: Dict[str, str]) -> Tuple[bool, str]:
        raise NotImplementedError


class UnifiedDiffApplier(BaseDiffApplier):
    DIFF_GIT_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)$", re.MULTILINE)

thinking
**Checking for needed changes in multi_agent_codex.py**
exec
/bin/bash -lc "sed -n '1,220p' multi_agent_codex.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 39ms:
#!/usr/bin/env python3
"""
multi_agent_codex.py — Multi-Agent Orchestrator for Codex CLI

Thin CLI entrypoint. Implementation lives in the multi_agent package.
"""

from __future__ import annotations

from multi_agent.cli import main


if __name__ == "__main__":
    main()

thinking
**Verifying need for test updates**
exec
/bin/bash -lc "sed -n '1,260p' multi_agent/cli.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 83ms:
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

thinking
**Verifying existing implementation**
exec
/bin/bash -lc "sed -n '1,220p' multi_agent/constants.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 125ms:
from pathlib import Path

DEFAULT_TIMEOUT_SEC = 20 * 60  # 20 Minuten pro Agent
DEFAULT_MAX_FILES = 350        # Snapshot: max Dateien
DEFAULT_MAX_FILE_BYTES = 90_000  # Snapshot: max bytes pro Datei
DEFAULT_CONCURRENCY = 2        # Parallelität (optional)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "main.json"

thinking
**Checking available models**
exec
/bin/bash -lc "sed -n '1,260p' multi_agent/models.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 75ms:
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Dict, List


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

thinking
**Exploring key modules**
exec
/bin/bash -lc "sed -n '1,260p' multi_agent/utils.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 80ms:
from __future__ import annotations

import os
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_safe(path: Path, limit_bytes: int) -> str:
    if not path.exists() or not path.is_file():
exec
/bin/bash -lc "sed -n '1,260p' multi_agent/config_loader.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 76ms:
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import AppConfig, RoleConfig


def load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_role_config(role_entry: Dict[str, object], base_dir: Path) -> RoleConfig:
    role_path = base_dir / str(role_entry["file"])
    data = load_json(role_path)
    role_id = str(role_entry.get("id") or data.get("id") or "")
    if not role_id:
        raise ValueError(f"Role file missing id: {role_path}")
    return RoleConfig(
exec
/bin/bash -lc "sed -n '1,240p' multi_agent/snapshot.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 31ms:
from __future__ import annotations

import abc
from pathlib import Path
from typing import Dict, List

from .constants import DEFAULT_MAX_FILES, DEFAULT_MAX_FILE_BYTES
from .utils import read_text_safe


class BaseSnapshotter(abc.ABC):
    @abc.abstractmethod
    def build_snapshot(
        self,
        root: Path,
        snapshot_cfg: Dict[str, object],
        max_files: int,
        max_bytes_per_file: int,
    ) -> str:
        raise NotImplementedError
exec
/bin/bash -lc "sed -n '1,240p' multi_agent/codex.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 33ms:
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, List, Tuple

from .models import AgentResult, AgentSpec
from .utils import write_text


class CodexClient:
    def __init__(self, codex_cmd: List[str], timeout_sec: int) -> None:
        self._codex_cmd = codex_cmd
        self._timeout_sec = timeout_sec

    async def run(self, prompt: str, workdir: Path) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *self._codex_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,

thinking
**Verifying refactor completion and next steps**
exec
/bin/bash -lc "sed -n '1,200p' multi_agent/__init__.py" in /mnt/c/Users/Christof/Projects/Python/MultiAgent succeeded in 85ms:
"""Multi-Agent Codex package."""

thinking
**Summarizing test approach and diff**

I'll outline a test strategy and test cases focused on manual CLI checks since no code changes are needed; I’ll include an empty unified diff block to comply with the requested format.
codex
# Tests
- Teststrategie: Smoke-Tests der CLI-Pipeline (manuell), keine neuen automatisierten Tests erforderlich.
- Testfälle: `python multi_agent_codex.py --task "Smoke" --dir .`; `python multi_agent_codex.py --task "Smoke" --dir . --apply`; ungültige `config/main.json` (Syntaxfehler) prüfen; fehlender Platzhalter im Prompt provozieren.
- UNIFIED DIFF für Tests/Anpassungen:
```diff
diff --git a/README.md b/README.md
```
tokens used
79,975

