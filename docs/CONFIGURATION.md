# Erweiterte Konfiguration

Vollständige Referenz aller Konfigurationsoptionen für den Multi-Agent Codex CLI Orchestrator.

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Hauptkonfiguration](#hauptkonfiguration)
3. [Rollen-Konfiguration](#rollen-konfiguration)
4. [Sharding-Optionen](#sharding-optionen)
5. [System-Regeln](#system-regeln)
6. [Codex-Konfiguration](#codex-konfiguration)
7. [Snapshot-Konfiguration](#snapshot-konfiguration)
8. [Prompt-Templates](#prompt-templates)
9. [Beispiele](#beispiele)

---

## Übersicht

Die Konfiguration besteht aus zwei Teilen:

1. **Hauptkonfiguration** (`<family>_main.json`) - Definiert die Pipeline und globale Einstellungen
2. **Rollen-Dateien** (`roles/<role>.json`) - Definieren einzelne Agent-Rollen

```
agent_families/
├── developer_main.json          # Hauptkonfiguration
├── designer_main.json
├── docs_main.json
└── developer_agents/             # Rollen-Definitionen
    ├── architect.json
    ├── implementer.json
    └── ...
```

---

## Hauptkonfiguration

### Minimale Konfiguration

```json
{
  "roles": [
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json"
    }
  ]
}
```

### Vollständige Struktur

```json
{
  "system_rules": "Du bist ein hilfreicher Coding-Assistent...",
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  },
  "snapshot": {
    "max_files": 500,
    "max_file_bytes": 100000,
    "include_patterns": ["**/*.py", "**/*.json"],
    "exclude_patterns": ["**/__pycache__/**", "**/*.pyc"]
  },
  "role_defaults": {
    "timeout_sec": 1800,
    "instances": 1,
    "shard_mode": "none",
    "overlap_policy": "warn",
    "enforce_allowed_paths": false,
    "max_files_per_shard": 10,
    "max_diff_lines_per_shard": 500,
    "reshard_on_timeout_124": true,
    "max_reshard_depth": 2
  },
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "instances": 1,
      "timeout_sec": 1800,
      "depends_on": [],
      "apply_diff": false
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 3,
      "timeout_sec": 3600,
      "depends_on": ["architect"],
      "apply_diff": true,
      "shard_mode": "headings",
      "overlap_policy": "warn",
      "enforce_allowed_paths": false
    }
  ],
  "final_role_id": "integrator"
}
```

### Top-Level Felder

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `system_rules` | string | `""` | Globale System-Anweisungen für alle Agenten |
| `codex` | object | `{}` | Codex CLI Konfiguration |
| `snapshot` | object | `{}` | Workspace-Snapshot Konfiguration |
| `role_defaults` | object | `{}` | Default-Werte für alle Rollen |
| `roles` | array | **required** | Liste der Rollen in der Pipeline |
| `final_role_id` | string | `null` | ID der finalen Rolle (für Summary) |

---

## Rollen-Konfiguration

### Rollen-Eintrag in `roles` Array

```json
{
  "id": "implementer",
  "file": "developer_agents/implementer.json",
  "instances": 3,
  "timeout_sec": 3600,
  "depends_on": ["architect"],
  "apply_diff": true,
  "shard_mode": "headings",
  "overlap_policy": "warn",
  "enforce_allowed_paths": false,
  "max_files_per_shard": 10,
  "max_diff_lines_per_shard": 500,
  "reshard_on_timeout_124": true,
  "max_reshard_depth": 2
}
```

### Basis-Felder

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `id` | string | **required** | Eindeutige Rollen-ID |
| `file` | string | **required** | Pfad zur Rollen-JSON (relativ zu Config) |
| `instances` | int | `1` | Anzahl paralleler Instanzen |
| `timeout_sec` | int | `1800` | Timeout pro Instanz (Sekunden) |
| `depends_on` | array | `[]` | IDs der Vorgänger-Rollen |
| `apply_diff` | bool | `false` | Automatisches Diff-Anwenden aktivieren |

### Sharding-Felder

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `shard_mode` | string | `"none"` | Sharding-Modus: `none`, `headings`, `files`, `llm` |
| `shard_count` | int | `null` | Explizite Shard-Anzahl (wenn ungleich `instances`) |
| `overlap_policy` | string | `"warn"` | Overlap-Verhalten: `forbid`, `warn`, `allow` |
| `enforce_allowed_paths` | bool | `false` | Erzwingt, dass Instanzen nur erlaubte Pfade ändern |
| `max_files_per_shard` | int | `10` | Max. Dateien pro Shard |
| `max_diff_lines_per_shard` | int | `500` | Max. Diff-Zeilen pro Shard |
| `reshard_on_timeout_124` | bool | `true` | Re-Sharding bei Timeout 124 (Phase 2) |
| `max_reshard_depth` | int | `2` | Max. Re-Sharding Tiefe (Phase 2) |

---

## Sharding-Optionen

### `shard_mode`

Bestimmt, wie Tasks aufgeteilt werden:

**`"none"` (Default)** - Ensemble-Modus
```json
{
  "shard_mode": "none",
  "instances": 3
}
```
→ Alle 3 Instanzen bekommen denselben Task (für Voting/Varianten)

**`"headings"` - Heading-basiert**
```json
{
  "shard_mode": "headings",
  "instances": 3
}
```
→ Task wird an H1-Headings (`# Title`) aufgeteilt

**`"files"` - Datei-basiert**
```json
{
  "shard_mode": "files",
  "instances": 3
}
```
→ Task wird anhand erwähnter Dateipfade aufgeteilt (mit Fallback zu `headings`)

**`"llm"` - LLM-basiert (Phase 2)**
```json
{
  "shard_mode": "llm",
  "instances": 3
}
```
→ LLM entscheidet, wie aufgeteilt wird (noch nicht implementiert)

### `overlap_policy`

Bestimmt, was bei Datei-Overlaps passiert:

**`"forbid"` - Abort bei Overlap**
```json
{
  "overlap_policy": "forbid"
}
```
→ Pipeline stoppt sofort, wenn 2 Instanzen dieselbe Datei ändern

**`"warn"` (Default) - Warnung bei Overlap**
```json
{
  "overlap_policy": "warn"
}
```
→ Pipeline läuft weiter, Overlap-Report wird erstellt

**`"allow"` - Overlaps erlaubt**
```json
{
  "overlap_policy": "allow"
}
```
→ Keine Overlap-Prüfung

### `enforce_allowed_paths`

Erzwingt, dass Instanzen nur ihre erlaubten Pfade ändern:

```json
{
  "enforce_allowed_paths": true
}
```

**Beispiel:**
```markdown
# Feature A
## Allowed paths
- app/auth/jwt.py
- app/auth/tokens.py
```

Wenn Instanz #1 `app/utils/helper.py` ändert:
- `enforce_allowed_paths: true` → Pipeline stoppt
- `enforce_allowed_paths: false` → Warnung, Pipeline läuft weiter

---

## System-Regeln

Globale Anweisungen, die an alle Agenten übergeben werden:

```json
{
  "system_rules": "Du bist ein erfahrener Software-Entwickler.\n\nPrinzipien:\n- Schreibe sauberen, gut dokumentierten Code\n- Folge Python Best Practices (PEP 8)\n- Nutze Type Hints\n- Schreibe aussagekräftige Commit-Messages\n\nOutput-Format:\n- Verwende immer unified diff format (git diff)\n- Markiere Diffs klar mit ```diff Blöcken"
}
```

### Best Practices

1. **Klare Erwartungen setzen**
   ```json
   "system_rules": "Du bist ein {ROLE}. Deine Aufgabe ist {TASK}."
   ```

2. **Output-Format definieren**
   ```json
   "system_rules": "Output-Format:\n- Code als unified diff\n- Zusammenfassung in Markdown"
   ```

3. **Coding-Standards festlegen**
   ```json
   "system_rules": "Code-Standards:\n- Python 3.10+\n- Type Hints erforderlich\n- Max. 100 Zeichen pro Zeile"
   ```

---

## Codex-Konfiguration

Konfiguration für das Codex CLI Tool:

```json
{
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex"
  }
}
```

### Felder

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `env_var` | string | `"CODEX_CMD"` | Umgebungsvariable für Codex-Pfad |
| `default_cmd` | string | `"codex"` | Fallback-Kommando wenn ENV nicht gesetzt |

### Verwendung

**Scenario 1: Codex im PATH**
```bash
# Keine Konfiguration nötig
which codex  # → /usr/local/bin/codex
```

**Scenario 2: Custom Pfad via ENV**
```bash
export CODEX_CMD="/opt/codex/bin/codex"
```

**Scenario 3: Custom Pfad in Config**
```json
{
  "codex": {
    "default_cmd": "/opt/codex/bin/codex"
  }
}
```

---

## Snapshot-Konfiguration

Konfiguration für den Workspace-Snapshot:

```json
{
  "snapshot": {
    "max_files": 500,
    "max_file_bytes": 100000,
    "include_patterns": [
      "**/*.py",
      "**/*.json",
      "**/*.md",
      "**/*.yaml",
      "**/*.yml"
    ],
    "exclude_patterns": [
      "**/__pycache__/**",
      "**/*.pyc",
      "**/.git/**",
      "**/node_modules/**",
      "**/.venv/**"
    ]
  }
}
```

### Felder

| Feld | Typ | Default | Beschreibung |
|------|-----|---------|--------------|
| `max_files` | int | `500` | Max. Anzahl Dateien im Snapshot |
| `max_file_bytes` | int | `100000` | Max. Größe pro Datei (Bytes) |
| `include_patterns` | array | `["**/*"]` | Glob-Patterns für einzuschließende Dateien |
| `exclude_patterns` | array | `[]` | Glob-Patterns für auszuschließende Dateien |

### Command-Line Override

Diese Werte können per CLI überschrieben werden:

```bash
python multi_agent_codex.py \
  --task "..." \
  --max-files 1000 \
  --max-file-bytes 200000
```

---

## Prompt-Templates

### Rollen-Datei (`roles/<role>.json`)

```json
{
  "id": "implementer",
  "name": "Code Implementer",
  "role": "Software Developer",
  "prompt_template": "# AUFGABE\n{task}\n\n# ARCHITEKTUR\n{architect_summary}\n\n# WORKSPACE\n{snapshot}\n\n# ANWEISUNGEN\nImplementiere die Aufgabe als unified diff."
}
```

### Verfügbare Platzhalter

| Platzhalter | Beschreibung | Verfügbar ab |
|-------------|--------------|--------------|
| `{task}` | Die Aufgabenstellung | Immer |
| `{snapshot}` | Workspace-Snapshot | Immer |
| `{role_instance_id}` | Instanz-Nummer (1, 2, 3, ...) | Bei `instances > 1` |
| `{shard_id}` | Shard-ID (z.B. "shard-1") | Bei Sharding |
| `{shard_title}` | Shard-Titel (z.B. "Feature A") | Bei Sharding |
| `{shard_goal}` | Shard-Ziel (aus `## Goal`) | Bei Sharding |
| `{allowed_paths}` | Erlaubte Pfade (kommasepariert) | Bei Sharding |
| `{architect_summary}` | Kurz-Output des Architects | Nach Architect-Rolle |
| `{architect_output}` | Voller Output des Architects | Nach Architect-Rolle |
| `{implementer_output}` | Voller Output des Implementers | Nach Implementer-Rolle |
| `{<role_id>_summary}` | Kurz-Output einer beliebigen Rolle | Nach entsprechender Rolle |
| `{<role_id>_output}` | Voller Output einer beliebigen Rolle | Nach entsprechender Rolle |

### Beispiel: Sharding-aware Prompt

```json
{
  "prompt_template": "# SHARD: {shard_title}\n\n## GOAL\n{shard_goal}\n\n## TASK\n{task}\n\n## ALLOWED PATHS\nDu darfst NUR diese Dateien ändern:\n{allowed_paths}\n\n## WORKSPACE\n{snapshot}\n\n## ANWEISUNGEN\n- Implementiere NUR deinen Shard ({shard_title})\n- Ändere NUR Dateien aus den Allowed Paths\n- Output als unified diff"
}
```

---

## Beispiele

### Beispiel 1: Einfache Pipeline

**Developer-Pipeline ohne Sharding:**

```json
{
  "system_rules": "Du bist ein Python-Entwickler. Schreibe sauberen Code mit Type Hints.",
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json"
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "depends_on": ["architect"],
      "apply_diff": true
    },
    {
      "id": "tester",
      "file": "developer_agents/tester.json",
      "depends_on": ["implementer"]
    }
  ],
  "final_role_id": "tester"
}
```

**Execution:**
```
architect → implementer (applies diff) → tester
```

---

### Beispiel 2: Sharding mit Overlap-Detection

**Parallele Implementierung mit strikter Validation:**

```json
{
  "role_defaults": {
    "timeout_sec": 3600,
    "shard_mode": "none",
    "overlap_policy": "warn"
  },
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json"
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 3,
      "shard_mode": "headings",
      "overlap_policy": "forbid",
      "enforce_allowed_paths": true,
      "depends_on": ["architect"],
      "apply_diff": true
    },
    {
      "id": "reviewer",
      "file": "developer_agents/reviewer.json",
      "instances": 2,
      "shard_mode": "none",
      "depends_on": ["implementer"]
    }
  ]
}
```

**Execution:**
```
architect
   ↓
implementer (3 parallel instances, strict validation)
   ↓
reviewer (2 instances in ensemble mode)
```

---

### Beispiel 3: Multi-Family Pipeline

**Designer + Developer kombiniert:**

```json
{
  "roles": [
    {
      "id": "ui_designer",
      "file": "designer_agents/ui_designer.json",
      "instances": 2,
      "shard_mode": "headings"
    },
    {
      "id": "ui_implementer",
      "file": "developer_agents/implementer.json",
      "depends_on": ["ui_designer"],
      "instances": 2,
      "shard_mode": "headings",
      "apply_diff": true
    },
    {
      "id": "ux_reviewer",
      "file": "designer_agents/ux_reviewer.json",
      "depends_on": ["ui_implementer"]
    }
  ]
}
```

**Use Case:** Design → Implementierung → Review in einer Pipeline

---

### Beispiel 4: Custom Snapshot Config

**Große Codebase mit selektivem Snapshot:**

```json
{
  "snapshot": {
    "max_files": 1000,
    "max_file_bytes": 200000,
    "include_patterns": [
      "src/**/*.py",
      "tests/**/*.py",
      "*.md",
      "pyproject.toml"
    ],
    "exclude_patterns": [
      "**/__pycache__/**",
      "**/*.pyc",
      "**/node_modules/**",
      "**/.venv/**",
      "**/build/**",
      "**/dist/**"
    ]
  },
  "roles": [...]
}
```

---

### Beispiel 5: Timeout-Strategie

**Verschiedene Timeouts pro Rolle:**

```json
{
  "role_defaults": {
    "timeout_sec": 1800
  },
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "timeout_sec": 1200
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "timeout_sec": 3600,
      "instances": 3
    },
    {
      "id": "tester",
      "file": "developer_agents/tester.json",
      "timeout_sec": 2400
    }
  ]
}
```

**Timeouts:**
- Architect: 20 Minuten (schnelle Planung)
- Implementer: 60 Minuten (komplexe Implementierung)
- Tester: 40 Minuten (Test-Erstellung)

---

## Weitere Ressourcen

- 📖 [Sharding-Dokumentation](SHARDING.md) - Vollständiger Sharding-Guide
- 🤝 [Eigene Rollen erstellen](CUSTOM_ROLES.md) - Wie du eigene Agenten erstellst
- 📁 [Beispiele](../examples/) - Fertige Configs zum Testen
- 📚 [Hauptdokumentation](../README.md) - Zurück zur Übersicht
