# Feature: Creator Scripts CLI-Provider Integration

## Problem Statement

Aktuell müssen Benutzer nach dem Erstellen einer Familie oder Rolle manuell:
1. Die generierte `*_main.json` öffnen
2. Für jede Rolle entscheiden welcher CLI-Provider geeignet ist
3. `cli_provider`, `model` und `cli_parameters` manuell hinzufügen
4. Validieren dass die Konfiguration korrekt ist

**Das ist zeitaufwändig und fehleranfällig.**

## Goals

### Primary Goals
1. **Automatische Provider-Auswahl** beim Erstellen von Familien/Rollen
2. **Intelligente Empfehlungen** basierend auf Rollen-Typ und Beschreibung
3. **Interactive CLI** zur Provider-Konfiguration
4. **Validierung** der CLI-Provider-Konfiguration

### Secondary Goals
1. **Templates** für häufige Provider-Kombinationen
2. **Learning System** - merkt sich User-Präferenzen
3. **Batch-Update** - CLI-Provider für existierende Configs hinzufügen

## User Stories

### Story 1: Familie mit optimalen Providern erstellen
```
Als Entwickler
Möchte ich beim Erstellen einer Familie automatisch optimale CLI-Provider zugewiesen bekommen
Sodass ich nicht manuell Provider konfigurieren muss
```

**Akzeptanzkriterien**:
- Family Creator fragt nach Provider-Strategie (auto/manual/template)
- Bei "auto": Provider werden basierend auf Rollen-Typ gewählt
- Generierte Config enthält `cli_provider` und `cli_parameters`
- User sieht Vorschau der Provider-Zuweisungen vor Bestätigung

### Story 2: Custom Provider-Zuweisungen
```
Als Power-User
Möchte ich für jede Rolle manuell den CLI-Provider wählen können
Sodass ich volle Kontrolle über die Konfiguration habe
```

**Akzeptanzkriterien**:
- Interactive Mode zeigt für jede Rolle Provider-Auswahlmenü
- Verfügbare Provider aus `cli_config.json` werden aufgelistet
- Model- und Parameter-Optionen werden angezeigt
- Validierung verhindert ungültige Konfigurationen

### Story 3: Template-basierte Erstellung
```
Als Team Lead
Möchte ich vordefinierte Provider-Templates verwenden
Sodass alle Team-Mitglieder konsistente Konfigurationen nutzen
```

**Akzeptanzkriterien**:
- Templates für "cost-optimized", "quality-first", "balanced" verfügbar
- Custom Templates können gespeichert werden
- Template-Auswahl im Creator CLI
- Templates werden in `.codex/templates/` gespeichert

### Story 4: Existierende Configs migrieren
```
Als Benutzer mit existierenden Configs
Möchte ich CLI-Provider für alte Konfigurationen nachträglich hinzufügen
Sodass ich die neuen Features nutzen kann
```

**Akzeptanzkriterien**:
- `--migrate-cli-providers` Flag für Family Creator
- Batch-Update für alle Rollen in einer Config
- Backup der alten Config wird erstellt
- Validierung nach Migration

## Non-Goals

- **Keine** Änderung der grundlegenden Creator-Architektur
- **Keine** Breaking Changes für existierende CLI-Flags
- **Keine** Provider-Installation (User muss Provider selbst installieren)

## Success Metrics

### Quantitative
- **90%** der generierten Configs nutzen CLI-Provider
- **< 30 Sekunden** durchschnittliche Zeit für Provider-Auswahl
- **< 5%** Fehlerrate bei Provider-Konfiguration

### Qualitative
- User finden Provider-Auswahl "intuitiv"
- Reduzierte Support-Anfragen zu Provider-Konfiguration
- Positive Feedback zu automatischen Empfehlungen

## Example Workflows

### Workflow 1: Auto Mode (Standard)

```bash
$ python multi_agent_codex.py create-family \
    --description "Team für Backend-Entwicklung mit Tests" \
    --auto-providers

[CLI Provider Configuration]
Provider-Strategie: Automatisch optimiert

Geplante Provider-Zuweisungen:
  architect     -> claude (sonnet)    [Komplexe Planung]
  implementer   -> codex              [Code-Generierung]
  tester        -> gemini (flash)     [Schnelle Tests]
  reviewer      -> claude (opus)      [Qualitäts-Review]
  integrator    -> claude (haiku)     [Einfache Zusammenfassung]

Geschätzte Kosten pro Run: $0.45 (vs. $1.20 nur Opus)
Ersparnis: 62%

Fortfahren? [Y/n]
```

### Workflow 2: Interactive Mode

```bash
$ python multi_agent_codex.py create-family \
    --description "ML Pipeline" \
    --interactive-providers

[CLI Provider Configuration]
Provider-Strategie: Interaktiv

Rolle: data_analyst
Beschreibung: Analysiert Daten und erstellt Feature Engineering Plan

Empfohlener Provider: claude (sonnet)
Verfügbare Provider:
  1. codex              [Standard, gut für Code]
  2. claude (sonnet)    [Empfohlen für Analyse] ⭐
  3. claude (opus)      [Höchste Qualität, teuer]
  4. claude (haiku)     [Schnell, kostengünstig]
  5. gemini (pro)       [Google, vielseitig]
  6. gemini (flash)     [Schnell, einfache Tasks]

Wähle Provider [2]: 2

Model: sonnet
Parameter anpassen? [y/N]: y

max_turns [3]: 5
allowed_tools [Read,Grep]: Read,Grep,Bash
output_format [text]: text

✓ data_analyst -> claude (sonnet) konfiguriert

[Nächste Rolle...]
```

### Workflow 3: Template Mode

```bash
$ python multi_agent_codex.py create-family \
    --description "Full-Stack App" \
    --provider-template cost-optimized

[CLI Provider Configuration]
Verwende Template: cost-optimized

Template-Details:
  Strategie: Minimale Kosten bei guter Qualität
  Haupt-Provider: gemini (flash 70%), claude (haiku 20%), codex (10%)
  Erwartete Kosten: ~$0.15 pro Run

Template anwenden? [Y/n]
```

## Related Features

- **Base Feature**: Multi-CLI Provider Support (COMPLETED)
- **Related**: Auto Provider Selection (verwendet gleiche Logik)
- **Related**: Cost Tracking Dashboard (zeigt Creator-generierte Costs)

## Open Questions

1. **Provider-Installation**: Sollen wir checken ob Provider installiert sind?
   - **Entscheidung**: Ja, Warning wenn Provider fehlt, aber Config wird trotzdem generiert

2. **Default-Strategie**: Was ist der Default wenn `--auto-providers` nicht gesetzt?
   - **Entscheidung**: Codex (Backwards compatible), aber Hinweis auf neue Features

3. **Template-Speicherort**: Wo speichern wir User-Templates?
   - **Entscheidung**: `~/.codex/templates/provider_templates.json`

4. **Konflikte**: Was wenn User `--codex-cmd` UND `--auto-providers` setzt?
   - **Entscheidung**: `--codex-cmd` hat Priorität (Legacy support), aber Warning
