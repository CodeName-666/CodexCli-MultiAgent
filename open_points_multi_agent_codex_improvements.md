# Offene Punkte aus multi_agent_codex_improvements.md (Quick-Check)

## Nicht umgesetzt
- JSON-Schema-Validierung: `--validate-config` prueft nur Pflichtfelder; `config/schema/*.json` wird nicht genutzt.
- Grep/rg-Index fuer selektiven Kontext: Dateiauswahl basiert nur auf Task-Token in Dateinamen.
- Integrationstests mit Mock-Codex fuer End-to-End Runs fehlen.
- Saubere Abbrueche: kein zentraler Shutdown/Cancel der laufenden Agent-Prozesse bei KeyboardInterrupt in der Pipeline.
- Prompt-Limits: Zeichenlimits und Summary-Reduktion sind da, aber keine Token-basierten Schranken oder Modellabhaengigkeit.

## Umgesetzt

## Fehler/Abweichungen
- `--validate-config` suggeriert Schema-Validierung, validiert aber nur Pflichtfelder; das kann fehlerhafte Configs passieren lassen.
