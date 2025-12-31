# CODEX MASTER PACK – Implementation Spec (Echte Parallelität via Sharding)

Dieses Dokument ist so geschrieben, dass es **direkt als Task-Input** für Codex CLI taugt.
Ziel: Die aktuelle Codebasis (Python Orchestrator) so erweitern, dass `instances` **echte parallele Worker** sind,
weil der Orchestrator pro Rolle **Shard-Subtasks** erzeugt und jeder Instanz **explizit** einen Shard zuweist.

## Scope
- Basis ist der aktuelle Repo-Stand (Orchestrator) mit folgenden Kernmodulen:
  - `multi_agent/pipeline.py` (Orchestrierung, Role-Run, Instance-Run)
  - `multi_agent/codex.py` (Codex Subprocess + Timeout/124)
  - `multi_agent/task_split.py` (Task Split nach Überschriften; wiederverwendbar)
  - `multi_agent/models.py` (Config-/Datamodelle, z. B. RoleConfig)
  - `multi_agent/config_loader.py` (JSON Config Loader)
  - `multi_agent/schema_validator.py` (Schema/Validation)
  - (optional) `multi_agent/run_logger.py` oder vergleichbares Logging-Modul, falls vorhanden
- Keine Änderungen an externen Tools; Änderungen erfolgen im Orchestrator-Code + Configs + Tests + Doku.

---

## Zielbild (funktional)
1. Für jede Rolle wird vor Instanz-Start ein **ShardPlan** erzeugt.
2. Jede Instanz bekommt **genau einen Shard** (Subtask) inkl. klarer Instruktionen + Grenzen (Allowed Paths).
3. Instanzen einer Rolle laufen **parallel**.
4. Nach Instanzabschluss gibt es eine **Stage Barrier**:
   - Diffs werden validiert (Scope + Overlaps)
   - Role-Result wird konsolidiert
5. Erst danach startet die nächste Rolle (sequentiell gemäß `depends_on`).
6. Das gilt für **alle Rollen** einer Rollen-Familie, wenn `instances > 1` und `shard_mode != "none"`.

---

## Zielbild (konfigurierbar)
### Neue RoleConfig Felder (in `multi_agent/models.py`)
Erweitere die bestehende `RoleConfig` Dataclass um:

- `shard_mode: str = "none"`
  - `"none"`: aktuelles Verhalten (alle Instanzen bekommen denselben Task; nur für Ensemble/Varianten)
  - `"headings"`: Sharding anhand Markdown-Überschriften
  - `"files"`: heuristisches Sharding anhand betroffener Dateien/Pfade (siehe Regeln unten)
  - `"llm"`: optional (NICHT in V1 implementieren; als Stub/NotImplemented ok)
- `shard_count: int | None = None`
  - Default: `instances`
- `overlap_policy: str = "forbid"`
  - `"forbid"`: Stage fail oder Resolver-Run
  - `"warn"`: log + continue (aber **kein Apply ohne Warnung**)
  - `"allow"`: keine Prüfung (nur für Experimente)
- `enforce_allowed_paths: bool = True` (wirkt nur bei shard_mode != none)
- `max_files_per_shard: int | None = 10`
- `max_diff_lines_per_shard: int | None = 500`
- `reshard_on_timeout_124: bool = True`
- `max_reshard_depth: int = 2` (bei 124 darf ein Shard nochmals gesplittet werden)

**Config Loader:** `multi_agent/config_loader.py` muss diese Felder aus JSON laden, Defaults setzen.
**Schema Validator:** `multi_agent/schema_validator.py` muss sie validieren (Enum checks).

---

## Deterministische Regeln (kritisch!)
### Heading-Sharding (`shard_mode="headings"`)
- Eingabe ist ein Markdown-Task (String).
- Shards werden durch Überschriften **H1/H2/H3** definiert (Zeilenbeginn `#`, `##`, `###`).
- Jeder Abschnitt (Überschrift + nachfolgender Inhalt bis zur nächsten Überschrift gleichen oder höheren Levels) ist ein Shard.
- Text vor der ersten Überschrift wird als "Preamble" Shard `shard-0` behandelt (falls nicht leer).
- Wenn `shard_count` < Anzahl Shards:
  - Packe Shards in `shard_count` Batches (round-robin oder greedy by size). Verwende **greedy by size (Zeilenzahl)**.
- Wenn `shard_count` > Anzahl Shards:
  - Starte nur so viele Instanzen wie es Shards gibt (überschüssige Instanzen sind idle).

### Files-Sharding (`shard_mode="files"`)
V1: Heuristisch, ohne LLM.
- Extrahiere candidate paths aus Tasktext:
  - Tokens, die wie Pfade aussehen: enthalten `/` oder enden auf `.py`, `.json`, `.md`
  - Unterstütze backticks und Markdown links
- Wenn keine Pfade gefunden:
  - fallback auf `headings`
- Gruppiere Pfade nach Top-Level-Dir (z. B. `multi_agent/`, `config/`, `tests/`)
- Erzeuge Shards pro Gruppe (max_files_per_shard beachten).

### Allowed Paths
- Jeder Shard hat `allowed_paths` (glob patterns).
- Für headings-mode: wenn keine Pfade ableitbar sind, setze `allowed_paths=["**"]` (aber **enforce_allowed_paths bleibt True**,
  d. h. wir wollen trotzdem Diff-Check; bei "**" ist es effectively off).
- Für files-mode: allowed_paths = group globs (z. B. `multi_agent/**`, `tests/**`).

---

## Stage Barrier & Konsolidierung (entscheidend)
### Diff Parsing
Implementiere eine Utility:
- Datei: `multi_agent/diff_utils.py` (neu) oder innerhalb `sharding.py`
- Funktion: `extract_touched_files_from_unified_diff(diff_text) -> set[str]`
  - parse `+++ b/<path>` und `--- a/<path>` lines
  - ignore `/dev/null`
  - normalize paths

### Overlap Check
Nach Abschluss aller Instanzen einer Rolle:
- build mapping `file -> [instance_ids]`
- wenn overlap_policy == "forbid" und irgendeine Datei von >1 Instanz geändert wird:
  - Stage FAIL **oder** Resolver-Run (siehe unten, V1: FAIL + klare Meldung)
- wenn overlap_policy == "warn":
  - log warning + mark role as "dirty"; apply nur wenn user bestätigt (falls apply-mode aktiv)

### Allowed Paths Enforcement
Wenn `enforce_allowed_paths=True` und Shard.allowed_paths != ["**"]:
- wenn touched_files nicht subset of allowed_paths => FAIL oder Retry
V1: FAIL + klare Meldung, damit der Nutzer den Shard-Plan verbessert.

### Role Output Konsolidierung
V1: Kein automatisches “Merge der Diffs” nötig.
- Speichere jeden Instanz-Diff separat im Run-Ordner.
- Erzeuge ein "role_summary.json" mit:
  - shards
  - touched_files je shard
  - overlap report
- Wenn apply aktiviert ist:
  - apply Diffs in stabiler Reihenfolge (shard order) **nur wenn** keine overlaps (oder overlap_policy erlaubt es).

Optional V2: Resolver-Run (nicht in V1 verpflichtend).

---

## Timeout/124 Verhalten (deterministisch)
Ihr habt bereits Timeout -> returncode 124 in `multi_agent/codex.py`.
V1 Regeln:
- Wenn ein Instanz-Run 124 liefert und `reshard_on_timeout_124=True`:
  - falls `max_reshard_depth` nicht überschritten:
    - splitte den Shard erneut (headings fallback: split by paragraphs or sentences; V1: split by double-newline blocks)
    - re-run die kleineren Subshards seriell oder parallel (max 2 children) innerhalb derselben Stage
  - sonst: fail mit Hinweis "Shard too big → increase timeout or split task"
- Wichtig: Keine endlosen Retries.

---

## Konkrete Code-Tasks (Datei-Anker)
### Task A: Config Schema
- Dateien:
  - `multi_agent/models.py` (RoleConfig erweitern)
  - `multi_agent/config_loader.py` (parsen + defaults)
  - `multi_agent/schema_validator.py` (enums/validation)
- DoD:
  - alte configs laufen unverändert
  - neue configs werden akzeptiert

### Task B: Sharding Engine
- Neue Datei: `multi_agent/sharding.py` (oder `multi_agent/shard_planner.py`)
- Optional: `multi_agent/diff_utils.py`
- DoD:
  - `ShardPlanner.plan()` erzeugt deterministische Shards (headings & files)
  - Plan wird als JSON persistiert

### Task C: Pipeline Umbau
- Datei: `multi_agent/pipeline.py`
- Änderung:
  - vor Instanz-start ShardPlan generieren
  - Instanz i bekommt shard i prompt/context
  - nach Instanzen: validate overlaps/scope
  - Stage summary persistieren

### Task D: Tests
- Dateien: `tests/`
- Tests:
  - ShardPlanner headings determinism
  - diff touched files extraction
  - overlap policy forbid
  - pipeline stage with mocked codex runner (falls Runner abstrahierbar)

### Task E: Doku
- README ergänzen: "instances + shard_mode = echte Worker"

---

## Golden Path (muss bestehen)
Siehe `tasks/golden_path.md` und `configs/example_developer_main.json` im Master Pack.
Erwartung:
- implementer instances=3, shard_mode=headings
- 3 Shards -> 3 Instanzen parallel
- keine overlaps (weil Shards sind disjunkt)
- role_summary.json enthält 3 shards + touched files sets

---

## Deliverables
- Code implementiert (A–E)
- Tests grün
- Beispiele laufen
