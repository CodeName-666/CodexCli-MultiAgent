# Family Creator: Automatische Agent-Familien-Generierung

Ein Tool zur automatischen Erstellung vollständiger Agent-Familien aus natürlicher Sprache, powered by Codex CLI.

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Modi](#modi)
5. [CLI-Referenz](#cli-referenz)
6. [Beispiele](#beispiele)
7. [Workflow](#workflow)
8. [Troubleshooting](#troubleshooting)

---

## Überblick

Der **Family Creator** (`multi_family_creator.py`) automatisiert die Erstellung kompletter Agent-Familien. Statt manuell 5-7 JSON-Dateien zu schreiben, beschreibst du einfach die Familie in natürlicher Sprache, und Codex CLI generiert:

- **Hauptkonfiguration** (`<family>_main.json`) - Nur family-spezifische Werte (nutzt `defaults.json`)
- **Alle Rollen-Dateien** (`<family>_roles/*.json`)
- **Prompt-Templates** für jede Rolle
- **Dependencies** zwischen Rollen
- **Expected-Sections** für Output-Validierung

**NEU:** Family-Configs sind jetzt ~80% kleiner, da globale Einstellungen automatisch aus `config/defaults.json` geladen werden.

### Was wird generiert?

```
config/
├── ml_team_main.json              # Haupt-Konfiguration
└── ml_team_roles/                 # Rollen-Verzeichnis
    ├── data_analyst.json          # Analysiert Daten
    ├── feature_engineer.json      # Erstellt Features
    ├── model_trainer.json         # Trainiert Modelle
    ├── evaluator.json             # Evaluiert Performance
    └── ml_integrator.json         # Integriert alles
```

Jede Familie kann sofort verwendet werden:
```bash
python -m multi_agent.cli \
  --config config/ml_team_main.json \
  --task "Entwickle Churn Prediction Model"
```

---

## Quick Start

### Installation

Keine zusätzliche Installation nötig - nutzt Python Standard Library + Codex CLI.

### Einfachste Verwendung

```bash
# Via Haupt-CLI (empfohlen)
python multi_agent_codex.py create-family \
  --description "Ein Team für Machine Learning: Daten-Analyse, Feature Engineering, Model Training, Evaluation"

# ODER direkt/eigenständig
python creators/multi_family_creator.py \
  --description "Ein Team für Machine Learning: Daten-Analyse, Feature Engineering, Model Training, Evaluation"
```

> **Hinweis:** Beide Aufrufe sind funktional identisch. Das Haupt-CLI bietet eine einheitlichere Schnittstelle.

**Output:**
```
Generiere Familie-Spezifikation via Codex...
Generiere Prompt-Templates für Rollen...
  Generiere Template: data_analyst...
  Generiere Template: feature_engineer...
  Generiere Template: model_trainer...
  Generiere Template: evaluator...
  Generiere Template: ml_integrator...
Schreibe Familie-Konfiguration...

✓ Familie erstellt: ml_team
  Haupt-Config: config/ml_team_main.json
  Rollen-Dir:   config/ml_team_roles/
```

### Mit Optimierung

```bash
# Via Haupt-CLI
python multi_agent_codex.py create-family \
  --description "Backend API Team mit GraphQL, Testing und Deployment" \
  --optimize-roles \
  --interactive

# ODER direkt
python creators/multi_family_creator.py \
  --description "Backend API Team mit GraphQL, Testing und Deployment" \
  --optimize-roles \
  --interactive
```

Dies:
1. Generiert Familie-Spec via Codex
2. Öffnet Editor für manuelle Review
3. Optimiert Rollen-Beschreibungen via Codex
4. Generiert optimierte Prompt-Templates
5. Schreibt alle Dateien

---

## Features

### 🤖 Codex-Assistiert

- **Familie-Spec-Generierung**: Codex erstellt strukturierte JSON-Spec aus Beschreibung
- **Prompt-Template-Generierung**: Codex generiert optimale Prompts für jede Rolle
- **Description-Optimierung**: Optional Beschreibungen optimieren lassen

### 📋 Template-Modi

- **Scratch**: Komplett neu von Codex generieren
- **Clone**: Existierende Familie 1:1 kopieren und anpassen
- **Inspire**: Existierende Familie als Inspiration nutzen

### ✅ Validierung

- **Dependency-Zyklus-Erkennung**: DFS-basierte Zyklus-Prüfung
- **Struktur-Validierung**: Alle Required-Fields werden geprüft
- **Role-ID-Uniqueness**: Keine Duplikate erlaubt

### 🔧 Flexibilität

- **Dry-Run Mode**: Spec anzeigen ohne Dateien zu schreiben
- **Interactive Mode**: Manuelle Review vor Dateischreiben
- **Force Mode**: Existierende Familien überschreiben
- **Multi-Language**: Deutsche und englische Prompts

---

## Modi

### 1. Scratch Mode (Default)

Erstelle Familie komplett neu von Codex.

```bash
# Via Haupt-CLI
python multi_agent_codex.py create-family \
  --description "Ein Team für Video Content Creation: Storyboard, Editing, Sound Design, Publishing"

# ODER direkt
python creators/multi_family_creator.py \
  --description "Ein Team für Video Content Creation: Storyboard, Editing, Sound Design, Publishing"
```

**Wann nutzen:**
- Neue, einzigartige Familie erstellen
- Kein passendes Template existiert
- Maximale Freiheit für Codex

**Codex generiert:**
- Familie-ID (z.B. `video_content_creation`)
- 4-7 Rollen basierend auf Beschreibung
- Dependencies zwischen Rollen
- System-Rules für die Familie

---

### 2. Clone Mode

Kopiere existierende Familie-Struktur 1:1 und passe an.

```bash
# Via Haupt-CLI
python multi_agent_codex.py create-family \
  --description "Backend API Team mit REST, GraphQL, Testing" \
  --template-from developer \
  --template-mode clone

# ODER direkt
python creators/multi_family_creator.py \
  --description "Backend API Team mit REST, GraphQL, Testing" \
  --template-from developer \
  --template-mode clone
```

**Wann nutzen:**
- Ähnlicher Workflow wie bestehende Familie
- Schnellere Erstellung durch Struktur-Wiederverwendung
- Konsistenz mit existierenden Familien

**Was passiert:**
1. Lädt `developer_main.json` als Template
2. Übernimmt Rollen-Anzahl und Dependencies
3. Passt Rollen-IDs und Beschreibungen an
4. Generiert neue Prompt-Templates

**Beispiel:**

Template (Developer):
```
architect → implementer → tester → reviewer → integrator
```

Wird zu (Backend API):
```
api_architect → api_implementer → api_tester → api_reviewer → api_integrator
```

---

### 3. Inspire Mode

Nutze Familie als Referenz, aber erstelle neue Struktur.

```bash
python creators/multi_family_creator.py \
  --description "Data Pipeline Team: Ingestion, Transformation, Quality Checks" \
  --template-from developer \
  --template-mode inspire
```

**Wann nutzen:**
- Grobe Orientierung an bestehender Familie
- Aber andere Rollen-Anzahl oder Struktur gewünscht
- Freiheit für Codex, aber mit Guidance

**Was passiert:**
1. Zeigt Template-Struktur an Codex als Inspiration
2. Codex generiert neue Struktur (kann abweichen!)
3. Kann mehr/weniger Rollen haben
4. Dependencies können unterschiedlich sein

---

## CLI-Referenz

### Erforderliche Argumente

| Argument | Beschreibung |
|----------|--------------|
| `--description TEXT` | Natural Language Beschreibung der Familie (**erforderlich**) |

### Familie-Metadata

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--family-id ID` | Auto-Slugify | Überschreibt automatisch generierte ID |
| `--family-name NAME` | family-id | Human-readable Name |
| `--system-rules TEXT` | Von Codex | Custom System-Regeln |

### Template-Modus

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--template-from FAMILY` | - | Basis-Familie (developer, designer, etc.) oder Pfad |
| `--template-mode MODE` | scratch | clone / inspire / scratch |

### Codex-Kontrolle

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--codex-cmd CMD` | $CODEX_CMD | Codex CLI Command Override |
| `--codex-timeout-sec SEC` | 180 | Timeout für Codex-Aufrufe |
| `--optimize-roles` | false | Rollen-Descriptions via Codex optimieren |

### Rollen-Konfiguration

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--role-count N` | Codex entscheidet | Hint für Anzahl Rollen |
| `--include-integrator` | true | Integrator-Rolle immer dabei |
| `--apply-diff-roles LIST` | - | Komma-separierte Liste (z.B. "implementer,tester") |

### Output

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--output-dir DIR` | config | Output-Verzeichnis |
| `--dry-run` | false | Zeigt nur JSON, schreibt nichts |
| `--interactive` | false | Manuelle Review vor Schreiben |
| `--force` | false | Überschreibt existierende Familie |

### Erweitert

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--extra-instructions TEXT` | - | Zusatz-Anweisungen für Codex |
| `--lang LANG` | de | Sprache (de/en) |

---

## Beispiele

### Beispiel 1: ML Team (Scratch)

```bash
python creators/multi_family_creator.py \
  --description "Machine Learning Team: Daten-Analyse, Feature Engineering, Model Training, Evaluation, Deployment"
```

**Generierte Familie:**
- **data_analyst**: Analysiert Datasets, findet Issues
- **feature_engineer**: Erstellt Features aus Rohdaten
- **model_trainer**: Trainiert ML-Modelle
- **evaluator**: Evaluiert Model-Performance
- **ml_integrator**: Integriert alles, nächste Schritte

---

### Beispiel 2: GraphQL Backend (Clone von Developer)

```bash
python creators/multi_family_creator.py \
  --description "GraphQL Backend Team: Schema Design, Resolver Implementation, Testing, Deployment" \
  --template-from developer \
  --template-mode clone \
  --family-id graphql_backend
```

**Struktur:**
- Übernimmt Developer-Workflow (Architect → Implementer → Tester → Reviewer → Integrator)
- Passt Rollen-IDs an (graphql_architect, graphql_implementer, etc.)
- Generiert GraphQL-spezifische Prompts

---

### Beispiel 3: Video Production (Inspire von Designer)

```bash
python creators/multi_family_creator.py \
  --description "Video Content Production: Storyboard, Filming, Editing, Sound Design, Publishing" \
  --template-from designer \
  --template-mode inspire \
  --optimize-roles \
  --interactive
```

**Workflow:**
1. Codex generiert Familie basierend auf Designer-Inspiration
2. Editor öffnet sich für manuelle Review
3. Codex optimiert Rollen-Descriptions
4. Dateien werden geschrieben

---

### Beispiel 4: Security Audit (Custom Instructions)

```bash
python creators/multi_family_creator.py \
  --description "Security Audit Team für Web Applications" \
  --extra-instructions "Fokus auf OWASP Top 10, Pentesting, Compliance" \
  --role-count 5 \
  --lang en
```

**Extra-Instructions:**
- Codex berücksichtigt OWASP Top 10
- Pentesting-Fokus
- Compliance-Aspekte

---

### Beispiel 5: Dry-Run (Spec Preview)

```bash
python creators/multi_family_creator.py \
  --description "E-Commerce Platform Team" \
  --dry-run
```

**Output:**
```json
{
  "family_id": "e_commerce_platform",
  "family_name": "E-Commerce Platform Team",
  "system_rules": "...",
  "roles": [
    {
      "id": "product_architect",
      "name": "Product Architect",
      "description": "...",
      "depends_on": [],
      ...
    },
    ...
  ],
  "final_role_id": "ecommerce_integrator"
}
```

Keine Dateien werden geschrieben - nur JSON-Ausgabe.

---

## Workflow

### Interner Ablauf

```
1. [Template laden] (optional)
   ↓
2. [Familie-Spec via Codex generieren]
   - Natural Language → JSON-Spec
   - Validierung (Dependencies, Structure)
   ↓
3. [Interaktive Review] (optional)
   - Editor öffnet Spec
   - Manuelle Anpassungen
   - Re-Validierung
   ↓
4. [Dry-Run Check] (optional)
   - Zeige JSON, exit
   ↓
5. [Rollen-Descriptions optimieren] (optional --optimize-roles)
   - Für jede Rolle: Codex optimiert Description
   ↓
6. [Prompt-Templates generieren]
   - Für jede Rolle: Codex generiert Prompt-Template
   - Berücksichtigt Dependencies, apply_diff, expected_sections
   ↓
7. [Dateien schreiben]
   - <family>_main.json
   - <family>_roles/*.json
```

### Codex-Aufrufe

Der Family Creator macht **2+N Codex-Aufrufe** (N = Anzahl Rollen):

1. **Familie-Spec-Generierung** (1 Aufruf):
   - Input: Natural Language Description
   - Output: JSON mit Rollen, Dependencies, System-Rules

2. **Prompt-Template-Generierung** (N Aufrufe):
   - Input: Rollen-Spec (ID, Description, Dependencies)
   - Output: Vollständiger Prompt-Template-Text

3. **Description-Optimierung** (N Aufrufe, optional):
   - Input: Rohe Rollen-Beschreibung
   - Output: Optimierte 2-4 Sätze

**Gesamt-Runtime:**
- Ohne Optimierung: ~3-5 Minuten (abhängig von Codex-Latenz)
- Mit Optimierung: ~5-10 Minuten

---

## Troubleshooting

### Problem: "Codex CLI timeout nach 180s"

**Ursache:** Codex braucht länger als 180 Sekunden.

**Lösung:**
```bash
python creators/multi_family_creator.py \
  --description "..." \
  --codex-timeout-sec 300
```

---

### Problem: "Fehler: Codex lieferte invalides JSON"

**Ursache:** Codex hat Text statt JSON zurückgegeben.

**Debug:**
- Output wird in Fehlermeldung angezeigt
- Prüfe ob Codex funktioniert: `echo "Test" | codex exec -`

**Lösung:**
- Vereinfache `--description` (zu komplex?)
- Nutze `--lang en` (evtl. bessere Codex-Performance)
- Retry (manchmal temporäre Codex-Probleme)

---

### Problem: "Familie existiert bereits"

**Ursache:** `config/<family>_main.json` existiert schon.

**Lösung 1 - Überschreiben:**
```bash
python creators/multi_family_creator.py \
  --description "..." \
  --force
```

**Lösung 2 - Neue ID:**
```bash
python creators/multi_family_creator.py \
  --description "..." \
  --family-id my_custom_family_v2
```

---

### Problem: "Dependency-Zyklus erkannt"

**Ursache:** Codex hat zirkuläre Dependencies generiert (A→B→C→A).

**Debug:**
```bash
python creators/multi_family_creator.py \
  --description "..." \
  --dry-run
```

Prüfe `depends_on` Fields in Output.

**Lösung:**
- Nutze `--interactive` um Dependencies manuell zu korrigieren
- Präzisiere `--description` (klare Rollen-Reihenfolge)
- Nutze `--template-from` für valide Struktur

---

### Problem: "Template nicht gefunden: developer"

**Ursache:** `config/developer_main.json` existiert nicht.

**Lösung:**
- Prüfe ob Template-Datei existiert: `ls config/developer_main.json`
- Nutze absoluten Pfad: `--template-from /absolute/path/to/config.json`
- Nutze anderen Template: `--template-from designer`

---

### Problem: Generierte Prompts sind zu generisch

**Ursache:** Codex hatte zu wenig Kontext.

**Lösung:**
```bash
python creators/multi_family_creator.py \
  --description "Detaillierte Beschreibung mit spezifischen Aufgaben pro Rolle" \
  --extra-instructions "Fokus auf [Domäne], nutze [Framework], berücksichtige [Constraint]" \
  --optimize-roles
```

Nutze `--optimize-roles` für bessere Beschreibungen.

---

### Problem: Zu viele/zu wenige Rollen generiert

**Ursache:** Codex entscheidet selbst basierend auf Beschreibung.

**Lösung:**
```bash
python creators/multi_family_creator.py \
  --description "..." \
  --role-count 5
```

Gibt Codex einen Hint (nicht strikt bindend, aber hilft).

---

## Best Practices

### 1. Präzise Beschreibungen

❌ **Schlecht:**
```bash
--description "Ein Team für ML"
```

✅ **Gut:**
```bash
--description "ML Team für Supervised Learning: Daten-Analyse mit Pandas, Feature Engineering, Model Training mit scikit-learn, Performance-Evaluation, Deployment"
```

### 2. Template-Nutzung

Nutze Templates wenn Workflow ähnlich:
- **Code-Entwicklung** → `--template-from developer`
- **Design-Aufgaben** → `--template-from designer`
- **Testing-Fokus** → `--template-from qa`
- **Infrastruktur** → `--template-from devops`

### 3. Interactive Mode für Komplexe Familien

```bash
python creators/multi_family_creator.py \
  --description "..." \
  --interactive \
  --optimize-roles
```

Ermöglicht manuelle Anpassungen vor Finalisierung.

### 4. Dry-Run zuerst

```bash
# 1. Dry-Run: Spec ansehen
python creators/multi_family_creator.py --description "..." --dry-run

# 2. Falls gut: Ohne dry-run ausführen
python creators/multi_family_creator.py --description "..."
```

### 5. Sprach-Konsistenz

Nutze `--lang en` wenn:
- Beschreibung auf Englisch ist
- Bessere Codex-Performance gewünscht
- Team international

---

## Weiterführende Links

- **[CONFIGURATION.md](CONFIGURATION.md)** - Vollständige Config-Referenz
- **[CUSTOM_ROLES.md](CUSTOM_ROLES.md)** - Manuelle Rollen-Erstellung
- **[QUICKSTART.md](QUICKSTART.md)** - Einstieg in Agent-Familien
- **[SHARDING.md](SHARDING.md)** - Parallele Agent-Ausführung

---

## Zusammenfassung

Der **Family Creator** macht es trivial, neue Agent-Familien zu erstellen:

1. **Beschreibe** die Familie in natürlicher Sprache
2. **Codex generiert** Struktur, Rollen, Prompts
3. **Review** (optional) und anpassen
4. **Fertig** - Familie sofort nutzbar

Statt Stunden manueller Arbeit: **5 Minuten automatisierte Generierung**.
