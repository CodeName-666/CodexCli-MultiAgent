# Feature: LLM-basiertes Task-Sharding

## Overview
Erweiterung des bestehenden Sharding-Systems um LLM-basierte Aufgabenaufteilung, sodass auch einfache Texteingaben (ohne Markdown-Struktur) auf mehrere parallele Instanzen verteilt werden koennen.

## Priority
🔴 **PRIORITY 1** - Core Feature Gap

## Impact
- **User Experience**: ⭐⭐⭐ (Parallele Verarbeitung fuer alle Eingabearten)
- **Effort**: Mittel (2-3 Tage)
- **ROI**: ⭐⭐⭐

## Problem Statement
Das aktuelle Sharding funktioniert nur mit strukturierten Markdown-Dateien (H1/H2-Headings). Bei einfachen Texteingaben ueber `--task` gibt es keine Aufteilung auf Instanzen - alle Instanzen erhalten denselben Task, was zu redundanter Arbeit fuehrt.

### Current Pain Points
1. `shard_mode: "headings"` erfordert strukturiertes Markdown mit H1/H2 Kapiteln
2. `shard_mode: "files"` funktioniert nur wenn Dateipfade im Text erkennbar sind
3. `shard_mode: "llm"` ist als Platzhalter vorhanden aber nicht implementiert (NotImplementedError)
4. Einfache Texteingaben werden als einzelner "Full Task" Shard behandelt
5. Keine Parallelisierung bei natuerlichsprachlichen Aufgabenbeschreibungen

### Betroffener Code
- `multi_agent/sharding.py:40-41` - NotImplementedError fuer LLM-Modus
- `multi_agent/sharding.py:83-93` - Fallback auf Single-Shard bei fehlenden Headings

## Goals
1. Implementierung von `shard_mode: "llm"` in `sharding.py`
2. Dynamische Nutzung des bereits konfigurierten `cli_provider` der jeweiligen Rolle
3. Intelligente Aufteilung von unstrukturierten Aufgaben in parallele Teilaufgaben
4. Robuster Fallback bei LLM-Parsing-Fehlern
5. Optionale Konfiguration eines separaten (guenstigeren) LLMs fuer das Sharding

## User Stories

### Story 1: Einfache Texteingabe parallel verarbeiten
```
Als Entwickler,
Wenn ich `--task "Implementiere Feature X mit Tests und Dokumentation"` eingebe,
Will ich dass das System die Aufgabe automatisch in sinnvolle Teilaufgaben aufteilt,
Sodass meine 3 konfigurierten Instanzen parallel an verschiedenen Aspekten arbeiten.
```

### Story 2: Automatische Provider-Nutzung
```
Als Entwickler,
Wenn ich `shard_mode: "llm"` fuer eine Rolle mit `cli_provider: "claude"` konfiguriere,
Will ich dass das Sharding automatisch Claude fuer die Aufteilung nutzt,
Sodass ich keinen zusaetzlichen LLM-Provider konfigurieren muss.
```

### Story 3: Guenstiges Sharding-LLM
```
Als Entwickler,
Wenn ich Kosten sparen will aber trotzdem LLM-Sharding nutzen moechte,
Will ich optional ein guenstigeres LLM (z.B. Haiku) nur fuer das Sharding konfigurieren,
Waehrend die eigentliche Arbeit von einem leistungsfaehigeren Modell erledigt wird.
```

### Story 4: Robuster Fallback
```
Als Entwickler,
Wenn das LLM-Sharding fehlschlaegt (Timeout, Parse-Error),
Will ich dass das System automatisch auf Single-Shard zurueckfaellt,
Sodass die Pipeline trotzdem laeuft (wenn auch ohne Parallelisierung).
```

## Success Metrics
- [ ] Einfache Textaufgaben werden auf konfigurierte Instanzen verteilt
- [ ] LLM-Sharding nutzt standardmaessig den `cli_provider` der Rolle
- [ ] Fallback auf Single-Shard bei LLM-Fehlern funktioniert zuverlaessig
- [ ] Sharding-Latenz < 30 Sekunden fuer typische Aufgaben
- [ ] Shard-Qualitaet: Aufgaben sind logisch getrennt und unabhaengig bearbeitbar

## Non-Goals
- Dynamisches Re-Sharding waehrend der Ausfuehrung (V2 Feature)
- Lernende Sharding-Strategien ueber mehrere Runs (V2 Feature)
- Automatische Erkennung der optimalen Shard-Anzahl (nutzt `instances` Konfiguration)
- Projektlead-Rolle mit kontinuierlicher Koordination (separates Feature)

## Konfigurationsbeispiele

### Minimal (nutzt Role-Provider)
```json
{
  "id": "implementer",
  "instances": 3,
  "cli_provider": "codex",
  "shard_mode": "llm"
}
```

### Mit separatem Sharding-LLM
```json
{
  "id": "implementer",
  "instances": 4,
  "cli_provider": "claude",
  "model": "opus",
  "shard_mode": "llm",
  "shard_llm": {
    "provider": "claude",
    "model": "haiku"
  }
}
```

### Mit erweiterten Optionen
```json
{
  "id": "implementer",
  "instances": 3,
  "cli_provider": "codex",
  "shard_mode": "llm",
  "shard_llm_options": {
    "timeout_sec": 60,
    "max_retries": 2,
    "fallback_mode": "single",
    "output_format": "json"
  }
}
```

## Abhaengigkeiten
- Bestehendes Sharding-System (`multi_agent/sharding.py`)
- CLI-Adapter System (`multi_agent/cli_adapter.py`)
- Models (`multi_agent/models.py` - RoleConfig)

## Risiken und Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| LLM gibt unparsbaren Output | Mittel | Niedrig | Robuster Fallback auf Single-Shard |
| Schlechte Aufteilungsqualitaet | Niedrig | Mittel | Klar strukturierter Prompt, Validierung |
| Hohe Latenz durch LLM-Call | Niedrig | Niedrig | Timeout-Konfiguration, guenstiges LLM |
| Inkonsistente Provider-APIs | Niedrig | Mittel | Abstraction durch cli_adapter |
