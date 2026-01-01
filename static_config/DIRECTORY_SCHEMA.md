# Directory Schema - Multi-Agent Codex CLI Orchestrator

## Übersicht

Dieses Dokument beschreibt die Verzeichnisstruktur des Multi-Agent Codex CLI Orchestrators.

## Verzeichnisstruktur

```
Codex_CLI_Agent/
├── static_config/                    # Statische Framework-Konfigurationen
│   ├── cli_config.json              # CLI-Provider Definitionen (Codex, Claude, Gemini)
│   ├── defaults.json                # Standard-Konfiguration für alle Familien
│   └── DIRECTORY_SCHEMA.md          # Diese Datei
│
├── agent_families/                   # Agent-Familien Konfigurationen (Benutzer-Configs)
│   ├── developer_main.json          # Backend-Entwicklungs-Familie
│   ├── designer_main.json           # UI/UX-Design-Familie
│   ├── data_main.json               # Data Science/ML-Familie
│   ├── devops_main.json             # DevOps/Infrastruktur-Familie
│   ├── docs_main.json               # Dokumentations-Familie
│   ├── product_main.json            # Product Management-Familie
│   ├── qa_main.json                 # QA/Testing-Familie
│   ├── research_main.json           # User Research-Familie
│   ├── security_main.json           # Security-Familie
│   │
│   ├── developer_agents/            # Agent-Definitionen für Developer-Familie
│   │   ├── architect.json
│   │   ├── implementer.json
│   │   ├── tester.json
│   │   ├── reviewer.json
│   │   ├── implementer_revision.json
│   │   └── integrator.json
│   │
│   ├── designer_agents/             # Agent-Definitionen für Designer-Familie
│   │   ├── ui_architect.json
│   │   ├── ui_designer.json
│   │   ├── ui_implementer.json
│   │   ├── ui_tester.json
│   │   ├── ui_reviewer.json
│   │   ├── ui_implementer_revision.json
│   │   └── ui_integrator.json
│   │
│   ├── data_agents/                 # Agent-Definitionen für Data-Familie
│   ├── devops_agents/               # Agent-Definitionen für DevOps-Familie
│   ├── docs_agents/                 # Agent-Definitionen für Docs-Familie
│   ├── product_agents/              # Agent-Definitionen für Product-Familie
│   ├── qa_agents/                   # Agent-Definitionen für QA-Familie
│   ├── research_agents/             # Agent-Definitionen für Research-Familie
│   └── security_agents/             # Agent-Definitionen für Security-Familie
│
├── examples/                         # Beispiel-Konfigurationen
│   ├── multi_cli_example.json       # Beispiel mit verschiedenen CLI-Providern
│   ├── minimal_template.json        # Minimale Template-Config
│   ├── sharding_basic_config.json   # Basis-Sharding-Beispiel
│   ├── sharding_advanced_config.json # Fortgeschrittenes Sharding
│   └── designer_sharding_config.json # Designer mit Sharding
│
├── multi_agent/                      # Core Python-Module
│   ├── cli_adapter.py               # CLI-Provider Adapter System
│   ├── config_loader.py             # Lädt Configs (merged defaults + family)
│   ├── pipeline.py                  # Haupt-Pipeline-Orchestrierung
│   ├── models.py                    # Datenmodelle (AppConfig, RoleConfig, etc.)
│   ├── codex.py                     # CLI-Client (unterstützt alle Provider)
│   ├── coordination.py              # Task Board für Agent-Koordination
│   ├── diff_applier.py              # Code-Diff Anwendung
│   ├── snapshot.py                  # Workspace-Snapshot Erstellung
│   ├── sharding.py                  # Parallele Task-Verteilung
│   └── ...                          # Weitere Core-Module
│
├── creators/                         # Tools zur Config-Generierung
│   ├── multi_family_creator.py      # Erstellt komplette Agent-Familien
│   ├── multi_role_agent_creator.py  # Erstellt einzelne Agent-Rollen
│   └── multi_role_agent_creator_legacy.py
│
├── docs/                             # Dokumentation
│   ├── QUICKSTART.md                # Schnellstart-Anleitung
│   ├── MULTI_CLI.md                 # Multi-CLI Provider Dokumentation
│   ├── CONFIGURATION.md             # Vollständige Config-Referenz
│   ├── FAMILY_CREATOR.md            # Family Creator Anleitung
│   ├── SHARDING.md                  # Sharding/Parallelisierung
│   ├── CUSTOM_ROLES.md              # Eigene Rollen erstellen
│   └── ROLE_CREATOR_NL.md           # Natural Language Role Creator
│
├── updates/                          # Feature-Dokumentation & Roadmap
│   ├── features/                    # Geplante Features
│   └── multi_cli_extensions/        # Multi-CLI Erweiterungs-Features
│
├── tests/                            # Unit & Integration Tests
├── .multi_agent_runs/               # Run-Outputs & Logs
└── multi_agent_codex.py             # CLI Entry Point

```

## Datei-Beschreibungen

### Static Config (`static_config/`)

**Zweck**: Framework-Level Konfigurationen, die von allen Benutzern gemeinsam genutzt werden.

#### `cli_config.json`
Definiert alle verfügbaren CLI-Provider und ihre Parameter:
- **codex**: OpenAI Codex CLI
- **claude**: Anthropic Claude Code CLI
- **gemini**: Google Gemini CLI

```json
{
  "cli_providers": {
    "codex": { "default_cmd": ["codex", "exec", "-"], ... },
    "claude": { "default_cmd": ["claude", "-p"], ... },
    "gemini": { "default_cmd": ["gemini", "-p"], ... }
  },
  "default_provider": "codex",
  "timeout_multiplier": { ... },
  "cost_tracking": { ... }
}
```

#### `defaults.json`
Standard-Werte die von allen Agent-Familien geerbt werden:
- System Rules
- Messages (Fehler-/Status-Meldungen)
- Role Defaults (Timeouts, Retries, etc.)
- Snapshot Konfiguration
- Koordinations-Settings

Agent-Familien überschreiben nur die Werte, die sie anpassen möchten.

### Agent Families (`agent_families/`)

**Zweck**: Benutzer-spezifische Agent-Familien-Konfigurationen.

#### `*_main.json` Dateien
Haupt-Konfiguration einer Agent-Familie:
- **cli**: Beschreibung der Familie
- **final_role_id**: Welcher Agent das finale Ergebnis liefert
- **diff_safety**: Welche Dateien geändert werden dürfen
- **roles**: Array von Agent-Definitionen mit:
  - `file`: Pfad zur Agent-Definition (`.json`)
  - `cli_provider`: Welcher CLI-Provider (codex, claude, gemini)
  - `model`: Welches Modell (sonnet, opus, haiku, gemini-2.5-flash, etc.)
  - `cli_parameters`: Provider-spezifische Parameter
  - `instances`: Anzahl paralleler Instanzen
  - `depends_on`: Von welchen Agents dieser abhängt

#### `*_agents/` Verzeichnisse
Enthalten die tatsächlichen Agent-Definitionen:
- `role`: Beschreibung der Rolle
- `prompt_template`: Template für den Prompt
- Jeder Agent ist wiederverwendbar und kann in mehreren Familien genutzt werden

### Examples (`examples/`)

**Zweck**: Vorlagen und Beispiele für verschiedene Use Cases.

#### `multi_cli_example.json`
Zeigt wie verschiedene Rollen verschiedene CLI-Provider nutzen:
- Architect: Claude Sonnet (komplexe Planung)
- Implementer: Codex (Code-Generierung)
- Tester: Gemini Flash (schnell & günstig)
- Integrator: Claude Haiku (einfache Zusammenfassung)

## Konfigurations-Hierarchie

```
defaults.json (static_config/)
    ↓ merged mit
*_main.json (agent_families/)
    ↓ referenziert
*_agents/*.json (agent_families/)
    ↓ verwendet
cli_config.json (static_config/)
```

### Merge-Logik

1. `defaults.json` wird geladen (alle Standard-Werte)
2. `*_main.json` wird geladen und merged (Familie-spezifische Overrides)
3. Für jede Rolle in `roles[]`:
   - Agent-Definition wird aus `*_agents/*.json` geladen
   - CLI-Provider wird aus `cli_config.json` geladen (falls `cli_provider` gesetzt)
   - Role-specific Overrides werden angewendet

**Beispiel**:
```json
// defaults.json
{
  "role_defaults": {
    "timeout_sec": 1200,
    "retries": 2
  }
}

// developer_main.json
{
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "timeout_sec": 1800,  // Override: 1800 statt 1200
      "cli_provider": "claude",
      "model": "sonnet"
      // retries wird von defaults geerbt (2)
    }
  ]
}
```

## CLI-Provider Strategie

Die Standard-Strategie für optimale Kosten/Qualität Balance:

| Agent-Typ | Provider | Modell | Begründung |
|-----------|----------|--------|------------|
| **Architect** | Claude | Sonnet | Komplexe Planung & Architektur |
| **Implementer/Designer** | Codex | (default) | Code-Generierung, spezialisiert |
| **Tester** | Gemini | Flash | Schnell, günstig, ausreichend |
| **Reviewer** | Claude | Opus | Höchste Qualität für Fehler-Erkennung |
| **Integrator** | Claude | Haiku | Einfache Zusammenfassungen |

**Geschätzte Kostenersparnis**: 60-70% vs. nur Opus/Sonnet

## Erweiterung

### Neue Agent-Familie erstellen

```bash
python multi_agent_codex.py create-family \
  --description "Team für X" \
  --auto-providers
```

Dies erstellt automatisch:
- `agent_families/x_main.json`
- `agent_families/x_agents/` mit generierten Agenten
- CLI-Provider werden automatisch zugewiesen

### Neue Agent-Rolle zu Familie hinzufügen

```bash
python multi_agent_codex.py create-role \
  --nl-description "Agent für Y" \
  --family developer \
  --id custom_agent
```

### Manuell Familie-Config bearbeiten

1. Öffne `agent_families/*_main.json`
2. Füge neue Rolle zu `roles[]` Array hinzu:
```json
{
  "id": "my_agent",
  "file": "developer_agents/my_agent.json",
  "cli_provider": "claude",
  "model": "sonnet",
  "instances": 1,
  "depends_on": ["architect"]
}
```
3. Erstelle `agent_families/developer_agents/my_agent.json` mit Agent-Definition

## Best Practices

### ✅ DO
- **Nutze `defaults.json`** für gemeinsame Einstellungen
- **Nutze CLI-Provider strategisch** (siehe Tabelle oben)
- **Teste neue Configs** mit `--dry-run` Flag
- **Versioniere** deine `agent_families/` Configs in Git
- **Dokumentiere** Custom-Agents in den Agent-Dateien

### ❌ DON'T
- **Ändere niemals** `static_config/` Dateien (außer bei Framework-Updates)
- **Dupliziere nicht** Settings die in `defaults.json` stehen
- **Hardcode nicht** Pfade - nutze relative Pfade
- **Mische nicht** verschiedene Families in einem Run

## Migration

### Von alter `config/` Struktur

Die Struktur wurde umbenannt für klarere Semantik:
- `config/` → `agent_families/`
- `*_roles/` → `*_agents/`
- `config/defaults.json` → `static_config/defaults.json`
- `config/cli_config.json` → `static_config/cli_config.json`

Alle Pfad-Referenzen wurden automatisch aktualisiert.

## Weitere Dokumentation

- [Quick Start Guide](../docs/QUICKSTART.md)
- [Multi-CLI Support](../docs/MULTI_CLI.md)
- [Configuration Reference](../docs/CONFIGURATION.md)
- [Family Creator](../docs/FAMILY_CREATOR.md)

---

**Letzte Aktualisierung**: 2025-01-01
**Version**: 2.0 (Multi-CLI Support)
