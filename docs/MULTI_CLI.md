# Multi-CLI Provider Support

## Übersicht

Der Multi-Agent Orchestrator unterstützt jetzt mehrere CLI-Provider, sodass verschiedene Rollen unterschiedliche KI-Interfaces nutzen können:

- **Codex CLI** (Standard)
- **Claude Code CLI** (Anthropic)
- **Google Gemini CLI**

## Warum Multi-CLI Support?

1. **Spezialisierung**: Nutze verschiedene Modelle für verschiedene Aufgaben
   - Claude Sonnet für Architektur & Planung
   - Codex für Code-Implementierung
   - Gemini Flash für schnelle Tests

2. **Kostenoptimierung**: Kleinere/günstigere Modelle für einfache Tasks
   - Claude Haiku für Zusammenfassungen
   - Gemini Flash für Validierung

3. **Flexibilität**: Teste und vergleiche verschiedene Provider
4. **Ausfallsicherheit**: Fallback wenn ein Provider überlastet ist

## Konfiguration

### 1. CLI Provider Config (`static_config/cli_config.json`)

Diese Datei definiert alle verfügbaren CLI-Provider und ihre Parameter:

```json
{
  "cli_providers": {
    "codex": {
      "name": "Codex CLI",
      "command": "codex",
      "execution_mode": "stdin",
      "env_var": "CODEX_CMD",
      "default_cmd": ["codex", "exec", "-"],
      "parameters": { ... }
    },
    "claude": {
      "name": "Claude Code CLI",
      "command": "claude",
      "execution_mode": "flag",
      "env_var": "CLAUDE_CMD",
      "default_cmd": ["claude", "-p"],
      "parameters": {
        "model": {
          "flag": "--model",
          "type": "string",
          "default": "sonnet",
          "aliases": {
            "sonnet": "claude-sonnet-4-5-20250929",
            "opus": "claude-opus-4-5-20251101",
            "haiku": "claude-3-5-haiku-20241022"
          }
        },
        "max_turns": {
          "flag": "--max-turns",
          "type": "int"
        },
        "output_format": {
          "flag": "--output-format",
          "type": "string",
          "options": ["text", "json", "stream-json"]
        },
        "allowed_tools": {
          "flag": "--allowedTools",
          "type": "string"
        }
      }
    },
    "gemini": {
      "name": "Google Gemini CLI",
      "command": "gemini",
      "execution_mode": "flag",
      "env_var": "GEMINI_CMD",
      "default_cmd": ["gemini", "-p"],
      "parameters": {
        "model": {
          "flag": "-m",
          "type": "string",
          "default": "gemini-2.5-pro",
          "options": [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash"
          ]
        },
        "output_format": {
          "flag": "--output-format",
          "type": "string"
        }
      }
    }
  },
  "default_provider": "codex",
  "timeout_multiplier": {
    "codex": 1.0,
    "claude": 1.2,
    "gemini": 1.0
  }
}
```

### 2. Rollen-Konfiguration (`*_main.json`)

Definiere den CLI-Provider pro Rolle:

```json
{
  "roles": [
    {
      "id": "architect",
      "file": "developer_agents/architect.json",
      "instances": 1,
      "cli_provider": "claude",
      "model": "sonnet",
      "cli_parameters": {
        "max_turns": 3,
        "allowed_tools": "Read,Glob,Grep"
      }
    },
    {
      "id": "implementer",
      "file": "developer_agents/implementer.json",
      "cli_provider": "codex"
    },
    {
      "id": "tester",
      "file": "developer_agents/tester.json",
      "cli_provider": "gemini",
      "model": "gemini-2.5-flash",
      "cli_parameters": {
        "temperature": 0.7
      }
    }
  ]
}
```

### 3. Rolle defaults (`defaults.json`)

Setze Standard-Provider für alle Rollen:

```json
{
  "role_defaults": {
    "timeout_sec": 1200,
    "cli_provider": "codex",
    "retries": 2
  }
}
```

## Parameter-Referenz

### Rollen-Ebene

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `cli_provider` | string | Provider-ID: "codex", "claude", "gemini" |
| `model` | string | Modell-Name (provider-spezifisch) |
| `cli_parameters` | object | Provider-spezifische Parameter |

### cli_parameters für Claude

```json
{
  "max_turns": 3,
  "output_format": "text",
  "allowed_tools": "Read,Edit,Bash",
  "system_prompt": "Du bist ein Experte...",
  "append_system_prompt": "Zusätzliche Anweisungen...",
  "verbose": false
}
```

### cli_parameters für Gemini

```json
{
  "output_format": "text",
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "include_directories": "../lib,../docs"
}
```

### cli_parameters für Codex

```json
{
  "temperature": 0.7,
  "max_tokens": 2000
}
```

## Best Practices

### 1. Architektur-Phase: Claude Sonnet

```json
{
  "id": "architect",
  "cli_provider": "claude",
  "model": "sonnet",
  "timeout_sec": 1800,
  "cli_parameters": {
    "max_turns": 3,
    "allowed_tools": "Read,Glob,Grep",
    "append_system_prompt": "Fokus auf modulare Architektur."
  }
}
```

**Warum?** Claude Sonnet ist hervorragend für komplexes Denken und Planung.

### 2. Implementierung: Codex oder Claude Opus

```json
{
  "id": "implementer",
  "cli_provider": "codex"
}
```

**Warum?** Codex ist auf Code-Generierung spezialisiert.

### 3. Tests: Gemini Flash (schnell & kostengünstig)

```json
{
  "id": "tester",
  "cli_provider": "gemini",
  "model": "gemini-2.5-flash",
  "timeout_sec": 600,
  "cli_parameters": {
    "temperature": 0.5
  }
}
```

**Warum?** Tests sind oft einfacher, Flash ist schnell genug.

### 4. Review: Claude Opus (höchste Qualität)

```json
{
  "id": "reviewer",
  "cli_provider": "claude",
  "model": "opus",
  "cli_parameters": {
    "max_turns": 2,
    "append_system_prompt": "Fokus auf Security, Performance, Maintainability."
  }
}
```

**Warum?** Opus findet subtile Bugs und Design-Issues.

### 5. Zusammenfassung: Claude Haiku (effizient)

```json
{
  "id": "integrator",
  "cli_provider": "claude",
  "model": "haiku",
  "timeout_sec": 300,
  "cli_parameters": {
    "max_turns": 1
  }
}
```

**Warum?** Zusammenfassungen sind einfach, Haiku reicht.

## Umgebungsvariablen

Override CLI-Commands per ENV:

```bash
# Codex
export CODEX_CMD="codex exec -"

# Claude
export CLAUDE_CMD="claude -p"

# Gemini
export GEMINI_CMD="gemini -p"
```

## Prioritäten

Das System wählt CLI-Provider in dieser Reihenfolge:

1. **Role-specific `cli_provider`**
   ```json
   {"cli_provider": "claude", "model": "sonnet"}
   ```

2. **Role defaults `cli_provider`**
   ```json
   {"role_defaults": {"cli_provider": "claude"}}
   ```

3. **Global default** (aus `cli_config.json`)
   ```json
   {"default_provider": "codex"}
   ```

## Kostenoptimierung

### Beispiel: Balancierte Pipeline

```json
{
  "roles": [
    {
      "id": "architect",
      "cli_provider": "claude",
      "model": "sonnet"
    },
    {
      "id": "implementer",
      "cli_provider": "codex"
    },
    {
      "id": "tester",
      "cli_provider": "gemini",
      "model": "gemini-2.5-flash"
    },
    {
      "id": "reviewer",
      "cli_provider": "claude",
      "model": "haiku"
    },
    {
      "id": "integrator",
      "cli_provider": "gemini",
      "model": "gemini-2.5-flash"
    }
  ]
}
```

**Geschätzte Kosten-Einsparung**: 60-70% vs. nur Opus/Sonnet

## Troubleshooting

### Provider nicht gefunden

```
ValueError: Unknown CLI provider: claude
```

**Lösung**: Stelle sicher, dass `agent_families/cli_config.json` existiert und den Provider definiert.

### CLI Command not found

```
FileNotFoundError: [Errno 2] No such file: 'claude'
```

**Lösung**:
1. Installiere das CLI Tool:
   ```bash
   # Claude
   npm install -g @anthropic-ai/claude-code-cli

   # Gemini
   npm install -g @google/gemini-cli
   ```

2. Oder setze ENV Variable:
   ```bash
   export CLAUDE_CMD="/path/to/claude -p"
   ```

### Timeout zu kurz

**Symptom**: Claude Modelle timeout häufiger

**Lösung**: Timeout-Multiplier erhöhen in `cli_config.json`:

```json
{
  "timeout_multiplier": {
    "claude": 1.5
  }
}
```

### Parameter werden ignoriert

**Symptom**: `cli_parameters` haben keine Wirkung

**Lösung**: Prüfe ob Parameter-Name korrekt ist:

```bash
# Test manuell
claude -p "test" --max-turns 3 --output-format text
```

Siehe `cli_config.json` für verfügbare Parameter.

## Beispiele

Siehe:
- [`agent_families/multi_cli_example.json`](../agent_families/multi_cli_example.json) - Vollständiges Beispiel
- [`static_config/cli_config.json`](../static_config/cli_config.json) - Provider-Definitionen

## Weiterführende Links

- [Claude Code CLI Docs](https://code.claude.com/docs/en/cli-reference.md)
- [Gemini CLI Docs](https://geminicli.com/docs/)
- [Codex CLI GitHub](https://github.com/openai/codex-cli)
