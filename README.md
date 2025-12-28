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
