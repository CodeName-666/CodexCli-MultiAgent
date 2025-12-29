# Verbesserungen fuer multi_agent_codex.py (Projekt)

Ziel: Hoehere Effizienz, stabilere Runs und bessere Ergebnisqualitaet. Die Datei `multi_agent_codex.py`
ist nur der CLI-Entrypoint; die wirklichen Hebel liegen in `multi_agent/` und der JSON-Konfiguration.

## Quick Wins (geringer Aufwand, hoher Nutzen)
- **Snapshot effizienter**: 
  - Skip-Liste um typische Build/Cache-Ordner erweitern (z.B. `.venv`, `.mypy_cache`, `node_modules`).
  - Optional: Dateigroessenlimit pro Datei dynamisch reduzieren, wenn der Snapshot zu gross wird.
  - Optional: Hash-Caching fuer Snapshots (erneuter Run mit unveraendertem Workspace spart Zeit).
- **Prompt-Limits**: 
  - Vor dem Agent-Lauf die Prompt-Laenge gegen ein Token/Char-Limit pruefen und kuerzen.
  - Alte Outputs im Kontext schrittweise zusammenfassen (z.B. Kontext-Compression nach jedem Agent).
- **Bessere Fehlersignale**:
  - Wenn `codex` einen non-zero RC liefert, Fail-Reason in der Statusausgabe hervorheben.
  - Optional: Bei leerem Output oder Timeout einen Retry mit kuerzerem Prompt.

## Effizienz (Runtime und Kosten)
- **Parallelisierung**:
  - Unabhaengige Rollen (z.B. Tester/Reviewer nach Implementer) parallel laufen lassen.
  - Voraussetzung: Config-Flag pro Rolle (z.B. `depends_on`) und DAG-Execution.
- **Delta-Snapshot statt Vollsnapshot**:
  - Bei wiederholten Runs nur geaenderte Dateien in den Snapshot aufnehmen.
  - Optional: zuletzt angewendete Diffs in den Kontext aufnehmen, statt kompletten Snapshot.
- **Selective Context**:
  - Relevanzfilter: Nur Dateien, die per Prompt/Task betroffen sind (Heuristik ueber Dateinamen).
  - Optional: Grep-Index (rg) fuer Dateiauswahl, statt alle Inhalte zu dumpen.

## Ergebnisqualitaet (Antworten der Agenten)
- **Strengere Output-Schemata pro Rolle**:
  - `prompt_template` klar strukturieren (z.B. YAML/JSON-Format oder feste Abschnittsmarker).
  - Validator, der Abschnitte prueft und bei Fehlern eine Self-Repair-Runde triggert.
- **Feedback-Loop**:
  - Reviewer-Output gezielt in Implementer-Revision einspeisen.
  - Optionale zweite Implementer-Runde nur bei kritischen Review-Findings.
- **Patch-Qualitaet verbessern**:
  - Patch-Precheck: `git apply --check` (falls Git vorhanden) vor `apply`.
  - Bei Kontext-Mismatch: Fallback-Strategie (z.B. `--3way` oder kleinere hunks).

## Robustheit und Zuverlaessigkeit
- **Retry-Logik**:
  - Konfigurierbare Retries bei Timeout/Fehlern (z.B. 1-2 Versuche mit Backoff).
  - Role-spezifische Timeouts (z.B. Architect laenger, Reviewer kuerzer).
- **Saubere Abbrueche**:
  - Bei `KeyboardInterrupt` auch laufende Subprozesse terminieren und Run-Log finalisieren.
- **Fehlertolerante Diff-Anwendung**:
  - Wenn eine Rolle keinen Diff liefert, explizit im Summary hervorheben (nicht nur im Log).

## Observability (Nachvollziehbarkeit)
- **Run-Metadaten**:
  - Pro Run eine `run.json` mit Konfig, Zeitstempeln, Token/Char-Groessen, RCs, Dauer je Rolle.
- **Structured Logs**:
  - Option fuer JSON-Logs (fuer CI/Monitoring), zusaetzlich zu menschenlesbarer Ausgabe.
- **Agent-Outputs sauberes Normalisieren**:
  - Entfernen leerer Sections, Reduzierung von sehr langen stderr-Ausgaben in Summary.

## Konfiguration und DX (Developer Experience)
- **Schema-Validierung fuer JSON**:
  - JSON-Schema fuer `config/developer_main.json` (oder `config/designer_main.json`) und `config/developer_roles/*.json` (oder `config/designer_roles/*.json`).
  - CLI: `--validate-config` vor dem Run.
- **Per-Rollen-Optionen**:
  - `timeout_sec`, `max_output_chars`, `max_prompt_chars`, `retries`.
  - `apply_diff` nur fuer Rollen mit sicherem Patch-Output.
- **Mehrere Modelle**:
  - Pro Rolle anderes Modell oder Codex-Command (z.B. "architect" groesseres Modell).

## Sicherheit
- **Safety-Check fuer Diffs**:
  - Blockliste fuer kritische Pfade (z.B. `~/.ssh`, `config/*`).
  - Optionaler "dry-run diff preview" mit Benutzerbestaetigung vor `--apply`.

## Tests
- **Unit-Tests fuer Kernlogik**:
  - Snapshotter: Skip-Listen, File-Size-Limits, Encoding-Faelle.
  - Diff-Applier: Hunk-Anwendung, Delete/New, Context-Mismatch.
  - Prompt-Format: Fehlende Keys muessen sauber erklaert werden.
- **Integration-Tests**:
  - Mock-Codex-Client (fixture) fuer reproducible End-to-End Runs.

## Priorisierte Umsetzungsempfehlung
1) Prompt-Limits + Summarizer-Compression im Kontext
2) Role-spezifische Timeouts + Retry-Logik
3) Snapshot-Skip-Listen erweitern + Delta-Snapshot
4) JSON-Schema-Validierung + `--validate-config`
5) DAG/Parallelisierung fuer unabhaengige Rollen

