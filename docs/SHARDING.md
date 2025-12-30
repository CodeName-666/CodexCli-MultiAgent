# Sharding: True Parallel Agent Execution

## Overview

Das Sharding-Feature ermöglicht **echte Parallelität** bei der Multi-Agent-Orchestrierung. Statt dass alle Instanzen einer Rolle denselben Task erhalten (Ensemble-Modus), kann der Task nun automatisch in **Shards** (Subtasks) aufgeteilt werden, wobei jede Instanz einen eigenen Shard bearbeitet.

### Vorher (Ensemble-Modus)
```
Task: "Implement features A, B, C"
├─ Instance #1 → Task: "Implement features A, B, C"
├─ Instance #2 → Task: "Implement features A, B, C"
└─ Instance #3 → Task: "Implement features A, B, C"
```
**Problem:** Alle Instanzen arbeiten redundant, können sich überlappen

### Nachher (Sharding-Modus)
```
Task: "# Feature A\n...\n# Feature B\n...\n# Feature C\n..."
├─ Instance #1 → Shard 1: "# Feature A\n..."
├─ Instance #2 → Shard 2: "# Feature B\n..."
└─ Instance #3 → Shard 3: "# Feature C\n..."
```
**Vorteil:** Echte Parallelität, keine Überlappungen, schnellere Ausführung

---

## Quick Start

### 1. Aktiviere Sharding in deiner Role-Config

```json
{
  "role_defaults": {
    "shard_mode": "headings",
    "overlap_policy": "warn"
  },
  "roles": [
    {
      "id": "implementer",
      "file": "roles/implementer.json",
      "instances": 3,
      "shard_mode": "headings"
    }
  ]
}
```

### 2. Strukturiere deinen Task mit Markdown-Headings

```markdown
# Feature A: User Authentication
Implement JWT-based authentication...

# Feature B: Database Schema
Create database models for...

# Feature C: API Endpoints
Implement REST API endpoints...
```

### 3. Führe aus

```bash
python -m multi_agent.cli --config config.json --task "@task.md"
```

Der Orchestrator erstellt automatisch:
- **3 Shards** (ein Shard pro H1-Heading)
- **3 parallele Instanzen** (jede bekommt einen Shard)
- **Overlap-Detection** nach Abschluss aller Instanzen

---

## Configuration Reference

### Sharding Fields (RoleConfig)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `shard_mode` | string | `"none"` | Sharding-Modus: `none`, `headings`, `files`, `llm` (V1: nur `headings`) |
| `shard_count` | int? | `instances` | Anzahl der Shards (überschreibt auto-detection) |
| `overlap_policy` | string | `"warn"` | Wie mit Überlappungen umgegangen wird: `forbid`, `warn`, `allow` |
| `enforce_allowed_paths` | bool | `false` | Strikt prüfen, dass Instanzen nur erlaubte Dateien ändern |
| `max_files_per_shard` | int? | `10` | Max. Dateien pro Shard (für `files`-Mode) |
| `max_diff_lines_per_shard` | int? | `500` | Max. Diff-Zeilen pro Shard (Warnung) |
| `reshard_on_timeout_124` | bool | `true` | Bei Timeout Shard nochmals aufteilen |
| `max_reshard_depth` | int | `2` | Max. Tiefe für rekursives Re-Sharding |

### Shard Modes

#### `none` (Default)
Kein Sharding. Alle Instanzen bekommen den vollständigen Task.
- **Use Case:** Ensemble-Voting, Varianten-Generierung
- **Beispiel:** 3 Reviewer bekommen denselben Code

#### `headings` (Empfohlen für V1)
Sharding basierend auf Markdown H1-Headings (`# Title`).
- **Use Case:** Feature-basierte Aufteilung, modulare Tasks
- **Algorithmus:**
  1. Extrahiere alle H1-Headings
  2. Jeder H1-Abschnitt = 1 Shard
  3. Falls `shard_count < anzahl_headings`: Greedy-Grouping nach Größe
  4. Falls `shard_count > anzahl_headings`: Überschüssige Instanzen sind idle

**Beispiel Task-Struktur:**
```markdown
# Chunk 1: Add Config Fields
## Goal
Add new RoleConfig fields for sharding

## Allowed paths
- multi_agent/models.py
- multi_agent/config_loader.py

## Definition of done
- Fields are parsed correctly
- Schema validation passes

# Chunk 2: Implement Planner
## Goal
Create deterministic ShardPlanner

## Allowed paths
- multi_agent/sharding.py

## Definition of done
- Unit tests pass
```

**Metadata-Extraktion:**
- `## Goal` → Shard.goal (erste Zeile nach Heading)
- `## Allowed paths` → Shard.allowed_paths (Listeneinträge `- path`)
- Metadata ist optional, wird aber für `enforce_allowed_paths` genutzt

#### `files` (Experimental)
Heuristische Aufteilung nach Dateipfaden im Task.
- **Use Case:** Tasks mit expliziter Dateiliste
- **Algorithmus:**
  1. Extrahiere Pfade aus Text (Regex + Backticks + Markdown-Links)
  2. Gruppiere nach Top-Level-Directory
  3. Erstelle Shards pro Directory-Gruppe
  4. **Fallback:** Bei 0 Pfaden → `headings`-Mode

**Beispiel:**
```markdown
Update the following files:
- `multi_agent/models.py`
- `multi_agent/config_loader.py`
- `tests/test_models.py`
```
→ 2 Shards: `multi_agent/**`, `tests/**`

#### `llm` (Not Implemented in V1)
LLM-basiertes intelligentes Sharding.
- **Status:** Stub, raises `NotImplementedError`
- **Geplant für V2**

---

## Overlap Policies

### `forbid` (Strikt)
Bei Datei-Überlappungen wird die gesamte Role abgebrochen.

**Wann verwenden:**
- Kritische Production-Deployments
- Strenge Compliance-Anforderungen

**Verhalten:**
```
Overlaps detected: file.py (instance1, instance2)
→ abort_run = True
→ Pipeline stoppt nach dieser Role
```

### `warn` (Empfohlen, Default)
Überlappungen werden geloggt, aber Pipeline läuft weiter.

**Wann verwenden:**
- Development/Testing
- Explorative Tasks

**Verhalten:**
```
Overlaps detected: file.py (instance1, instance2)
→ Warning logged
→ Overlap report saved to <role>_overlaps.json
→ Pipeline continues
```

### `allow` (Experimentell)
Keine Overlap-Prüfung, alle Diffs werden angewendet.

**Wann verwenden:**
- Prototyping
- Tasks, wo Überlappungen erwartet/gewünscht sind

**Verhalten:**
```
Keine Overlap-Detection
→ Alle Diffs werden nacheinander angewendet (Reihenfolge: Shard-Order)
```

---

## Stage Barrier & Validation

Nach Abschluss aller Instanzen einer Role:

### 1. Diff Extraction
Jeder Instanz-Output wird geparst:
```python
touched_files = extract_touched_files_from_unified_diff(diff_text)
# Beispiel: {"multi_agent/models.py", "multi_agent/config_loader.py"}
```

### 2. Allowed Paths Validation
Falls `enforce_allowed_paths=true`:
```python
is_valid = all(file in allowed_paths for file in touched_files)
# Beispiel: allowed_paths = ["multi_agent/**"]
```

**Bei Violation:**
```
Shard validation failed: instance1 violated allowed_paths: tests/file.py
→ Saved to <role>_shard_summary.json
```

### 3. Overlap Detection
```python
overlaps = {
  "file.py": ["instance1", "instance3"],
  "other.py": ["instance2", "instance3"]
}
```

### 4. Validation Report
Gespeichert als `<role>_shard_summary.json`:
```json
{
  "role": "implementer",
  "shard_count": 3,
  "instances": {
    "implementer#1": ["multi_agent/models.py"],
    "implementer#2": ["multi_agent/config_loader.py"],
    "implementer#3": ["multi_agent/pipeline.py"]
  },
  "overlaps": {},
  "validation": "passed"
}
```

---

## Output Artifacts

### Per-Role Outputs

**`<role>_shard_plan.json`** (wenn Sharding aktiv)
```json
{
  "role_id": "implementer",
  "shard_mode": "headings",
  "shard_count": 3,
  "overlap_policy": "warn",
  "enforce_allowed_paths": false,
  "shards": [
    {
      "id": "shard-1",
      "title": "Add Config Fields",
      "goal": "Extend RoleConfig with sharding fields",
      "allowed_paths": ["multi_agent/models.py", "multi_agent/config_loader.py"]
    },
    ...
  ]
}
```

**`<role>_shard_summary.json`** (Validation-Ergebnis)
```json
{
  "role": "implementer",
  "shard_count": 3,
  "instances": {
    "implementer#1": ["file1.py"],
    "implementer#2": ["file2.py"],
    "implementer#3": ["file3.py"]
  },
  "overlaps": {},
  "validation": "passed"
}
```

**`<role>_overlaps.json`** (falls Overlaps erkannt)
```json
{
  "role": "implementer",
  "overlap_count": 2,
  "overlapping_files": {
    "multi_agent/utils.py": ["implementer#1", "implementer#3"],
    "tests/test_utils.py": ["implementer#2", "implementer#3"]
  }
}
```

---

## Best Practices

### 1. Task-Strukturierung für Heading-Mode

**✅ Good:**
```markdown
# Feature A: Authentication
Implement JWT authentication with refresh tokens.

# Feature B: Authorization
Add role-based access control (RBAC).

# Feature C: API Security
Add rate limiting and CORS configuration.
```

**❌ Bad:**
```markdown
Please implement authentication, authorization, and API security features.
All features should work together.
```

**Warum:** Klar abgegrenzte H1-Sections → deterministische Shards

### 2. Allowed Paths angeben

**✅ Good:**
```markdown
# Feature A: User Model
## Goal
Create user database model

## Allowed paths
- app/models/user.py
- app/schemas/user.py
- tests/test_user_model.py
```

**❌ Bad:**
```markdown
# Feature A: User Model
Create user database model (change whatever files you need)
```

**Warum:** Explizite Pfade → bessere Overlap-Vermeidung

### 3. Shard-Balance beachten

**✅ Good:** Ähnlich große Sections
```markdown
# Feature A (ca. 50 Zeilen)
...

# Feature B (ca. 60 Zeilen)
...

# Feature C (ca. 55 Zeilen)
...
```

**❌ Bad:** Stark unterschiedliche Größen
```markdown
# Feature A (5 Zeilen)
...

# Feature B (200 Zeilen)
...
```

**Warum:** Unbalanced Shards → eine Instanz ist viel länger beschäftigt

### 4. Overlap-Policy je nach Phase

**Development:**
```json
"overlap_policy": "warn"
```

**Production:**
```json
"overlap_policy": "forbid",
"enforce_allowed_paths": true
```

---

## Advanced Configuration

### Conditional Sharding

Sharding nur für bestimmte Roles:
```json
{
  "role_defaults": {
    "shard_mode": "none"
  },
  "roles": [
    {
      "id": "architect",
      "instances": 2,
      "shard_mode": "none"  // Ensemble voting
    },
    {
      "id": "implementer",
      "instances": 3,
      "shard_mode": "headings"  // Parallel work
    },
    {
      "id": "reviewer",
      "instances": 2,
      "shard_mode": "none"  // Review full output
    }
  ]
}
```

### Dynamic Shard Count

Mehr Shards als Instanzen (für bessere Granularität):
```json
{
  "id": "implementer",
  "instances": 3,
  "shard_mode": "headings",
  "shard_count": 5  // 5 Shards auf 3 Instanzen verteilt
}
```

→ Greedy-Algorithmus verteilt Shards optimal

### Custom Timeouts pro Shard

```json
{
  "id": "implementer",
  "instances": 3,
  "timeout_sec": 600,
  "reshard_on_timeout_124": true,
  "max_reshard_depth": 1
}
```

Bei Timeout:
1. Shard wird nochmals aufgeteilt (z.B. bei Double-Newlines)
2. Kleinere Sub-Shards werden erneut versucht
3. Max. 1 Ebene tief (um Endlosschleifen zu vermeiden)

---

## Troubleshooting

### Problem: "No shards created"

**Ursache:** Task hat keine H1-Headings

**Lösung:**
```markdown
# Task 1
Content...

# Task 2
Content...
```

Oder: `shard_mode="none"` für Tasks ohne Struktur

### Problem: "Shard validation failed: overlap detected"

**Ursache:** Mehrere Instanzen haben dieselbe Datei geändert

**Diagnose:**
```bash
cat run_dir/<role>_overlaps.json
```

**Lösungen:**
1. **Task besser strukturieren:** Klarere Abgrenzung der Features
2. **Allowed Paths nutzen:** Explizite Pfadzuweisung pro Shard
3. **Overlap Policy ändern:** `"warn"` statt `"forbid"`

### Problem: "Instance violated allowed_paths"

**Ursache:** Instanz hat Datei außerhalb der erlaubten Pfade geändert

**Diagnose:**
```bash
cat run_dir/<role>_shard_summary.json
# Check "violations" field
```

**Lösungen:**
1. **Allowed Paths erweitern:** Fehlende Pfade zur `## Allowed paths` Liste hinzufügen
2. **Enforcement deaktivieren:** `"enforce_allowed_paths": false` (nur für Development)

### Problem: "Unbalanced shards (one instance finishes 10x faster)"

**Ursache:** Stark unterschiedliche Shard-Größen

**Diagnose:**
```bash
cat run_dir/<role>_shard_plan.json
# Check content length per shard
```

**Lösungen:**
1. **Task umstrukturieren:** Größere Sections aufteilen
2. **Mehr Instances:** `instances` erhöhen für bessere Verteilung
3. **Custom shard_count:** `"shard_count": 6` für feinere Granularität

---

## Migration Guide

### Von Ensemble zu Sharding

**Vorher (Ensemble):**
```json
{
  "id": "implementer",
  "instances": 3
}
```

**Nachher (Sharding):**
```json
{
  "id": "implementer",
  "instances": 3,
  "shard_mode": "headings",
  "overlap_policy": "warn"
}
```

**Task anpassen:**
```markdown
# Feature 1
...

# Feature 2
...

# Feature 3
...
```

### Schrittweise Migration

1. **Phase 1:** Nur eine Role mit Sharding testen
   ```json
   "shard_mode": "headings",
   "overlap_policy": "allow"  // Permissive
   ```

2. **Phase 2:** Validation aktivieren
   ```json
   "overlap_policy": "warn",
   "enforce_allowed_paths": false
   ```

3. **Phase 3:** Strikte Policies
   ```json
   "overlap_policy": "forbid",
   "enforce_allowed_paths": true
   ```

---

## Performance Considerations

### Wann lohnt sich Sharding?

**✅ Sharding sinnvoll:**
- **Große Tasks** (>5 Features/Module)
- **Klar abgegrenzte Subtasks**
- **Parallele Bearbeitung möglich** (keine Abhängigkeiten)
- **Zeitkritische Deployments**

**❌ Ensemble besser:**
- **Kleine Tasks** (1-2 Features)
- **Kreative/explorative Tasks** (Varianten gewünscht)
- **Review/Voting** (mehrere Meinungen)

### Expected Speedup

Bei idealen Bedingungen (perfekt balancierte Shards, keine Overlaps):

| Instances | Theoretical Speedup | Realistic Speedup |
|-----------|---------------------|-------------------|
| 2 | 2x | 1.6-1.8x |
| 3 | 3x | 2.2-2.6x |
| 4 | 4x | 2.8-3.4x |

**Overhead-Faktoren:**
- Shard-Plan-Erstellung: ~0.1-0.5s
- Validation: ~0.1-0.3s
- Unbalanced Shards: -10-30%

---

## API Reference

### Python API

```python
from multi_agent.sharding import create_shard_plan
from multi_agent.models import RoleConfig

role_cfg = RoleConfig(
    id="implementer",
    shard_mode="headings",
    instances=3,
    # ... other fields
)

task_text = """
# Feature A
...

# Feature B
...
"""

shard_plan = create_shard_plan(role_cfg, task_text)
# Returns ShardPlan with 2 shards
```

### Dataclasses

```python
@dataclasses.dataclass(frozen=True)
class Shard:
    id: str                    # "shard-1", "shard-2", ...
    title: str                 # "Feature A"
    goal: str                  # "Implement authentication"
    content: str               # Full markdown content
    allowed_paths: List[str]   # ["app/models/**", "tests/**"]

@dataclasses.dataclass(frozen=True)
class ShardPlan:
    role_id: str
    shard_mode: str
    shard_count: int
    shards: List[Shard]
    overlap_policy: str
    enforce_allowed_paths: bool
```

---

## Roadmap

### V1.0 (Current) ✅
- ✅ Heading-based sharding
- ✅ Overlap detection
- ✅ Allowed paths enforcement
- ✅ Stage barrier validation
- ✅ Greedy shard distribution

### V1.5 (Planned)
- ⏳ Re-sharding on timeout 124
- ⏳ Improved files-mode heuristics
- ⏳ Shard balance metrics
- ⏳ Performance profiling per shard

### V2.0 (Future)
- 📋 LLM-based intelligent sharding
- 📋 Automatic overlap resolution (Resolver-Run)
- 📋 Dynamic shard rebalancing
- 📋 Cross-role shard dependencies

---

## FAQ

**Q: Kann ich Sharding mit apply_diff kombinieren?**
A: Ja! Diffs werden nach Shard-Reihenfolge angewendet. Bei Overlaps siehe `overlap_policy`.

**Q: Was passiert bei mehr Instances als Shards?**
A: Überschüssige Instanzen bleiben idle (werden nicht gestartet).

**Q: Funktioniert Sharding mit allen Rollen?**
A: Ja, aber am sinnvollsten für `implementer`, `tester`, `refactorer`. Für `reviewer` eher Ensemble.

**Q: Wie debugge ich Shard-Probleme?**
A: Check `<role>_shard_plan.json` und `<role>_shard_summary.json` im Run-Directory.

**Q: Kann ich Sharding deaktivieren?**
A: Ja: `"shard_mode": "none"` (oder Feld weglassen, Default ist `"none"`).

---

## Examples

Siehe `examples/` Ordner:
- `examples/sharding_basic.json` - Einfaches Sharding-Setup
- `examples/sharding_advanced.json` - Alle Features genutzt
- `examples/tasks/three_features.md` - Beispiel-Task mit 3 Shards

---

## Support

Bei Problemen:
1. Check `<role>_shard_summary.json` für Validation-Details
2. Erhöhe Logging: `"logging": {"jsonl_enabled": true}`
3. Issue erstellen: [GitHub Issues](https://github.com/your-repo/issues)

---

**Last Updated:** 2025-12-31
**Version:** 1.0.0
**Authors:** Claude Sonnet 4.5
