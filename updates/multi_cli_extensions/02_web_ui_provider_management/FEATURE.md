# Feature: Web-UI für Provider Management

## Problem Statement

Die CLI-basierte Konfiguration von Multi-Agent-Pipelines ist für erfahrene Entwickler effizient, aber:

1. **Hohe Einstiegshürde** für neue Benutzer
2. **Keine visuelle Übersicht** über laufende Agents
3. **Schwierige Fehlerdiagnose** ohne Live-Monitoring
4. **Komplexe Config-Bearbeitung** in JSON-Dateien
5. **Kein Echtzeit-Feedback** während der Ausführung

## Goals

### Primary Goals
1. **Visual Config Management** - Grafisches Interface für CLI-Provider-Konfiguration
2. **Live Monitoring** - Echtzeit-Ansicht laufender Agent-Pipelines
3. **Interactive Editing** - Drag & Drop Config-Builder
4. **Run History** - Dashboard für vergangene Runs mit Filtern
5. **Provider Health** - Status-Monitoring aller CLI-Provider

### Secondary Goals
1. **Template Editor** - Visuelle Erstellung von Provider-Templates
2. **Logs Viewer** - Durchsuchbare Agent-Logs
3. **Diff Viewer** - Visuelle Anzeige generierter Code-Diffs
4. **Cost Analytics** - Grafische Kostenübersicht
5. **Multi-User Support** - Team-Collaboration (später)

## User Stories

### Story 1: Visuelles Config-Management
```
Als nicht-technischer User
Möchte ich Konfigurationen visuell bearbeiten können
Sodass ich keine JSON-Syntax lernen muss
```

**Akzeptanzkriterien**:
- Drag & Drop Interface für Rollen-Anordnung
- Dropdowns für CLI-Provider-Auswahl
- Live-Validation während der Eingabe
- Preview der generierten JSON-Config
- Ein-Klick Export/Import

### Story 2: Live Run-Monitoring
```
Als Entwickler
Möchte ich laufende Pipelines in Echtzeit überwachen
Sodass ich sofort sehe was die Agents machen
```

**Akzeptanzkriterien**:
- Live-Update der Agent-Status (pending, running, completed, failed)
- Streaming-Output von Agent-Stdout/Stderr
- Progress-Bars für jede Rolle
- Geschätzte verbleibende Zeit
- Pause/Resume/Cancel Buttons

### Story 3: Run History & Analytics
```
Als Team Lead
Möchte ich vergangene Runs analysieren und vergleichen
Sodass ich Optimierungspotentiale identifizieren kann
```

**Akzeptanzkriterien**:
- Filterbares Run-History-Dashboard
- Success/Failure Statistiken
- Durchschnittliche Laufzeit pro Rolle
- Token-Usage & Kosten-Trends
- Run-Vergleich (Diff zwischen zwei Runs)

### Story 4: Provider Health Dashboard
```
Als DevOps
Möchte ich den Status aller CLI-Provider überwachen
Sodass ich Ausfälle frühzeitig erkenne
```

**Akzeptanzkriterien**:
- Status-Indicators (online/offline/degraded)
- Latenz-Monitoring pro Provider
- Error-Rate Tracking
- Auto-Retry Configuration
- Fallback-Provider Setup

## Technical Architecture

### Stack

#### Backend (FastAPI)
- **Framework**: FastAPI (async, modern, OpenAPI)
- **WebSockets**: For real-time updates
- **Database**: SQLite (same as cost tracking)
- **CORS**: Configured for local development

#### Frontend (React)
- **Framework**: React 18 + TypeScript
- **UI Library**: shadcn/ui (Radix + Tailwind)
- **State**: Zustand (lightweight, simple)
- **Data Fetching**: TanStack Query (caching, invalidation)
- **Routing**: React Router v6
- **Charts**: Recharts (declarative, responsive)
- **Real-time**: Socket.IO Client

#### Development
- **Build Tool**: Vite (fast HMR)
- **Linting**: ESLint + Prettier
- **Type Checking**: TypeScript strict mode

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Config      │  │ Monitoring  │  │ History     │        │
│  │ Editor      │  │ Dashboard   │  │ Analytics   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP + WebSocket
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ REST API     │  │ WebSocket    │  │ Run Manager  │     │
│  │ Endpoints    │  │ Server       │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Config   │  │  Run DB  │  │  File    │
  │ Loader   │  │ (SQLite) │  │  System  │
  └──────────┘  └──────────┘  └──────────┘
```

## UI Mockups

### 1. Config Editor

```
┌────────────────────────────────────────────────────────────┐
│  Multi-Agent Configurator                        [Save] [▶]│
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Family: developer_main                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Description: Backend development with tests            │ │
│  │ Final Role: integrator                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Roles:                                           [+ Add Role]│
│  ┌────────────────────────────────────────────────────────┐ │
│  │  🏗️  architect                          [⋮]            │ │
│  │  ├─ CLI Provider: claude ▼                              │ │
│  │  ├─ Model: sonnet ▼                                     │ │
│  │  ├─ Timeout: 1800s                                      │ │
│  │  └─ Parameters: max_turns=3, allowed_tools=...         │ │
│  │                                                          │ │
│  │  💻 implementer                        [⋮]            │ │
│  │  ├─ CLI Provider: codex ▼                               │ │
│  │  ├─ Model: (default)                                    │ │
│  │  ├─ Timeout: 1200s                                      │ │
│  │  └─ Apply Diff: ✓                                       │ │
│  │                                                          │ │
│  │  🧪 tester                            [⋮]            │ │
│  │  ├─ CLI Provider: gemini ▼                              │ │
│  │  ├─ Model: gemini-2.5-flash ▼                           │ │
│  │  └─ Parameters: temperature=0.5                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Estimated Cost per Run: $0.45    (-62% vs all Opus)       │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### 2. Live Monitoring

```
┌────────────────────────────────────────────────────────────┐
│  Run: 2025-12-31_14-30-00                [Pause] [Cancel]  │
├────────────────────────────────────────────────────────────┤
│  Task: "Add authentication system"                          │
│  Family: developer_main                                      │
│  Started: 14:30:00    Elapsed: 3m 45s    ETA: 2m 15s       │
│                                                              │
│  Pipeline Progress: ████████████░░░░ 65%                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ✅ architect                                3m 12s      │ │
│  │    Provider: claude (sonnet)                            │ │
│  │    Tokens: 4,523      Cost: $0.014                     │ │
│  │    [Show Output]                                        │ │
│  │                                                          │ │
│  │ 🔄 implementer                         1m 33s / ~3m    │ │
│  │    Provider: codex                                      │ │
│  │    Progress: ██████████████░░░░░ 70%                   │ │
│  │    ┌──────────────────────────────────────────────────┐ │ │
│  │    │ [Live Output]                                    │ │ │
│  │    │ Analyzing existing code...                       │ │ │
│  │    │ Creating auth module structure...                │ │ │
│  │    │ ▋ Generating authentication logic...             │ │ │
│  │    └──────────────────────────────────────────────────┘ │ │
│  │                                                          │ │
│  │ ⏸️  tester                                              │ │
│  │    Provider: gemini (flash)                             │ │
│  │    Waiting for: implementer                             │ │
│  │                                                          │ │
│  │ ⏸️  reviewer                                            │ │
│  │ ⏸️  integrator                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  System Metrics:                                            │
│  CPU: ██████████░░░░░ 65%    Memory: ███░░░░░░░ 28%       │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### 3. Run History

```
┌────────────────────────────────────────────────────────────┐
│  Run History                             [Filters ▼] [Export]│
├────────────────────────────────────────────────────────────┤
│  Filters: [All Families ▼] [Last 7 days ▼] [All Status ▼] │
│                                                              │
│  ┌────┬──────────────────┬─────────┬────────┬──────┬─────┐ │
│  │    │ Run ID           │ Family  │ Status │ Time │ Cost│ │
│  ├────┼──────────────────┼─────────┼────────┼──────┼─────┤ │
│  │ ✅ │ 2025-12-31_14-30 │ dev     │ Success│ 6m   │$0.42│ │
│  │ ❌ │ 2025-12-31_13-15 │ dev     │ Failed │ 2m   │$0.08│ │
│  │ ✅ │ 2025-12-31_10-00 │ designer│ Success│ 4m   │$0.35│ │
│  │ ✅ │ 2025-12-30_16-45 │ dev     │ Success│ 7m   │$0.51│ │
│  └────┴──────────────────┴─────────┴────────┴──────┴─────┘ │
│                                                              │
│  Success Rate: 75% (3/4)                                    │
│  Avg Duration: 4m 45s                                       │
│  Total Cost (7d): $1.36                                     │
│                                                              │
│  [Click row to view details]                                │
└────────────────────────────────────────────────────────────┘
```

## API Endpoints

### REST API

```
GET    /api/configs                    # List all configs
GET    /api/configs/{family_id}        # Get specific config
POST   /api/configs                    # Create new config
PUT    /api/configs/{family_id}        # Update config
DELETE /api/configs/{family_id}        # Delete config

GET    /api/providers                  # List CLI providers
GET    /api/providers/{provider_id}    # Get provider info
POST   /api/providers/health-check     # Check provider status

GET    /api/runs                       # List runs (with filters)
GET    /api/runs/{run_id}              # Get run details
POST   /api/runs                       # Start new run
PUT    /api/runs/{run_id}/pause        # Pause running pipeline
PUT    /api/runs/{run_id}/resume       # Resume paused pipeline
DELETE /api/runs/{run_id}              # Cancel running pipeline

GET    /api/templates                  # List provider templates
POST   /api/templates                  # Create custom template

GET    /api/stats/overview             # Dashboard stats
GET    /api/stats/costs                # Cost analytics
GET    /api/stats/providers            # Provider usage stats
```

### WebSocket Events

```
Client -> Server:
  subscribe_run: {run_id}              # Subscribe to run updates
  unsubscribe_run: {run_id}            # Unsubscribe

Server -> Client:
  run_started: {run_id, timestamp, ...}
  run_progress: {run_id, progress%, agent_statuses, ...}
  agent_started: {run_id, agent_name, ...}
  agent_output: {run_id, agent_name, stdout_chunk, ...}
  agent_completed: {run_id, agent_name, returncode, ...}
  run_completed: {run_id, status, final_summary, ...}
  run_error: {run_id, error_message, ...}
```

## Non-Goals

- **No Authentication** (v1) - Local-only tool
- **No Multi-Tenancy** - Single-user focus
- **No Cloud Hosting** - Self-hosted only
- **No Mobile App** - Desktop browsers only

## Success Metrics

### Quantitative
- **< 5 seconds** - Time to load Config Editor
- **< 100ms** - WebSocket message latency
- **60 FPS** - UI rendering during live updates
- **90%+** - User retention after first use

### Qualitative
- "Easier than CLI" - User feedback
- Reduced support requests about config syntax
- Increased adoption of Multi-CLI features

## Dependencies

- Multi-CLI Support (COMPLETED)
- Cost Tracking Backend (Feature 4, can be parallel)
- Run History DB (part of this feature)

## Security Considerations

- **CORS**: Whitelist only localhost
- **File Access**: Sandboxed to config directory
- **Command Injection**: No direct shell access from UI
- **Rate Limiting**: Prevent DoS on API endpoints

## Open Questions

1. **Port**: Default port 8080? Configurable?
   - **Decision**: 8080, with `--port` override

2. **Multi-Instance**: Support multiple simultaneous runs?
   - **Decision**: Yes, but warn on resource contention

3. **Persistence**: Where to store UI preferences?
   - **Decision**: `~/.codex/ui_settings.json`

4. **Offline Mode**: Should UI work without internet?
   - **Decision**: Yes, no CDN dependencies
