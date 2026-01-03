# CLI Reference - Multi-Agent Codex

## Übersicht

Multi-Agent Codex bietet mehrere Subcommands für verschiedene Aufgaben:

```bash
multi_agent_codex [subcommand] [options]
```

## Subcommands

### 1. `run` - Task ausführen (EMPFOHLEN)

Führt einen Multi-Agent-Task aus - wahlweise interaktiv oder per CLI.

#### Verwendung

```bash
# Vollständig interaktiv (empfohlen)
multi_agent_codex run

# Hybrid: Familie vorgeben, Rest interaktiv
multi_agent_codex run --family developer

# Vollständig per CLI (scriptbar)
multi_agent_codex run --family developer --task "Fix Bug" --apply --yes
```

#### Alle Parameter

```bash
multi_agent_codex run --help
```

**Core-Parameter:**
- `--family FAMILY` - Agent-Familie (z.B. developer, designer)
- `--task TASK` - Task-Beschreibung
- `--dir DIR` - Working Directory (default: .)
- `--timeout TIMEOUT` - Timeout in Sekunden (default: 1200)

**Apply-Optionen:**
- `--apply` - Diff automatisch anwenden
- `--apply-mode {end,role}` - Wann applyen (default: end)
- `--apply-confirm` - Vor jedem Apply bestätigen
- `--apply-roles ROLE` - Nur für diese Rollen (wiederholbar)

**Execution:**
- `--fail-fast` - Bei Fehler sofort abbrechen
- `--ignore-fail` - Fehler ignorieren
- `--task-split` - Task-Splitting aktivieren
- `--no-task-resume` - Task-Splitting Resume deaktivieren

**Limits:**
- `--max-files N` - Max Dateien im Snapshot (default: 350)
- `--max-file-bytes N` - Max Bytes pro Datei (default: 90000)

**Interaktivität:**
- `--non-interactive` - Fehler bei fehlenden Parametern
- `--yes, -y` - Alle Bestätigungen automatisch mit Ja

#### Modi

**Interaktiver Modus** (keine Parameter):
- Geführter Dialog
- Familienauswahl aus Liste
- Multi-Line Task-Eingabe
- Optionale Parameter abfragen
- Zusammenfassung & Bestätigung

**Hybrid-Modus** (teilweise Parameter):
- Angegebene Parameter nutzen
- Fehlende interaktiv abfragen
- Schneller als voll-interaktiv

**CLI-Modus** (alle Parameter):
- Vollständig scriptbar
- Für CI/CD geeignet
- Mit `--yes` keine Bestätigung nötig

---

### 2. `create-family` - Familie erstellen

Erstellt eine neue Agent-Familie aus natürlichsprachlicher Beschreibung.

#### Verwendung

```bash
multi_agent_codex create-family --description "Ein Team für ML-Entwicklung"
```

#### Alle Parameter

```bash
multi_agent_codex create-family --help
```

**Erforderlich:**
- `--description TEXT` - Natürlichsprachliche Beschreibung der Familie

**Optional:**
- `--family-id ID` - Familie-ID (default: aus description)
- `--family-name NAME` - Lesbarer Name (default: family-id)
- `--system-rules RULES` - Custom System-Regeln
- `--template-from FAMILY` - Basis-Familie zum Klonen
- `--template-mode {clone,inspire,scratch}` - Template-Modus (default: scratch)
- `--codex-cmd CMD` - Codex CLI override
- `--codex-timeout-sec N` - Timeout (default: 180)
- `--optimize-roles` - Rollen-Beschreibungen optimieren
- `--role-count N` - Hint für Anzahl Rollen
- `--include-integrator` - Integrator-Rolle hinzufügen (default: true)
- `--apply-diff-roles ROLES` - Rollen die Diffs applyen (komma-separiert)
- `--output-dir DIR` - Output-Verzeichnis (default: agent_families/)
- `--dry-run` - Spec generieren ohne zu schreiben
- `--interactive` - Review & Edit vor Schreiben
- `--force` - Existierende Familie überschreiben
- `--extra-instructions TEXT` - Zusätzliche Anweisungen für Codex
- `--lang {de,en}` - Sprache (default: de)

#### Beispiele

```bash
# Einfachste Form
multi_agent_codex create-family --description "Team für API-Entwicklung"

# Mit Template
multi_agent_codex create-family \
  --description "Spezialisiertes Security-Team" \
  --template-from developer \
  --template-mode inspire

# Mit Review
multi_agent_codex create-family \
  --description "Data Science Team" \
  --interactive \
  --optimize-roles
```

---

### 3. `create-role` - Rolle erstellen

Erstellt eine neue Rolle in einer bestehenden Familie.

#### Verwendung

```bash
# Natural Language Mode (empfohlen)
multi_agent_codex create-role --nl-description "Ein Code Reviewer für Security"

# Legacy Mode (manuelle Kontrolle)
multi_agent_codex create-role --description "Code Reviewer" --section "- Findings:"
```

#### Alle Parameter

```bash
multi_agent_codex create-role --help
```

**Natural Language Mode:**
- `--nl-description TEXT` - Natürlichsprachliche Beschreibung
- `--lang {de,en}` - Sprache (default: de)
- `--extra-instructions TEXT` - Zusätzliche Anweisungen
- `--nl-timeout-sec N` - Timeout (default: 180)
- `--codex-cmd-override CMD` - Codex CLI override
- `--dry-run` - Spec anzeigen ohne zu schreiben

**Legacy Mode:**
- `--description TEXT` - Rollen-Beschreibung (LEGACY)
- `--id ID` - Rollen-ID (default: slugified)
- `--name NAME` - Rollen-Name (default: id)
- `--role LABEL` - Rollen-Label (default: name)
- `--title TITLE` - Prompt-Title (default: role label)
- `--section TEXT` - Format-Section (wiederholbar)
- `--expected-section TEXT` - Expected section (wiederholbar)
- `--context KEY[:LABEL]` - Extra Placeholder (wiederholbar)
- `--rule TEXT` - Regel-Zeile (wiederholbar)
- `--replace-rules` - Nur eigene Rules verwenden

**Common Options:**
- `--file PATH` - Rollen-Datei Pfad (relativ zu agent_families/)
- `--apply-diff` - Rolle produziert Diff
- `--diff-text TEXT` - Custom Diff-Anweisung
- `--diff-instructions / --no-diff-instructions` - Diff-Instructions inkludieren
- `--insert-after ID` - Nach dieser Rolle einfügen
- `--depends-on ID` - Dependency (wiederholbar)
- `--instances N` - Anzahl Instanzen (default: 1)
- `--timeout-sec N` - Rollen-Timeout override
- `--max-output-chars N` - Max Output chars
- `--max-prompt-chars N` - Max Prompt chars
- `--max-prompt-tokens N` - Max Prompt tokens
- `--retries N` - Retry count
- `--codex-cmd CMD` - Codex command override
- `--model MODEL` - Model override
- `--run-if-review-critical` - Nur bei kritischem Review
- `--config PATH` - Main config Pfad (default: developer_main.json)
- `--force` - Existierende Rolle überschreiben

**Description Optimization (Legacy):**
- `--optimize-description` - Beschreibung via Codex optimieren
- `--optimize-instructions TEXT` - Extra Instructions
- `--optimize-timeout-sec N` - Timeout (default: 120)
- `--optimize-codex-cmd CMD` - Codex CMD override

**Toggles:**
- `--description-block / --no-description-block` - Beschreibungs-Block
- `--no-last-applied-diff` - Last-Applied-Diff Block weglassen
- `--no-coordination` - Coordination Block weglassen
- `--no-snapshot` - Snapshot Block weglassen
- `--no-expected-diff` - ```diff aus expected sections entfernen

#### Beispiele

```bash
# Natural Language (empfohlen)
multi_agent_codex create-role --nl-description "Ein Tester der Edge Cases prüft"

# Mit Config
multi_agent_codex create-role \
  --nl-description "Ein Performance Analyst" \
  --config agent_families/developer_main.json

# Legacy Mode
multi_agent_codex create-role \
  --description "Code Reviewer" \
  --section "- Findings:" \
  --section "- Risk Level:" \
  --apply-diff \
  --depends-on implementer
```

---

## Rückwärtskompatibilität

Der alte CLI-Modus (direkt mit `--task`) funktioniert weiterhin:

```bash
# Alte Syntax (noch unterstützt)
multi_agent_codex --task "Implementiere Feature X" --config agent_families/developer_main.json --apply

# Neue Syntax (empfohlen)
multi_agent_codex run --family developer --task "Implementiere Feature X" --apply
```

---

## Hilfe-System

Jeder Subcommand hat seine eigene Hilfe:

```bash
# Allgemeine Hilfe
multi_agent_codex --help

# Subcommand-spezifische Hilfe
multi_agent_codex run --help
multi_agent_codex create-family --help
multi_agent_codex create-role --help
```

---

## Best Practices

### Für Einsteiger
- Nutze `multi_agent_codex run` ohne Parameter (vollständig interaktiv)
- Nutze `create-family` mit nur `--description`
- Nutze `create-role` mit nur `--nl-description`

### Für Power-User
- Nutze `run` mit `--family` und `--task` für schnelle Tasks
- Nutze `--non-interactive` und `--yes` für Scripts
- Nutze `--dry-run` bei Familie/Rollen-Erstellung zum Testen

### Für CI/CD
```bash
# Vollständig nicht-interaktiv
multi_agent_codex run \
  --family developer \
  --task "@task.md" \
  --apply \
  --non-interactive \
  --yes \
  --fail-fast
```

---

## Tipps & Tricks

### Task aus Datei laden
```bash
# Task-Beschreibung aus Datei
multi_agent_codex run --task "@task_description.md"
```

### Familie schnell erstellen
```bash
# Minimale Eingabe
multi_agent_codex create-family --description "API Testing Team"
```

### Rollen interaktiv konfigurieren
```bash
# Mit Interactive Review
multi_agent_codex create-family --description "DevOps Team" --interactive
```

### Debugging
```bash
# Dry-run zum Testen
multi_agent_codex create-family --description "Test" --dry-run

# Config validieren
multi_agent_codex --task "test" --validate-config
```
