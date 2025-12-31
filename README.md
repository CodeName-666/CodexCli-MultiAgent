# Multi-Agent Codex CLI Orchestrator

Ein Python-basiertes Framework zur Orchestrierung von spezialisierten KI-Agenten für Software-Entwicklung, Design, Dokumentation und mehr.

---

## 🚀 Quick Start

```bash
# Installation
git clone <repo>
cd <repo>

# Einfacher Lauf (nur Analyse, keine Änderungen)
python multi_agent_codex.py --task "Implementiere User-Login"

# Mit automatischer Code-Anwendung
python multi_agent_codex.py --task "Implementiere User-Login" --apply
```

**Das war's!** Die Agenten analysieren deinen Code, erstellen einen Plan und implementieren die Lösung.

---

## 📚 Dokumentation

**Neu hier? Starte mit diesen Guides:**

- **[Quick Start Guide](docs/QUICKSTART.md)** ← **Starte hier!** Eigene Konfiguration in 5 Minuten
- **[Vollständige Konfiguration](docs/CONFIGURATION.md)** - Referenz aller Config-Optionen
- **[Eigene Rollen erstellen](docs/CUSTOM_ROLES.md)** - Custom Agent-Rollen schreiben
- **[Sharding (Parallelisierung)](docs/SHARDING.md)** - Echte parallele Agent-Ausführung

**Beispiele:**
- [Beispiel-Configs](examples/) - Fertige Konfigurationen zum Kopieren
- [Minimal Template](examples/minimal_template.json) - Absolutes Minimum zum Starten

---

## 📖 Inhaltsverzeichnis

1. [Was macht dieses Tool?](#was-macht-dieses-tool)
2. [Grundkonzepte](#grundkonzepte)
3. [Installation & Voraussetzungen](#installation--voraussetzungen)
4. [Verwendung](#verwendung)
5. [Neue Features: Sharding](#neue-features-sharding-v10)
6. [Konfiguration](#konfiguration)
7. [Rollen-Familien](#rollen-familien)
8. [Command-Line Optionen](#command-line-optionen)
9. [Troubleshooting](#troubleshooting)

---

## Was macht dieses Tool?

Dieses System koordiniert **mehrere spezialisierte KI-Agenten**, die zusammenarbeiten, um Software-Aufgaben zu lösen:

```
Task: "Füge User-Authentifizierung hinzu"
    ↓
┌─────────────┐
│  Architect  │ → Plant die Architektur
└─────────────┘
    ↓
┌─────────────┐
│ Implementer │ → Schreibt den Code (als Diff)
└─────────────┘
    ↓
┌─────────────┐
│   Tester    │ → Erstellt Tests
└─────────────┘
    ↓
┌─────────────┐
│  Reviewer   │ → Reviewed den Code
└─────────────┘
    ↓
┌─────────────┐
│ Integrator  │ → Fasst alles zusammen
└─────────────┘
```

**Ergebnis:** Vollständige Implementierung inkl. Tests, dokumentiert und reviewed.

---

## Grundkonzepte

### 1. **Rollen-Familien**
Vordefinierte Agent-Teams für verschiedene Aufgaben:
- **developer** - Software-Entwicklung (Architect → Implementer → Tester → Reviewer)
- **designer** - UI/UX Design (UI-Architect → Designer → Implementer → Reviewer)
- **docs** - Dokumentation (Technical Writer → Tutorial Builder → Reviewer)
- **qa** - Testing (Test Strategist → Test Author → Bug Triager)
- **devops** - Infrastructure (Infra Architect → Pipeline Implementer)
- **security** - Security Audits (Threat Modeler → Security Reviewer)
- Weitere: `product`, `data`, `research`

### 2. **Tasks: Inline vs. Datei**

**Inline** (kurze Aufgaben):
```bash
python multi_agent_codex.py --task "Füge Logging hinzu"
```

**Aus Datei** (längere Aufgaben):
```bash
python multi_agent_codex.py --task "@tasks/feature.md"
```
> `@pfad` lädt den Task aus einer Datei (du erstellst die Datei selbst)

### 3. **Outputs**
Alle Agent-Ergebnisse landen in `.multi_agent_runs/<timestamp>/`:
```
.multi_agent_runs/2025-12-31_10-30-45/
├── snapshot.txt          # Workspace-Snapshot
├── architect_1.md        # Architect Output
├── implementer_1.md      # Implementer Output (inkl. Diff)
├── tester_1.md           # Tester Output
├── reviewer_1.md         # Reviewer Output
└── integrator_1.md       # Finale Zusammenfassung
```

### 4. **Diff-Anwendung**
```bash
# Nur Analyse (Dry-Run, sicher)
python multi_agent_codex.py --task "..."

# Mit Code-Anwendung (Änderungen am Workspace)
python multi_agent_codex.py --task "..." --apply

# Mit Bestätigung vor jeder Änderung
python multi_agent_codex.py --task "..." --apply --apply-confirm
```

---

## Installation & Voraussetzungen

### Voraussetzungen
- **Python 3.10+**
- **Codex CLI** im PATH (Claude CLI oder ähnlich)
- Optional: **Git** (für besseres Diff-Handling)

### Installation
```bash
git clone <repo>
cd <repo>

# Konfiguration prüfen (optional)
python multi_agent_codex.py --help
```

Keine weiteren Dependencies nötig – nutzt nur Python Standard Library!

---

## Verwendung

### Basis-Workflow

#### Schritt 1: Task definieren
```bash
# Kurz: Direkt im Terminal
python multi_agent_codex.py --task "Implementiere User-Login mit JWT"

# Lang: Als Datei
echo "# User Login\n## Ziel\nJWT-basierte Authentifizierung..." > tasks/login.md
python multi_agent_codex.py --task "@tasks/login.md"
```

#### Schritt 2: Agenten arbeiten
Das System:
1. Erstellt Workspace-Snapshot
2. Startet Agenten sequenziell (Architect → Implementer → ...)
3. Jeder Agent sieht Outputs der vorherigen Agenten
4. Speichert alle Ergebnisse in `.multi_agent_runs/`

#### Schritt 3: Ergebnisse anwenden
```bash
# Prüfen der generierten Diffs
cat .multi_agent_runs/<timestamp>/implementer_1.md

# Diffs anwenden
python multi_agent_codex.py --task "@tasks/login.md" --apply
```

### Verschiedene Familien nutzen

```bash
# Developer (Standard)
python multi_agent_codex.py --task "..."

# Designer für UI-Aufgaben
python multi_agent_codex.py \
  --config config/designer_main.json \
  --task "Redesigne Dashboard"

# Docs für Dokumentation
python multi_agent_codex.py \
  --config config/docs_main.json \
  --task "Schreibe API-Dokumentation"
```

---

## Neue Features: Sharding (V1.0)

### 🎯 Was ist Sharding?

**Vorher (Ensemble-Modus):**
```
Task: "Implementiere Features A, B, C"
├─ Implementer #1 → Bekommt kompletten Task
├─ Implementer #2 → Bekommt kompletten Task
└─ Implementer #3 → Bekommt kompletten Task
   → Alle arbeiten redundant
```

**Jetzt (Sharding-Modus):**
```
Task: "# Feature A\n...\n# Feature B\n...\n# Feature C\n..."
├─ Implementer #1 → Bekommt nur Feature A
├─ Implementer #2 → Bekommt nur Feature B
└─ Implementer #3 → Bekommt nur Feature C
   → Echte parallele Arbeit, kein Waste!
```

### Quick Start Sharding

**1. Task mit Headings strukturieren:**
```markdown
# Feature A: User Authentication
Implementiere JWT-basierte Authentifizierung...

# Feature B: Database Schema
Erstelle User- und Session-Models...

# Feature C: API Endpoints
Implementiere /login und /logout...
```

**2. Sharding in Config aktivieren:**
```json
{
  "roles": [{
    "id": "implementer",
    "instances": 3,
    "shard_mode": "headings"
  }]
}
```

**3. Ausführen:**
```bash
python multi_agent_codex.py \
  --config examples/sharding_basic_config.json \
  --task "@examples/task_three_features.md"
```

**Ergebnis:** 3 Implementer arbeiten parallel an 3 Features!

### Sharding Config-Optionen

| Option | Typ | Default | Beschreibung |
|--------|-----|---------|--------------|
| `shard_mode` | string | `"none"` | `none` = Ensemble, `headings` = H1-basiert, `files` = Pfad-basiert |
| `instances` | int | 1 | Anzahl paralleler Instanzen |
| `overlap_policy` | string | `"warn"` | `forbid` = Abort bei Overlap, `warn` = Continue, `allow` = Keine Prüfung |
| `enforce_allowed_paths` | bool | false | Erzwingt, dass Instanzen nur definierte Dateien ändern |

### Wann Sharding nutzen?

✅ **Sharding sinnvoll:**
- Mehrere unabhängige Features
- Klar abgegrenzte Aufgaben
- Zeitkritische Projekte (→ Speedup)

❌ **Ensemble besser:**
- Kleine, einzelne Tasks
- Kreative/explorative Aufgaben (mehrere Ansätze gewünscht)
- Code-Review (mehrere Meinungen gewünscht)

📖 **[Vollständige Sharding-Dokumentation](docs/SHARDING.md)**
📁 **[Beispiele mit Sharding](examples/)**

---

## Konfiguration

> **💡 Tipp:** Für eine detaillierte Anleitung zum Erstellen eigener Configs, siehe [Quick Start Guide](docs/QUICKSTART.md)

### Struktur

```
config/
├── developer_main.json          # Developer-Pipeline
├── designer_main.json           # UI/UX-Pipeline
├── docs_main.json               # Dokumentations-Pipeline
├── developer_roles/
│   ├── architect.json
│   ├── implementer.json
│   ├── tester.json
│   └── ...
└── designer_roles/
    ├── ui_designer.json
    └── ...
```

### Hauptkonfiguration (`<family>_main.json`)

**Minimal-Beispiel:**
```json
{
  "system_rules": "Du bist ein hilfreicher Coding-Assistent...",
  "roles": [
    {
      "id": "implementer",
      "file": "developer_roles/implementer.json",
      "instances": 1,
      "apply_diff": true
    }
  ],
  "final_role_id": "implementer"
}
```

**Mit Sharding:**
```json
{
  "role_defaults": {
    "shard_mode": "none",
    "overlap_policy": "warn"
  },
  "roles": [
    {
      "id": "implementer",
      "file": "developer_roles/implementer.json",
      "instances": 3,
      "shard_mode": "headings",
      "apply_diff": true
    }
  ]
}
```

### Rollen-Datei (`roles/<role>.json`)

```json
{
  "id": "implementer",
  "name": "Implementer",
  "role": "Code Implementer",
  "prompt_template": "AUFGABE:\n{task}\n\nARCHITEKTUR:\n{architect_summary}\n\nSNAPSHOT:\n{snapshot}\n"
}
```

**Verfügbare Platzhalter:**
- `{task}` - Die Aufgabenstellung
- `{snapshot}` - Workspace-Snapshot
- `{architect_summary}` - Kurz-Output des Architects
- `{implementer_output}` - Voller Output des Implementers
- `{role_instance_id}` - Instanz-Nummer (bei Parallelisierung)
- `{shard_title}` - Shard-Titel (bei Sharding)
- `{allowed_paths}` - Erlaubte Pfade (bei Sharding)

📖 **Mehr Details:** [Vollständige Konfigurationsreferenz](docs/CONFIGURATION.md) | [Eigene Rollen erstellen](docs/CUSTOM_ROLES.md)

---

## Rollen-Familien

### Developer (Software-Entwicklung)

**Rollen:**
- `architect` - Architektur & Design
- `implementer` - Code-Implementierung
- `tester` - Test-Erstellung
- `reviewer` - Code-Review
- `integrator` - Finale Zusammenfassung

**Verwendung:**
```bash
python multi_agent_codex.py --task "Implementiere Feature X"
```

---

### Designer (UI/UX)

**Rollen:**
- `ui_architect` - Informationsarchitektur
- `ui_designer` - Design-Konzept
- `ui_implementer` - UI-Code
- `ux_reviewer` - UX-Review

**Verwendung:**
```bash
python multi_agent_codex.py \
  --config config/designer_main.json \
  --task "Erstelle Login-Formular"
```

---

### Docs (Dokumentation)

**Rollen:**
- `technical_writer` - Technische Dokumentation
- `tutorial_builder` - Tutorials
- `docs_reviewer` - Review

**Verwendung:**
```bash
python multi_agent_codex.py \
  --config config/docs_main.json \
  --task "Dokumentiere die API"
```

---

### QA (Testing)

**Rollen:**
- `test_strategist` - Teststrategie
- `test_author` - Testfall-Erstellung
- `bug_triager` - Bug-Priorisierung

**Verwendung:**
```bash
python multi_agent_codex.py \
  --config config/qa_main.json \
  --task "Erstelle Testplan für Feature X"
```

---

### Weitere Familien

- **DevOps** - Infrastructure & CI/CD
- **Security** - Security Audits & Threat Modeling
- **Data** - Data Pipelines & ML
- **Product** - Requirements & User Stories
- **Research** - User Research & Analyse

[Vollständige Übersicht aller Familien](docs/FAMILIES.md)

---

## Command-Line Optionen

### Haupt-Optionen

```bash
python multi_agent_codex.py [OPTIONEN]
```

| Option | Beschreibung | Beispiel |
|--------|--------------|----------|
| `--task` | Aufgabe (inline oder `@datei`) | `--task "Füge Login hinzu"` |
| `--config` | Config-Datei | `--config config/designer_main.json` |
| `--dir` | Arbeitsverzeichnis | `--dir /path/to/project` |
| `--apply` | Diffs anwenden | `--apply` |
| `--apply-confirm` | Vor jedem Diff fragen | `--apply-confirm` |
| `--timeout` | Timeout pro Agent (Sekunden) | `--timeout 3600` |

### Erweiterte Optionen

| Option | Beschreibung |
|--------|--------------|
| `--apply-mode` | Wann Diffs anwenden: `end` (nach allen) oder `role` (nach jeder Rolle) |
| `--apply-roles` | Nur bestimmte Rollen anwenden (kommasepariert) |
| `--fail-fast` | Bei Fehler sofort abbrechen |
| `--ignore-fail` | Exitcode immer 0 |
| `--task-split` | Task in mehrere Runs aufteilen |
| `--max-files` | Max. Dateien im Snapshot |
| `--max-file-bytes` | Max. Größe pro Datei im Snapshot |

### Beispiele

```bash
# Standard-Lauf
python multi_agent_codex.py --task "Implementiere Feature X"

# Mit Diff-Anwendung
python multi_agent_codex.py --task "..." --apply

# Mit Bestätigung
python multi_agent_codex.py --task "..." --apply --apply-confirm

# Designer-Familie mit Sharding
python multi_agent_codex.py \
  --config examples/designer_sharding_config.json \
  --task "@examples/designer_task_ui_components.md"

# Nur bestimmte Rollen anwenden
python multi_agent_codex.py \
  --task "..." \
  --apply \
  --apply-roles implementer,tester
```

---

## Troubleshooting

### Problem: "Codex CLI nicht gefunden"

**Ursache:** `codex` ist nicht im PATH

**Lösung:**
```bash
# Option 1: Codex CLI zum PATH hinzufügen
export PATH="$PATH:/pfad/zu/codex"

# Option 2: In Config setzen
{
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "/pfad/zu/codex"
  }
}
```

---

### Problem: "Kein Diff gefunden"

**Ursache:** Agent hat keinen validen Diff generiert

**Lösung:**
1. Prüfe Agent-Output: `cat .multi_agent_runs/<timestamp>/implementer_1.md`
2. Suche nach `diff --git` Headers
3. Passe Prompt-Template an, falls nötig

---

### Problem: "Overlaps detected" (bei Sharding)

**Ursache:** Mehrere Instanzen haben dieselbe Datei geändert

**Lösung:**
```bash
# Option 1: Overlap-Report prüfen
cat .multi_agent_runs/<timestamp>/<role>_overlaps.json

# Option 2: Policy ändern
{
  "overlap_policy": "allow"  # Statt "forbid" oder "warn"
}

# Option 3: Task besser strukturieren
# Klarere Abgrenzung der Features in den Headings
```

---

### Problem: Agent-Output zu lang / Timeout

**Lösung:**
```bash
# Timeout erhöhen
python multi_agent_codex.py --task "..." --timeout 3600

# Oder: Snapshot kleiner machen
python multi_agent_codex.py \
  --task "..." \
  --max-files 100 \
  --max-file-bytes 50000
```

---

## Weitere Ressourcen

- 📖 **[Sharding-Dokumentation](docs/SHARDING.md)** - Vollständiger Guide zu echter Parallelität
- 📁 **[Beispiele](examples/)** - Fertige Configs und Tasks zum Testen
- 🔧 **[Erweiterte Konfiguration](docs/CONFIGURATION.md)** - Alle Config-Optionen im Detail
- 🤝 **[Eigene Rollen erstellen](docs/CUSTOM_ROLES.md)** - Wie du eigene Agenten erstellst

---

## Lizenz

MIT – Freie Nutzung auf eigene Verantwortung
