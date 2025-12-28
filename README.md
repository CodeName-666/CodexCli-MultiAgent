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
| --apply-mode | Wann Diffs angewendet werden: end (nach allen Rollen) oder role (nach jeder Rolle) |
| --apply-roles | Welche Rollen angewendet werden (repeatable oder kommasepariert) |
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
      ├── task_board.json
      ├── coordination.log
      ├── architect_1.md
      ├── implementer_1.md
      ├── implementer_2.md
      ├── tester_1.md
      ├── reviewer_1.md
      └── integrator_1.md
```

## JSON Konfiguration
### Hauptdatei: `config/main.json`
- Die Ausfuehrungsreihenfolge und Auswahl der Rollen kommt ausschliesslich aus `roles` in `config/main.json`.
- `system_rules`: System-Regeln fuer alle Agenten.
- `final_role_id`: Rolle, deren Output als finale Kurz-Zusammenfassung genutzt wird.
- `summary_max_chars` / `final_summary_max_chars`: Laengen fuer Zusammenfassungen.
- `codex`: `env_var` und `default_cmd` fuer den Codex CLI Aufruf.
- `paths`: Run-Ordner und Dateinamen fuer Snapshot/Apply-Log.
- `coordination`: Task-Board + Log fuer parallele Rolleninstanzen.
- `outputs`: Dateinamen-Schema fuer Agent-Outputs (z.B. `<role>_<instance>.md`).
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
In `config/main.json` pro Rolle zusaetzlich:
- `instances`: Anzahl paralleler Instanzen (default: 1).

### Standard-Platzhalter
In jedem `prompt_template` verfuegbar:
- `{task}`: Globale Aufgabe.
- `{snapshot}`: Workspace-Snapshot.
- `{task_board_path}`: Pfad zum Task-Board (JSON).
- `{coordination_log_path}`: Pfad zum Koordinations-Log (JSONL).
- `{role_instance_id}` / `{role_instance}`: Instanz-Infos fuer parallele Rollen.
- `{<rolle>_summary}`: Kurz-Zusammenfassung der Rolle (z.B. `{architect_summary}`).
- `{<rolle>_output}`: Voller Output der Rolle (z.B. `{reviewer_output}`).

## Rollen-Ablauf
- Rollen laufen sequentiell in der Reihenfolge aus `config/main.json`.
- `apply_diff: true` markiert Rollen, deren Diffs bei `--apply` angewendet werden.
- `--apply-mode role` wendet Diffs direkt nach der Rolle an und erzeugt einen frischen Snapshot.
- Die finale Kurz-Ausgabe stammt von `final_role_id`.

## Parallelisierung pro Rolle
- `roles[].instances` startet mehrere Instanzen derselben Rolle parallel.
- Task-Board und Log liegen im Run-Ordner (`task_board.json`, `coordination.log`).
- Output-Dateien nutzen das Pattern aus `outputs.pattern` (z.B. `<role>_<instance>.md`).

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

## Neuere Updates
- `--apply-mode` und `--apply-roles` geben Kontrolle ueber Zeitpunkt und Auswahl der Patch-Anwendung.
- Status-Ausgabe enthaelt jetzt einen lesbaren Text (`OK`, `KEIN_BEITRAG`, `FEHLER`).
- Snapshots ignorieren `.multi_agent_runs`, um Kontextgroesse zu reduzieren.

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
