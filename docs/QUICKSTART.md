# Quick Start: Eigene Konfiguration erstellen

Ein Schritt-für-Schritt Guide zum Erstellen deiner ersten eigenen `*_main.json` Konfiguration.

---

## Inhaltsverzeichnis

1. [Wann brauche ich eine eigene Config?](#wann-brauche-ich-eine-eigene-config)
2. [Option 1: Existierende Config verwenden](#option-1-existierende-config-verwenden)
3. [Option 2: Eigene Config erstellen](#option-2-eigene-config-erstellen)
4. [Option 3: Von Minimal-Template starten](#option-3-von-minimal-template-starten)
5. [Nächste Schritte](#nächste-schritte)

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

## Option 1: Existierende Config verwenden

Die einfachste Methode - nutze eine vorhandene Config:

```bash
# Developer-Familie (Standard)
python -m multi_agent.cli \
  --config config/developer_main.json \
  --task "Implementiere User-Login mit JWT"

# Designer-Familie
python -m multi_agent.cli \
  --config config/designer_main.json \
  --task "Entwirf ein Dashboard UI"

# QA-Familie
python -m multi_agent.cli \
  --config config/qa_main.json \
  --task "Erstelle Testplan für Login-Feature"
```

**Vorteil:** Sofort einsatzbereit, keine Konfiguration nötig.

---

## Option 2: Eigene Config erstellen

### Schritt 1: Basis-Config als Template kopieren

Kopiere eine existierende Config, die deiner Anforderung am nächsten kommt:

```bash
# Für Code-Tasks: Developer als Basis
cp config/developer_main.json config/my_project_main.json

# Für Design-Tasks: Designer als Basis
cp config/designer_main.json config/my_design_main.json

# Für Dokumentation: Docs als Basis
cp config/docs_main.json config/my_docs_main.json
```

### Schritt 2: Anpassen

Öffne deine neue Config und passe die wichtigsten Felder an:

```json
{
  "system_rules": "Du bist ein Experte für [DEIN BEREICH].\n\nPrinzipien:\n- [DEINE REGEL 1]\n- [DEINE REGEL 2]\n...",

  "role_defaults": {
    "timeout_sec": 1800,
    "instances": 1
  },

  "roles": [
    {
      "id": "architect",
      "file": "developer_roles/architect.json",
      "instances": 1
    },
    {
      "id": "implementer",
      "file": "developer_roles/implementer.json",
      "instances": 1,
      "depends_on": ["architect"],
      "apply_diff": true
    }
  ],

  "final_role_id": "implementer"
}
```

**Wichtige Anpassungen:**

1. **`system_rules`** - Deine globalen Regeln/Prinzipien
2. **`roles`** - Welche Agenten sollen laufen (und in welcher Reihenfolge)
3. **`final_role_id`** - Welche Rolle liefert das finale Ergebnis
4. **`instances`** - Anzahl paralleler Instanzen pro Rolle

### Schritt 3: Testen

```bash
python -m multi_agent.cli \
  --config config/my_project_main.json \
  --task "Teste die neue Config" \
  --validate-config
```

Der `--validate-config` Flag prüft die Config auf Fehler und bricht ab, ohne Agenten zu starten.

### Schritt 4: Produktiv nutzen

```bash
python -m multi_agent.cli \
  --config config/my_project_main.json \
  --task "@tasks/my_task.md" \
  --apply
```

---

## Option 3: Von Minimal-Template starten

Wenn du ganz von vorne anfangen willst, nutze das Minimal-Template:

### Schritt 1: Template kopieren

```bash
cp examples/minimal_template.json config/my_minimal_main.json
```

### Schritt 2: Verstehen

Das Minimal-Template enthält nur das Nötigste:

```json
{
  "system_rules": "Du bist ein hilfreicher Coding-Assistent.",
  "codex": {
    "env_var": "CODEX_CMD",
    "default_cmd": "codex exec -"
  },
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

**Was passiert:**
- Nur **eine Rolle** (Implementer) läuft
- Keine Pipeline, keine Dependencies
- Perfekt für einfache, direkte Tasks

### Schritt 3: Erweitern

Füge nach Bedarf weitere Rollen hinzu:

```json
{
  "roles": [
    {
      "id": "architect",
      "file": "developer_roles/architect.json",
      "instances": 1
    },
    {
      "id": "implementer",
      "file": "developer_roles/implementer.json",
      "instances": 1,
      "depends_on": ["architect"],  // ← Läuft nach architect
      "apply_diff": true
    },
    {
      "id": "tester",
      "file": "developer_roles/tester.json",
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
      "file": "developer_roles/implementer.json",
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
      "file": "developer_roles/implementer.json",
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
  --config config/my_config.json \
  --task "Test" \
  --validate-config
```

**Häufige Fehler:**

1. **"Role file not found"**
   ```
   Fehler: config/my_roles/foo.json nicht gefunden
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
  --config config/my_config.json \
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
python -m multi_agent.cli --config config/developer_main.json --task "@tasks/test.md"
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
