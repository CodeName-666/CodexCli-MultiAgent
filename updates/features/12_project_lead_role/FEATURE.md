# Feature: Project Lead Role - Dynamische Koordination

## Overview
Einfuehrung einer speziellen "Project Lead" Rolle, die parallel zu allen anderen Rollen arbeitet und als dynamischer Task-Coordinator, Reviewer und Re-Sharding-Manager fungiert. Der Project Lead ueberwacht den Fortschritt, verteilt Aufgaben dynamisch und kann bei Bedarf Tasks neu aufteilen.

## Priority
🟡 **PRIORITY 2** - Advanced Feature (nach LLM-Sharding)

## Impact
- **User Experience**: ⭐⭐⭐ (Intelligente, adaptive Koordination)
- **Effort**: Hoch (5-7 Tage)
- **ROI**: ⭐⭐ (Komplexe Szenarien)

## Problem Statement
Das aktuelle Pipeline-System arbeitet sequentiell mit statischem Sharding. Einmal erstellte Shards koennen nicht mehr angepasst werden. Es gibt keine zentrale Instanz, die:
- Den Fortschritt aller Instanzen ueberwacht
- Aufgaben dynamisch umverteilt wenn eine Instanz blockiert ist
- Die Qualitaet der Outputs kontinuierlich prueft
- Bei Problemen eingreift und Re-Sharding durchfuehrt

### Current Pain Points
1. Statisches Sharding - einmal erstellt, nicht mehr aenderbar
2. Keine Echtzeit-Koordination zwischen parallelen Instanzen
3. Ungleiche Arbeitslast wenn ein Shard komplexer ist als erwartet
4. Keine fruehzeitige Erkennung von Qualitaetsproblemen
5. Keine Moeglichkeit, blockierte Tasks neu zu verteilen
6. Fehlende Gesamtsicht ueber den Pipeline-Fortschritt

### Abgrenzung zu LLM-Sharding (Feature 11)
| Aspekt | LLM-Sharding | Project Lead |
|--------|--------------|--------------|
| Zeitpunkt | Vor Ausfuehrung | Waehrend Ausfuehrung |
| Frequenz | Einmalig | Kontinuierlich |
| Anpassung | Statisch | Dynamisch |
| Overhead | Minimal (1 Call) | Hoeher (laufend) |
| Komplexitaet | Niedrig | Hoch |

## Goals
1. Parallele Project Lead Rolle die alle anderen Rollen ueberwacht
2. Dynamisches Re-Sharding wenn Tasks zu gross/komplex sind
3. Echtzeit-Qualitaetspruefung von Outputs
4. Load-Balancing zwischen Instanzen
5. Fruehwarnsystem fuer Probleme
6. Zentrale Entscheidungsinstanz fuer Konflikte

## Architektur-Konzept

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PROJECT LEAD                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  - Ueberwacht TaskBoard kontinuierlich                      │   │
│  │  - Prueft Outputs auf Qualitaet                             │   │
│  │  - Entscheidet ueber Re-Sharding                            │   │
│  │  - Loest Konflikte bei Overlaps                             │   │
│  │  - Gibt Feedback an blockierte Instanzen                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         │ watch              │ intervene          │ redistribute   │
│         ▼                    ▼                    ▼                │
└─────────────────────────────────────────────────────────────────────┘
          │                    │                    │
    ┌─────┴─────┐        ┌─────┴─────┐        ┌─────┴─────┐
    │ Architect │        │Implementer│        │  Tester   │
    │  #1  #2   │        │ #1 #2 #3  │        │  #1  #2   │
    └───────────┘        └───────────┘        └───────────┘
```

## User Stories

### Story 1: Dynamisches Re-Sharding
```
Als Entwickler,
Wenn eine Implementer-Instanz nach 50% der Zeit erst 10% erledigt hat,
Will ich dass der Project Lead den Task automatisch neu aufteilt,
Sodass andere Instanzen Teile uebernehmen koennen.
```

### Story 2: Qualitaets-Gate
```
Als Entwickler,
Wenn eine Instanz Output produziert der nicht den erwarteten Sections entspricht,
Will ich dass der Project Lead sofort Feedback gibt und Korrektur anfordert,
Sodass Fehler frueh erkannt werden statt erst am Ende der Pipeline.
```

### Story 3: Konflikt-Resolution
```
Als Entwickler,
Wenn zwei Instanzen versehentlich dieselbe Datei bearbeiten wollen,
Will ich dass der Project Lead den Konflikt erkennt und eine Instanz umleitet,
Sodass keine Merge-Konflikte entstehen.
```

### Story 4: Fortschritts-Reporting
```
Als Entwickler,
Will ich Echtzeit-Updates ueber den Status aller Instanzen sehen,
Sodass ich den Fortschritt der gesamten Pipeline nachvollziehen kann.
```

### Story 5: Adaptive Timeout-Steuerung
```
Als Entwickler,
Wenn eine Instanz kurz vor dem Timeout steht aber guten Fortschritt macht,
Will ich dass der Project Lead den Timeout verlaengert,
Sodass die Arbeit nicht verloren geht.
```

## Funktionsumfang

### Phase 1: Passive Ueberwachung
- [ ] TaskBoard-Monitoring in Echtzeit
- [ ] Fortschritts-Tracking pro Instanz
- [ ] Output-Validierung gegen expected_sections
- [ ] Logging von Anomalien und Warnungen
- [ ] Status-Dashboard Output

### Phase 2: Aktive Intervention
- [ ] Re-Sharding bei Timeout-Gefahr
- [ ] Feedback-Injection in laufende Prompts
- [ ] Dynamische Timeout-Anpassung
- [ ] Konflikt-Erkennung bei Datei-Overlaps

### Phase 3: Intelligente Koordination
- [ ] Vorhersage von Problemen basierend auf Fortschritt
- [ ] Automatische Priorisierung von Tasks
- [ ] Cross-Instance Wissensaustausch
- [ ] Lernende Optimierung ueber mehrere Runs

## Konfiguration

### Family Config mit Project Lead
```json
{
  "project_lead": {
    "enabled": true,
    "cli_provider": "claude",
    "model": "haiku",
    "check_interval_sec": 30,
    "intervention_threshold": 0.7,
    "enable_resharding": true,
    "enable_quality_gates": true,
    "max_interventions_per_role": 3
  },
  "roles": [
    {
      "id": "implementer",
      "instances": 3,
      "allow_lead_intervention": true,
      "lead_quality_check": true
    }
  ]
}
```

### Project Lead Optionen
```json
{
  "project_lead": {
    "enabled": true,
    "cli_provider": "claude",
    "model": "haiku",

    "monitoring": {
      "check_interval_sec": 30,
      "progress_estimation": true,
      "output_validation": true
    },

    "intervention": {
      "enabled": true,
      "threshold_progress_behind": 0.5,
      "threshold_timeout_risk": 0.8,
      "max_reshards_per_role": 2,
      "cooldown_after_intervention_sec": 60
    },

    "quality": {
      "check_sections": true,
      "check_diff_syntax": true,
      "check_overlap": true,
      "reject_on_failure": false
    },

    "reporting": {
      "realtime_status": true,
      "summary_on_completion": true,
      "log_decisions": true
    }
  }
}
```

## Success Metrics
- [ ] 30% weniger Pipeline-Failures durch fruehe Intervention
- [ ] 20% bessere Ressourcen-Auslastung durch Load-Balancing
- [ ] 50% weniger Overlap-Konflikte durch proaktive Erkennung
- [ ] Echtzeit-Visibility ueber Pipeline-Status
- [ ] Messbare Verbesserung der Output-Qualitaet

## Non-Goals (V1)
- Vollautonome Pipeline ohne menschliche Aufsicht
- Lernen ueber Sessions hinweg (nur In-Session Optimierung)
- Multi-Pipeline Koordination (nur einzelne Pipeline)
- Automatische Code-Korrekturen (nur Feedback)

## Risiken und Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Zu viele Interventionen stoeren Flow | Mittel | Mittel | Cooldown-Zeiten, max_interventions Limit |
| LLM-Kosten durch kontinuierliche Checks | Hoch | Niedrig | Guenstiges Modell (Haiku), lange Intervalle |
| Falsche Re-Sharding Entscheidungen | Niedrig | Hoch | Konservative Thresholds, Logging |
| Komplexitaet erschwert Debugging | Mittel | Mittel | Umfangreiches Logging, Dry-Run Modus |
| Race Conditions bei Intervention | Niedrig | Hoch | Locking, sequentielle Entscheidungen |

## Abhaengigkeiten
- Feature 11: LLM-Sharding (fuer Re-Sharding Logik)
- TaskBoard System (bereits implementiert)
- CoordinationLog (bereits implementiert)
- Streaming Output (fuer Progress-Tracking)

## Technische Herausforderungen

### 1. Parallelitaet
Der Project Lead muss parallel zu den anderen Rollen laufen ohne deren Ausfuehrung zu blockieren.

### 2. State Management
Entscheidungen des Project Lead muessen persistent sein und von allen Instanzen respektiert werden.

### 3. Intervention Timing
Interventionen muessen zum richtigen Zeitpunkt erfolgen - nicht zu frueh (unnoetig), nicht zu spaet (wirkungslos).

### 4. LLM Context
Der Project Lead braucht ausreichend Kontext um gute Entscheidungen zu treffen, aber der Kontext darf nicht zu gross werden.
