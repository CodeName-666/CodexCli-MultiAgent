# Quick Start: Eigene Konfiguration erstellen

Ein Schritt-für-Schritt Guide zum Erstellen deiner ersten eigenen `*_main.json` Konfiguration.

---

## Inhaltsverzeichnis

1. [Wann brauche ich eine eigene Config?](#wann-brauche-ich-eine-eigene-config)
2. [Option 0: Family Creator (NEU!)](#option-0-family-creator-automatisch)
3. [Option 1: Existierende Config verwenden](#option-1-existierende-config-verwenden)
4. [Option 2: Eigene Config erstellen](#option-2-eigene-config-erstellen)
5. [Option 3: Von Minimal-Template starten](#option-3-von-minimal-template-starten)
6. [Nächste Schritte](#nächste-schritte)

---

## Wann brauche ich eine eigene Config?

### ✅ **Erstelle eine neue Config wenn:**
- Du eine neue Rollen-Familie brauchst (z.B. "Marketing", "Legal")
- Du eine existierende Familie stark anpassen willst
- Du projektspezifische System-Regeln definieren möchtest
- Du mit Sharding experimentieren willst

### ❌ **Nutze existierende Config wenn:**
- Deine Aufgabe in eine vorhandene Familie passt (Developer, Designer, QA, etc.)
- Du nur den Task ändern willst (nutze `--task` Parameter)
- Du nur Timeouts/Instanzen anpassen willst (können als CLI-Args übergeben werden)

**Vorhandene Familien:**
- `developer_main.json` - Software-Entwicklung
- `designer_main.json` - UI/UX Design
- `docs_main.json` - Dokumentation
- `qa_main.json` - Testing & QA
- `devops_main.json` - Infrastructure
- `security_main.json` - Security Audits
- `product_main.json` - Product Management
- `data_main.json` - Data Engineering
- `research_main.json` - Research & Analysis

---

## Option 0: Family Creator (Automatisch)

**🆕 NEU: Die schnellste Methode!**

Erstelle eine komplette Familie automatisch via Natural Language mit dem [Family Creator](FAMILY_CREATOR.md):

```bash
# Via Haupt-CLI (empfohlen)
python multi_agent_codex.py create-family \
  --description "Ein Team für Machine Learning: Daten-Analyse, Feature Engineering, Model Training, Evaluation"

# ODER direkt (eigenständig)
python creators/multi_family_creator.py \
  --description "Ein Team für Machine Learning: Daten-Analyse, Feature Engineering, Model Training, Evaluation"
```

**Was passiert:**
1. Codex generiert Familie-Struktur aus deiner Beschreibung
2. Alle Rollen werden automatisch erstellt (mit Prompts, Dependencies, etc.)
3. Dateien werden geschrieben: `agent_families/ml_team_main.json` + `agent_families/ml_team_agents/*.json`
4. **Fertig!** Familie ist sofort nutzbar

**Beispiele:**

```bash
# GraphQL Backend (klone Developer-Familie)
python multi_agent_codex.py create-family \
  --description "GraphQL Backend Team: Schema Design, Resolver, Testing" \
  --template-from developer \
  --template-mode clone

# Video Production (von Grund auf)
python multi_agent_codex.py create-family \
  --description "Video Content Team: Storyboard, Editing, Sound, Publishing" \
  --optimize-roles \
  --interactive
```

**Wann nutzen:**
- ✅ Neue Familie schnell erstellen
- ✅ Codex soll Struktur vorschlagen
- ✅ Keine manuelle JSON-Arbeit

**Vollständige Dokumentation:** [FAMILY_CREATOR.md](FAMILY_CREATOR.md)

---

## Option 1: Existierende Config verwenden

Die einfachste Methode - nutze eine vorhandene Config:

```bash
# Developer-Familie (Standard)
python -m multi_agent.cli \
  --config agent_families/developer_main.json \
  --task "Implementiere User-Login mit JWT"

# Designer-Familie
python -m multi_agent.cli \
  --config agent_families/designer_main.json \
  --task "Entwirf ein Dashboard UI"

# QA-Familie
python -m multi_agent.cli \
  --config agent_families/qa_main.json \
  --task "Erstelle Testplan für Login-Feature"
```

**Vorteil:** Sofort einsatzbereit, keine Konfiguration nötig.

---

## Option 2: Eigene Config erstellen

### Schritt 1: Basis-Config als Template kopieren

Kopiere eine existierende Config, die deiner Anforderung am nächsten kommt:

```bash
# Für Code-Tasks: Developer als Basis
cp agent_families/developer_main.json agent_families/my_project_main.json

# Für Design-Tasks: Designer als Basis
cp agent_families/designer_main.json agent_families/my_design_main.json

# Für Dokumentation: Docs als Basis
cp agent_families/docs_main.json agent_families/my_docs_main.json
```

### Schritt 2: Anpassen

Öffne deine neue Config und passe die wichtigsten Felder an:

**NEU (mit defaults.json):**
```json
{
  "final_role_id": "implementer",
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "instances": 1
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 1,
      "depends_on": ["architect"],
      "apply_diff": true
    }
  ],
  "cli": {
    "description": "Multi-Agent Orchestrator für [DEIN BEREICH]"
  },
  "diff_safety": {
    "allowlist": [
      "agent_families/my_project_main.json",
      "agent_families/my_project_agents/*"
    ]
  }
}
```

**Wichtige Anpassungen:**

1. **`roles`** - Welche Agenten sollen laufen (und in welcher Reihenfolge)
2. **`final_role_id`** - Welche Rolle liefert das finale Ergebnis
3. **`cli.description`** - Beschreibung deiner Familie
4. **`diff_safety.allowlist`** - Erlaubte Pfade für Diff-Anwendung
5. **`instances`** - Anzahl paralleler Instanzen pro Rolle

**Hinweis:** Alle anderen Werte (system_rules, codex, limits, messages, etc.) werden automatisch aus `agent_families/defaults.json` geladen. Falls du diese anpassen willst, kannst du sie in deiner Family-Config überschreiben.

### Schritt 3: Testen

```bash
python -m multi_agent.cli \
  --config agent_families/my_project_main.json \
  --task "Teste die neue Config" \
  --validate-config
```

Der `--validate-config` Flag prüft die Config auf Fehler und bricht ab, ohne Agenten zu starten.

### Schritt 4: Produktiv nutzen

```bash
python -m multi_agent.cli \
  --config agent_families/my_project_main.json \
  --task "@tasks/my_task.md" \
  --apply
```

---

## Option 3: Von Minimal-Template starten

Wenn du ganz von vorne anfangen willst, nutze das Minimal-Template:

### Schritt 1: Template kopieren

```bash
cp examples/minimal_template.json agent_families/my_minimal_main.json
```

### Schritt 2: Verstehen

Das Minimal-Template enthält nur das Nötigste:

**NEU (mit defaults.json):**
```json
{
  "final_role_id": "implementer",
  "roles": [
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 1,
      "apply_diff": true
    }
  ],
  "cli": {
    "description": "Minimal-Config für direkte Code-Implementierung"
  }
}
```

**Was passiert:**
- Nur **eine Rolle** (Implementer) läuft
- Keine Pipeline, keine Dependencies
- Perfekt für einfache, direkte Tasks
- Alle anderen Werte kommen aus `defaults.json`

### Schritt 3: Erweitern

Füge nach Bedarf weitere Rollen hinzu:

```json
{
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "instances": 1
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 1,
      "depends_on": ["architect"],  // ← Läuft nach architect
      "apply_diff": true
    },
    {
      "id": "tester",
      "file": "developer_agents/tester.json",
      "instances": 1,
      "depends_on": ["implementer"]  // ← Läuft nach implementer
    }
  ]
}
```

---

## Häufige Anpassungen

### 1. Parallelisierung aktivieren

```json
{
  "roles": [
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "instances": 3,  // ← 3 parallele Instanzen
      "shard_mode": "headings",  // ← Task wird aufgeteilt
      "apply_diff": true
    }
  ]
}
```

**Wann:** Große Tasks mit mehreren unabhängigen Features.

### 2. Rollen entfernen

Du brauchst nicht immer alle Rollen:

```json
{
  "roles": [
    // "architect" auskommentiert oder gelöscht
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "depends_on": []  // ← Keine Dependencies mehr
    }
    // "tester", "reviewer" weggelassen
  ]
}
```

**Wann:** Schnelle Prototypen, einfache Bugfixes.

### 3. Timeouts anpassen

```json
{
  "role_defaults": {
    "timeout_sec": 3600  // ← 60 Minuten für alle Rollen
  },
  "roles": [
    {
      "id": "implementer",
      "timeout_sec": 7200  // ← Override: 120 Minuten für Implementer
    }
  ]
}
```

**Wann:** Komplexe Tasks, langsame Codex-Instanzen.

### 4. Snapshot-Optimierung (große Codebases)

```json
{
  "snapshot": {
    "max_files": 200,
    "max_file_bytes": 50000,
    "selective_context": {
      "enabled": true,
      "min_files": 10,
      "max_files": 200
    }
  }
}
```

**Wann:** Große Repositories (>1000 Dateien).

---

## Validierung & Debugging

### Config validieren

```bash
python -m multi_agent.cli \
  --config agent_families/my_config.json \
  --task "Test" \
  --validate-config
```

**Häufige Fehler:**

1. **"Role file not found"**
   ```
   Fehler: agent_families/my_agents/foo.json nicht gefunden
   Lösung: Prüfe den "file" Pfad in "roles" Array
   ```

2. **"Circular dependency"**
   ```
   Fehler: role A depends_on B, B depends_on A
   Lösung: Entferne zirkuläre Dependencies
   ```

3. **"Unknown role_id in depends_on"**
   ```
   Fehler: depends_on: ["xyz"] aber "xyz" existiert nicht
   Lösung: Prüfe Schreibweise der Role-IDs
   ```

### Dry-Run (ohne Code-Änderungen)

```bash
python -m multi_agent.cli \
  --config agent_families/my_config.json \
  --task "Test"
  # Ohne --apply Flag!
```

Outputs landen in `.multi_agent_runs/<timestamp>/`, Workspace bleibt unverändert.

---

## Nächste Schritte

### Weiterführende Dokumentation

1. **[CONFIGURATION.md](CONFIGURATION.md)** - Vollständige Config-Referenz
   - Alle verfügbaren Felder
   - Sharding-Optionen
   - Prompt-Template Platzhalter

2. **[CUSTOM_ROLES.md](CUSTOM_ROLES.md)** - Eigene Rollen erstellen
   - Wie du eigene Agent-Rollen schreibst
   - Prompt Engineering
   - Best Practices

3. **[SHARDING.md](SHARDING.md)** - Parallele Agent-Ausführung
   - Heading-based Sharding
   - Overlap-Detection
   - Advanced Sharding-Features

### Beispiele durchgehen

Schau dir die Beispiel-Configs an:

```bash
# Einfaches Sharding
cat examples/sharding_basic_config.json

# Fortgeschrittenes Sharding
cat examples/sharding_advanced_config.json

# Designer-Familie mit Sharding
cat examples/designer_sharding_config.json
```

### Experimentieren

Erstelle einen Test-Task und probiere verschiedene Configs aus:

```bash
# Erstelle einen Test-Task
cat > tasks/test.md << 'EOF'
# Feature A: Hello World
Implementiere eine hello_world.py Datei.

# Feature B: Math Utils
Implementiere eine math_utils.py mit add() und multiply().

# Feature C: String Utils
Implementiere eine string_utils.py mit reverse() und capitalize().
EOF

# Teste mit verschiedenen Configs
python -m multi_agent.cli --config agent_families/developer_main.json --task "@tasks/test.md"
python -m multi_agent.cli --config examples/sharding_basic_config.json --task "@tasks/test.md"
```

---

## Hilfe & Support

- **Fehler beim Config-Laden:** Prüfe JSON-Syntax (Kommata, Klammern)
- **Agenten liefern unerwartete Ergebnisse:** Passe `system_rules` und Prompt-Templates an
- **Performance-Probleme:** Aktiviere `selective_context` im Snapshot
- **Weitere Fragen:** Siehe [README.md](../README.md) oder [CONFIGURATION.md](CONFIGURATION.md)

---

**Los geht's! 🚀**
