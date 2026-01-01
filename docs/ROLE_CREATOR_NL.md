# Role Creator: Natural Language Mode

Erstelle einzelne Rollen automatisch via Natural Language mit Codex CLI.

---

## Überblick

Der **Role Creator** (`multi_role_agent_creator.py`) wurde erweitert um einen **Natural Language Mode**, ähnlich wie der Family Creator. Du kannst jetzt Rollen mit einer einfachen Beschreibung erstellen, statt alle Details manuell via CLI-Flags anzugeben.

### Zwei Modi:

1. **Natural Language Mode** (NEU) - Beschreibe Rolle, Codex generiert Details
2. **Legacy Mode** - Alle Details via Flags (wie bisher)

---

## Quick Start: Natural Language Mode

### Einfachste Verwendung

```bash
# Via Haupt-CLI (empfohlen)
python multi_agent_codex.py create-role \
  --nl-description "Ein Code Reviewer der auf Bugs, Security-Issues und Best Practices prüft" \
  --config agent_families/developer_main.json

# ODER direkt/eigenständig
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Code Reviewer der auf Bugs, Security-Issues und Best Practices prüft" \
  --config agent_families/developer_main.json
```

> **Hinweis:** Beide Aufrufe sind funktional identisch. Das Haupt-CLI bietet eine einheitlichere Schnittstelle.

**Output:**
```
Generiere Rollen-Spezifikation via Codex (Natural Language Mode)...
✓ Rollen-Datei erstellt: agent_families/developer_agents/code_reviewer.json
✓ Rolle registriert in: agent_families/developer_main.json

Rolle erstellt: code_reviewer
  Name: Code Reviewer
  Datei: developer_agents/code_reviewer.json
  Apply-Diff: Nein
```

### Mit mehr Optionen

```bash
# Via Haupt-CLI
python multi_agent_codex.py create-role \
  --nl-description "Ein Security Auditor der OWASP Top 10 Vulnerabilities findet und Fixes vorschlägt" \
  --config agent_families/security_main.json \
  --apply-diff \
  --depends-on threat_modeler \
  --lang en

# ODER direkt
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Security Auditor der OWASP Top 10 Vulnerabilities findet und Fixes vorschlägt" \
  --config agent_families/security_main.json \
  --apply-diff \
  --depends-on threat_modeler \
  --lang en
```

### Dry-Run (Preview)

```bash
# Via Haupt-CLI
python multi_agent_codex.py create-role \
  --nl-description "Ein Performance Optimizer der Bottlenecks identifiziert" \
  --config agent_families/developer_main.json \
  --dry-run

# ODER direkt
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Performance Optimizer der Bottlenecks identifiziert" \
  --config agent_families/developer_main.json \
  --dry-run
```

**Output:**
```json
{
  "id": "performance_optimizer",
  "name": "Performance Optimizer",
  "role_label": "Performance Engineer",
  "title": "Performance-Optimierung",
  "description": "Identifiziert Performance-Bottlenecks im Code und schlägt Optimierungen vor.",
  "apply_diff": false,
  "expected_sections": [
    "# Performance-Optimierung",
    "- Bottlenecks:",
    "- Empfehlungen:",
    "- Messungen:"
  ],
  ...
}
```

Keine Dateien werden geschrieben - nur JSON-Preview.

---

## CLI-Referenz: Natural Language Mode

| Argument | Default | Beschreibung |
|----------|---------|--------------|
| `--nl-description TEXT` | - | **Erforderlich**: Natural Language Rollen-Beschreibung |
| `--config PATH` | developer_main.json | Haupt-Config-Datei |
| `--lang LANG` | de | Sprache (de/en) für Codex-Prompts |
| `--extra-instructions TEXT` | - | Zusatz-Anweisungen für Codex |
| `--nl-timeout-sec SEC` | 180 | Timeout für Codex-Aufrufe |
| `--codex-cmd-override CMD` | - | Override Codex CLI Command |
| `--dry-run` | false | Zeigt nur JSON, schreibt nichts |
| `--apply-diff` | false | Rolle soll Diffs anwenden |
| `--depends-on ROLE` | [] | Dependencies (wiederholbar) |
| `--instances N` | 1 | Anzahl Instanzen |
| `--force` | false | Überschreibt existierende Rolle |

---

## Beispiele

### Beispiel 1: Code Reviewer

```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Code Reviewer der Bugs, Code-Smells und Best-Practice-Verletzungen findet" \
  --config agent_families/developer_main.json
```

**Was Codex generiert:**
- `id`: `code_reviewer`
- `name`: `Code Reviewer`
- `role_label`: `Software Quality Engineer`
- `expected_sections`: ["# Code Review", "- Findings:", "- Priority:", "- Recommendations:"]
- `apply_diff`: `false` (liest nur, ändert nicht)

---

### Beispiel 2: Security Fixer (mit Diffs)

```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Security Fixer der Vulnerabilities automatisch patcht" \
  --config agent_families/security_main.json \
  --apply-diff \
  --depends-on security_reviewer
```

**Was Codex generiert:**
- `id`: `security_fixer`
- `apply_diff`: `true` (generiert Diffs)
- `depends_on`: `["security_reviewer"]`
- `diff_instructions`: "Liefere unified diff mit Security-Patches"
- `expected_sections`: ["# Security Fixes", "```diff"]

---

### Beispiel 3: UI Component Generator

```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Generiert React Components mit TypeScript, Styled-Components und Tests" \
  --config agent_families/designer_main.json \
  --apply-diff \
  --lang en
```

**Was Codex generiert:**
- `id`: `ui_component_generator`
- `expected_sections`: ["# Component Implementation", "```diff", "- Tests:"]
- Englische Prompts (wegen `--lang en`)

---

### Beispiel 4: Custom Instructions

```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Ein API Documentation Generator" \
  --config agent_families/docs_main.json \
  --extra-instructions "Fokus auf OpenAPI 3.0 Spec, mit Beispielen und Error-Codes"
```

**Extra-Instructions:**
- Codex berücksichtigt OpenAPI 3.0
- Fügt Beispiele hinzu
- Berücksichtigt Error-Codes

---

## Was Codex Automatisch Generiert

Basierend auf der Natural Language Description generiert Codex:

| Feld | Beispiel | Beschreibung |
|------|----------|--------------|
| `id` | `code_reviewer` | Slugified von Description |
| `name` | `Code Reviewer` | Human-readable Name |
| `role_label` | `Software Quality Engineer` | Job Title |
| `title` | `Code Review` | Prompt-Header |
| `description` | "Prüft Code auf Bugs..." | 2-4 Sätze |
| `apply_diff` | `true/false` | Ändert Code? |
| `expected_sections` | `["# Review", "- Findings:"]` | Output-Struktur |
| `format_sections` | `["- Aufgaben:", ...]` | Prompt-Format |
| `context_entries` | `[{"key": "snapshot", ...}]` | Welche Inputs? |
| `depends_on` | `["architect"]` | Vorgänger-Rollen |
| `diff_instructions` | "Liefere unified diff..." | Bei apply_diff=true |

---

## Vergleich: Natural Language vs. Legacy Mode

### Natural Language Mode (NEU)

```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Test Generator der Unit Tests mit pytest erstellt"
```

**Vorteile:**
- ✅ Sehr schnell (1 Befehl)
- ✅ Codex generiert alles automatisch
- ✅ Optimal für neue/unbekannte Rollen
- ✅ Ähnlich wie Family Creator

**Nachteile:**
- ❌ Weniger Kontrolle über Details
- ❌ Codex kann falsche Annahmen treffen

---

### Legacy Mode

```bash
python creators/multi_role_agent_creator_legacy.py \
  --description "Generiert Unit Tests mit pytest" \
  --section "- Tests:" \
  --section "- Coverage:" \
  --context architect_summary:ARCHITEKTUR \
  --apply-diff \
  --diff-text "Dann liefere pytest Tests als unified diff"
```

**Vorteile:**
- ✅ Maximale Kontrolle über jedes Detail
- ✅ Präzise Prompt-Struktur
- ✅ Keine Codex-Calls (schneller, deterministisch)

**Nachteile:**
- ❌ Sehr viele Flags nötig
- ❌ Manueller Aufwand
- ❌ Muss Prompt-Struktur verstehen

---

## Empfehlungen

### Nutze Natural Language Mode wenn:
- ✅ Neue Rolle schnell erstellen
- ✅ Nicht sicher, welche Sections/Context-Entries nötig sind
- ✅ Codex soll optimale Struktur vorschlagen
- ✅ Ähnlicher Workflow wie bei Family Creator gewünscht

### Nutze Legacy Mode wenn:
- ✅ Präzise Kontrolle über Prompt-Template erforderlich
- ✅ Bestehende Rolle klonen/anpassen
- ✅ Kein Codex CLI verfügbar
- ✅ Deterministisches Ergebnis gewünscht

---

## Troubleshooting

### Problem: "Codex CLI timeout"

**Lösung:**
```bash
python creators/multi_role_agent_creator.py \
  --nl-description "..." \
  --nl-timeout-sec 300
```

---

### Problem: "Fehler: Codex lieferte invalides JSON"

**Debug:**
- Vereinfache Description (zu komplex?)
- Nutze `--lang en` (evtl. bessere Codex-Performance)
- Retry (manchmal temporäre Codex-Probleme)

---

### Problem: "Rolle existiert bereits"

**Lösung:**
```bash
python creators/multi_role_agent_creator.py \
  --nl-description "..." \
  --force
```

---

### Problem: Generierte Rolle ist zu generisch

**Lösung:**
```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Detaillierte Beschreibung mit spezifischen Aufgaben und Constraints" \
  --extra-instructions "Fokus auf [Framework], nutze [Pattern], berücksichtige [Requirement]"
```

---

## Migration von Legacy zu Natural Language

**Alt (Legacy):**
```bash
python creators/multi_role_agent_creator_legacy.py \
  --description "Code Reviewer" \
  --section "- Findings:" \
  --section "- Priority:" \
  --section "- Recommendations:" \
  --context architect_summary:ARCH \
  --context implementer_output:CODE \
  --rule "Findings müssen kategorisiert sein" \
  --config agent_families/developer_main.json
```

**Neu (Natural Language):**
```bash
python creators/multi_role_agent_creator.py \
  --nl-description "Ein Code Reviewer der Code analysiert und Findings nach Priority kategorisiert" \
  --config agent_families/developer_main.json
```

Codex generiert automatisch:
- Sections (Findings, Priority, Recommendations)
- Context-Entries (architect_summary, implementer_output)
- Rules (kategorisierte Findings)

---

## Weiterführende Links

- **[FAMILY_CREATOR.md](FAMILY_CREATOR.md)** - Ganze Familien via Natural Language
- **[CUSTOM_ROLES.md](CUSTOM_ROLES.md)** - Manuelle Rollen-Erstellung (Legacy-Details)
- **[CONFIGURATION.md](CONFIGURATION.md)** - Config-Referenz

---

## Zusammenfassung

Der **Natural Language Mode** macht es trivial, neue Rollen zu erstellen:

1. **Beschreibe** die Rolle in natürlicher Sprache
2. **Codex generiert** alle Details (Prompt, Sections, Context)
3. **Fertig** - Rolle sofort nutzbar

Statt 10+ Flags: **1 Natural Language Beschreibung**.
