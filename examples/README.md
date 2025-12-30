# Sharding Examples

Dieses Verzeichnis enthält Beispielkonfigurationen und Tasks für das Sharding-Feature.

## Dateien

### Konfigurationen

**`sharding_basic_config.json`**
- Einfaches Setup mit nur einer Role (implementer)
- 3 Instanzen mit `shard_mode=headings`
- Ideal zum Testen und Kennenlernen

**Verwendung:**
```bash
python -m multi_agent.cli \
  --config examples/sharding_basic_config.json \
  --task "@examples/task_three_features.md"
```

---

**`sharding_advanced_config.json`**
- Vollständige Pipeline mit 5 Roles
- Verschiedene Sharding-Modi pro Role
- Strikte Validation (`overlap_policy=forbid`, `enforce_allowed_paths=true`)
- Production-ready Setup

**Verwendung:**
```bash
python -m multi_agent.cli \
  --config examples/sharding_advanced_config.json \
  --task "@examples/task_three_features.md" \
  --apply
```

### Tasks

**`task_three_features.md`**
- Beispiel-Task mit 3 klar abgegrenzten Features
- Strukturiert für optimales Heading-based Sharding
- Jedes Feature hat Goal, Allowed Paths, Requirements, DoD

**Erwartetes Verhalten:**
- 3 H1-Headings → 3 Shards
- Bei 3 Instances: Jede Instanz bekommt 1 Feature
- Bei 4 Instances: Greedy-Verteilung (1 Instance idle oder doppelt)

## Erwartete Outputs

Nach dem Run findest du im Run-Verzeichnis (`.multi_agent_runs/<timestamp>/`):

### Sharding-Artefakte
- **`implementer_shard_plan.json`** - Der generierte Shard-Plan
  ```json
  {
    "role_id": "implementer",
    "shard_mode": "headings",
    "shard_count": 3,
    "shards": [
      {
        "id": "shard-1",
        "title": "Feature A: User Authentication System",
        "goal": "Implement a complete JWT-based authentication system...",
        "allowed_paths": ["app/auth/jwt.py", "app/auth/tokens.py", ...]
      },
      ...
    ]
  }
  ```

- **`implementer_shard_summary.json`** - Validation-Ergebnis
  ```json
  {
    "role": "implementer",
    "shard_count": 3,
    "instances": {
      "implementer#1": ["app/auth/jwt.py", "app/auth/tokens.py"],
      "implementer#2": ["app/auth/rbac.py", "app/models/role.py"],
      "implementer#3": ["app/middleware/rate_limit.py", "app/utils/redis_client.py"]
    },
    "overlaps": {},
    "validation": "passed"
  }
  ```

- **`implementer_overlaps.json`** - Falls Overlaps erkannt wurden
  ```json
  {
    "role": "implementer",
    "overlap_count": 1,
    "overlapping_files": {
      "app/middleware/auth.py": ["implementer#1", "implementer#2"]
    }
  }
  ```

### Instanz-Outputs
- **`implementer_1.md`** - Output der 1. Instanz (Feature A)
- **`implementer_2.md`** - Output der 2. Instanz (Feature B)
- **`implementer_3.md`** - Output der 3. Instanz (Feature C)

Jede Datei enthält nur den Code/Diff für ihr zugewiesenes Feature.

## Experimente

### Experiment 1: Overlap-Detection testen

Modifiziere `task_three_features.md` so, dass zwei Features dieselbe Datei benötigen:

```markdown
# Feature A
## Allowed paths
- app/auth/jwt.py
- app/middleware/auth.py  ← Shared file

# Feature B
## Allowed paths
- app/auth/rbac.py
- app/middleware/auth.py  ← Shared file (Overlap!)
```

**Mit `overlap_policy=forbid`:**
```
Shard validation failed: Overlaps detected: app/middleware/auth.py (implementer#1, implementer#2)
→ Pipeline stoppt
```

**Mit `overlap_policy=warn`:**
```
Warning: Overlaps detected
→ Pipeline läuft weiter
→ Overlap-Report in implementer_overlaps.json
```

### Experiment 2: Allowed Paths Enforcement

Setze in `sharding_advanced_config.json`:
```json
"enforce_allowed_paths": true
```

Wenn eine Instanz eine Datei außerhalb ihrer `allowed_paths` ändert:
```
Shard validation failed: implementer#1 violated allowed_paths: app/utils/helper.py
```

### Experiment 3: Unbalanced Shards

Erstelle einen Task mit stark unterschiedlich großen Sections:

```markdown
# Feature A (klein, 10 Zeilen)
Simple utility function

# Feature B (groß, 200 Zeilen)
Complete authentication system with multiple endpoints,
middleware, database models, tests, documentation...
```

**Beobachtung:**
- Instanz #1 (Feature A) findet deutlich schneller fertig
- Instanz #2 (Feature B) läuft viel länger
- → Gesamt-Runtime = Runtime der langsamsten Instanz

**Lösung:**
Feature B weiter aufteilen in mehrere H1-Sections

## Troubleshooting

**Problem: "No shards created despite shard_mode=headings"**
- Check: Hat der Task H1-Headings (`# Title`)?
- Lösung: Mindestens ein `# Heading` einfügen

**Problem: "All instances get the same task"**
- Check: Ist `shard_mode` wirklich gesetzt?
- Check: Ist `instances > 1`?
- Debug: `cat .multi_agent_runs/<timestamp>/implementer_shard_plan.json`

**Problem: "Overlaps detected but files look different"**
- Ursache: Beide Instanzen ändern technisch dieselbe Datei (auch unterschiedliche Zeilen)
- Lösung: Task besser strukturieren oder `overlap_policy=allow`

## Weitere Ressourcen

- **[Vollständige Sharding-Dokumentation](../docs/SHARDING.md)**
- **[Hauptkonfigurationen](../config/)**
- **[Golden Path Test](../updates/tasks/golden_path.md)**
