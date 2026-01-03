# Implementation: Web-UI für Provider Management

## Project Structure

```
codex_web_ui/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── configs.py          # Config CRUD endpoints
│   │   ├── providers.py        # Provider management
│   │   ├── runs.py             # Run management
│   │   └── stats.py            # Analytics endpoints
│   ├── websocket/
│   │   └── run_monitor.py      # WebSocket server for live updates
│   ├── models/
│   │   ├── config.py           # Pydantic models for configs
│   │   ├── run.py              # Run models
│   │   └── provider.py         # Provider models
│   ├── services/
│   │   ├── config_service.py   # Business logic for configs
│   │   ├── run_service.py      # Run execution logic
│   │   └── provider_service.py # Provider health checks
│   └── db/
│       ├── database.py          # SQLite connection
│       └── models.py            # SQLAlchemy models
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfigEditor/
│   │   │   │   ├── ConfigEditor.tsx
│   │   │   │   ├── RoleCard.tsx
│   │   │   │   └── ProviderSelect.tsx
│   │   │   ├── Monitoring/
│   │   │   │   ├── RunMonitor.tsx
│   │   │   │   ├── AgentCard.tsx
│   │   │   │   └── LiveOutput.tsx
│   │   │   ├── History/
│   │   │   │   ├── RunHistory.tsx
│   │   │   │   ├── RunFilters.tsx
│   │   │   │   └── RunDetails.tsx
│   │   │   └── Dashboard/
│   │   │       ├── Overview.tsx
│   │   │       ├── CostChart.tsx
│   │   │       └── ProviderHealth.tsx
│   │   ├── hooks/
│   │   │   ├── useConfigs.ts       # TanStack Query hooks
│   │   │   ├── useRuns.ts
│   │   │   └── useWebSocket.ts     # WebSocket hook
│   │   ├── stores/
│   │   │   └── uiStore.ts          # Zustand store
│   │   ├── api/
│   │   │   └── client.ts           # Axios client
│   │   └── types/
│   │       └── index.ts            # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
└── setup.py                    # Install script
```

## Backend Implementation

### 1. FastAPI Main App

**File**: `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio

from .api import configs, providers, runs, stats
from .websocket import run_monitor
from .db import database

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Codex UI",
    description="Web UI for Multi-CLI Provider Management",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO for WebSockets
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:5173"]
)
socket_app = socketio.ASGIApp(sio, app)

# Include API routers
app.include_router(configs.router, prefix="/api/configs", tags=["configs"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

# Mount static files (production build)
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

# Lifecycle events
@app.on_event("startup")
async def startup():
    await database.init_db()
    await run_monitor.start(sio)

@app.on_event("shutdown")
async def shutdown():
    await run_monitor.stop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8080)
```

### 2. WebSocket Run Monitor

**File**: `backend/websocket/run_monitor.py`

```python
import asyncio
import socketio
from pathlib import Path
from typing import Dict, Set

from ..services.run_service import RunService

class RunMonitor:
    """
    Monitors running pipelines and broadcasts updates via WebSocket.
    """

    def __init__(self):
        self.sio: socketio.AsyncServer | None = None
        self.active_subscriptions: Dict[str, Set[str]] = {}  # run_id -> {sid, ...}
        self.monitoring_task: asyncio.Task | None = None

    async def start(self, sio: socketio.AsyncServer):
        """Start monitoring service."""
        self.sio = sio

        # Register Socket.IO event handlers
        @sio.on("subscribe_run")
        async def subscribe(sid, data):
            run_id = data.get("run_id")
            if run_id not in self.active_subscriptions:
                self.active_subscriptions[run_id] = set()
            self.active_subscriptions[run_id].add(sid)
            print(f"Client {sid} subscribed to run {run_id}")

        @sio.on("unsubscribe_run")
        async def unsubscribe(sid, data):
            run_id = data.get("run_id")
            if run_id in self.active_subscriptions:
                self.active_subscriptions[run_id].discard(sid)

        @sio.on("disconnect")
        async def disconnect(sid):
            # Remove from all subscriptions
            for run_id in self.active_subscriptions:
                self.active_subscriptions[run_id].discard(sid)

        # Start monitoring loop
        self.monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop monitoring service."""
        if self.monitoring_task:
            self.monitoring_task.cancel()

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Check all subscribed runs for updates
                for run_id, subscribers in list(self.active_subscriptions.items()):
                    if not subscribers:
                        continue

                    # Get run updates from RunService
                    updates = await self._get_run_updates(run_id)
                    if updates:
                        # Broadcast to all subscribers
                        for subscriber_sid in subscribers:
                            await self.sio.emit(
                                "run_progress",
                                updates,
                                room=subscriber_sid
                            )

                await asyncio.sleep(0.5)  # 500ms update interval

            except Exception as e:
                print(f"Error in monitor loop: {e}")
                await asyncio.sleep(1)

    async def _get_run_updates(self, run_id: str) -> Dict | None:
        """Get latest updates for a run."""
        # Read run metadata and agent outputs
        # Return progress updates
        # (Implementation depends on how pipeline stores progress)
        pass

run_monitor = RunMonitor()
```

### 3. Config API

**File**: `backend/api/configs.py`

```python
from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List

from ..models.config import ConfigResponse, ConfigCreate, ConfigUpdate
from ..services.config_service import ConfigService

router = APIRouter()
config_service = ConfigService()

@router.get("/", response_model=List[ConfigResponse])
async def list_configs():
    """List all available configs."""
    return await config_service.list_configs()

@router.get("/{family_id}", response_model=ConfigResponse)
async def get_config(family_id: str):
    """Get a specific config."""
    config = await config_service.get_config(family_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.post("/", response_model=ConfigResponse)
async def create_config(config: ConfigCreate):
    """Create a new config."""
    return await config_service.create_config(config)

@router.put("/{family_id}", response_model=ConfigResponse)
async def update_config(family_id: str, config: ConfigUpdate):
    """Update an existing config."""
    updated = await config_service.update_config(family_id, config)
    if not updated:
        raise HTTPException(status_code=404, detail="Config not found")
    return updated

@router.delete("/{family_id}")
async def delete_config(family_id: str):
    """Delete a config."""
    success = await config_service.delete_config(family_id)
    if not success:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"status": "deleted"}
```

## Frontend Implementation

### 1. Config Editor Component

**File**: `frontend/src/components/ConfigEditor/ConfigEditor.tsx`

```typescript
import { useState } from 'react';
import { useConfigs, useUpdateConfig } from '@/hooks/useConfigs';
import { RoleCard } from './RoleCard';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

export function ConfigEditor({ familyId }: { familyId: string }) {
  const { data: config, isLoading } = useConfigs(familyId);
  const updateConfig = useUpdateConfig();
  const [editedConfig, setEditedConfig] = useState(config);

  const handleRoleUpdate = (roleId: string, updates: any) => {
    setEditedConfig(prev => ({
      ...prev,
      roles: prev.roles.map(role =>
        role.id === roleId ? { ...role, ...updates } : role
      )
    }));
  };

  const handleSave = async () => {
    await updateConfig.mutateAsync({
      familyId,
      config: editedConfig
    });
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          Config Editor: {familyId}
        </h1>
        <div className="flex gap-2">
          <Button onClick={handleSave}>Save</Button>
          <Button variant="outline">Run</Button>
        </div>
      </div>

      <Card className="p-4">
        <div className="space-y-2">
          <label>Description</label>
          <input
            value={editedConfig.cli.description}
            onChange={(e) => setEditedConfig({
              ...editedConfig,
              cli: { ...editedConfig.cli, description: e.target.value }
            })}
            className="w-full p-2 border rounded"
          />
        </div>
      </Card>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Roles</h2>
        {editedConfig.roles.map((role) => (
          <RoleCard
            key={role.id}
            role={role}
            onUpdate={(updates) => handleRoleUpdate(role.id, updates)}
          />
        ))}
      </div>

      <Card className="p-4 bg-green-50">
        <div className="text-sm">
          <strong>Estimated Cost per Run:</strong> ${estimateCost(editedConfig).toFixed(2)}
          <span className="ml-2 text-green-600">
            (-{getSavingsPercent(editedConfig)}% vs all Opus)
          </span>
        </div>
      </Card>
    </div>
  );
}
```

### 2. Live Run Monitor

**File**: `frontend/src/components/Monitoring/RunMonitor.tsx`

```typescript
import { useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { AgentCard } from './AgentCard';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

export function RunMonitor({ runId }: { runId: string }) {
  const { data: runState, subscribe, pause, cancel } = useWebSocket(runId);

  useEffect(() => {
    subscribe(runId);
    return () => unsubscribe(runId);
  }, [runId]);

  if (!runState) return <div>Connecting...</div>;

  const progress = (runState.completed_agents / runState.total_agents) * 100;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Run: {runId}</h1>
          <p className="text-gray-600">Task: "{runState.task}"</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={pause}>Pause</Button>
          <Button variant="destructive" onClick={cancel}>Cancel</Button>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Elapsed: {runState.elapsed}</span>
          <span>ETA: {runState.eta}</span>
        </div>
        <Progress value={progress} />
      </div>

      <div className="space-y-2">
        {runState.agents.map((agent) => (
          <AgentCard key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}
```

### 3. WebSocket Hook

**File**: `frontend/src/hooks/useWebSocket.ts`

```typescript
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

let socket: Socket | null = null;

export function useWebSocket(runId: string) {
  const [runState, setRunState] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    if (!socket) {
      socket = io('http://localhost:8080', {
        transports: ['websocket']
      });
    }

    // Subscribe to run updates
    socket.emit('subscribe_run', { run_id: runId });

    // Listen for updates
    socket.on('run_progress', (data) => {
      setRunState(data);
    });

    socket.on('run_completed', (data) => {
      setRunState(data);
    });

    return () => {
      socket.emit('unsubscribe_run', { run_id: runId });
    };
  }, [runId]);

  return {
    data: runState,
    subscribe: (id: string) => socket?.emit('subscribe_run', { run_id: id }),
    pause: () => socket?.emit('pause_run', { run_id: runId }),
    cancel: () => socket?.emit('cancel_run', { run_id: runId })
  };
}
```

## Installation & Deployment

### Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:socket_app --reload --port 8080

# Frontend
cd frontend
npm install
npm run dev  # Vite dev server on port 5173
```

### Production Build

```bash
# Build frontend
cd frontend
npm run build  # Output to dist/

# Start server (serves built frontend + API)
cd backend
python main.py
```

### Docker (Optional)

```dockerfile
FROM python:3.11
WORKDIR /app

# Install backend deps
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Build and copy frontend
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Expose port
EXPOSE 8080

# Run
CMD ["python", "backend/main.py"]
```

## Testing

### Backend Tests
```bash
pytest backend/tests/
```

### Frontend Tests
```bash
npm run test  # Vitest
```

### E2E Tests
```bash
playwright test  # Playwright
```

## Performance Targets

- **Initial Load**: < 2s
- **Config Save**: < 500ms
- **WebSocket Latency**: < 100ms
- **Run History Load**: < 1s (1000 runs)

## Security Checklist

- ✅ CORS restricted to localhost
- ✅ No eval() or dangerous HTML
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (Pydantic + SQLAlchemy)
- ✅ Rate limiting on API endpoints
- ✅ File access sandboxed to config directory

## Rollout Plan

### Week 1-2: Backend Foundation
- FastAPI setup
- Basic CRUD endpoints
- WebSocket server
- Database schema

### Week 3-4: Frontend Core
- Config Editor
- Live Monitoring
- Basic styling

### Week 5: Polish
- Run History
- Analytics
- Error handling
- Documentation

### Week 6: Testing & Deployment
- E2E tests
- Performance optimization
- Docker setup
- User documentation
