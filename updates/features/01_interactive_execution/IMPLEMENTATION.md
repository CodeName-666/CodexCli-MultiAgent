# Implementation Plan: Interactive Execution Mode

## Architecture

### Core Components

#### 1. Interactive Controller (`multi_agent/interactive.py`)
```python
class InteractiveController:
    """Manages interactive execution flow."""

    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.state = ExecutionState()

    async def checkpoint(
        self,
        agent_name: str,
        output: str,
        context: Dict[str, Any]
    ) -> InteractiveAction:
        """
        Pause execution and prompt user for action.

        Returns:
            InteractiveAction: continue, retry, edit, skip, abort
        """
        pass
```

#### 2. Execution State Manager (`multi_agent/execution_state.py`)
```python
@dataclass
class ExecutionState:
    """Persistent pipeline execution state."""

    run_id: str
    completed_agents: List[str]
    agent_outputs: Dict[str, str]
    current_agent: Optional[str]
    timestamp: float

    def save(self, path: Path) -> None:
        """Persist state to JSON file."""
        pass

    @classmethod
    def load(cls, path: Path) -> "ExecutionState":
        """Load state from JSON file."""
        pass
```

#### 3. Interactive Actions (`multi_agent/interactive_actions.py`)
```python
from enum import Enum

class InteractiveAction(Enum):
    CONTINUE = "continue"     # Proceed to next agent
    RETRY = "retry"          # Re-run current agent
    EDIT = "edit"            # Edit output before continue
    SKIP = "skip"            # Skip current agent
    ABORT = "abort"          # Stop pipeline
    SAVE = "save"            # Save state and exit

class ActionPrompt:
    """Terminal prompts for user interaction."""

    @staticmethod
    def show_menu(agent_name: str, output_preview: str) -> InteractiveAction:
        """Display interactive menu and get user choice."""
        pass

    @staticmethod
    def edit_output(current_output: str) -> str:
        """Open editor for output modification."""
        pass

    @staticmethod
    def edit_prompt(current_prompt: str) -> str:
        """Open editor for prompt modification."""
        pass
```

### Integration Points

#### 1. Pipeline Modification (`multi_agent/pipeline.py`)
```python
# Current location: around line 450-500 (after agent execution)

async def _run_role_instance(self, ...):
    # ... existing code ...

    # Execute agent
    result = await self._exec_agent(...)

    # NEW: Interactive checkpoint
    if self.interactive_controller.enabled:
        action = await self.interactive_controller.checkpoint(
            agent_name=agent_name,
            output=result.stdout,
            context={
                'role_id': role_cfg.id,
                'instance': instance_num,
                'dependencies': completed_deps
            }
        )

        if action == InteractiveAction.RETRY:
            # Modify prompt and retry
            new_prompt = ActionPrompt.edit_prompt(prompt)
            result = await self._exec_agent(..., prompt=new_prompt)

        elif action == InteractiveAction.EDIT:
            # Edit output
            result.stdout = ActionPrompt.edit_output(result.stdout)

        elif action == InteractiveAction.SKIP:
            # Mark as skipped, use placeholder output
            result.stdout = f"[SKIPPED by user]\n"

        elif action == InteractiveAction.ABORT:
            # Save state and exit
            self.save_state()
            raise InterruptedError("User aborted pipeline")

        elif action == InteractiveAction.SAVE:
            # Save state for later resume
            self.save_state()
            sys.exit(0)

    # Continue with existing output validation...
```

#### 2. CLI Integration (`multi_agent/cli.py`)
```python
# Add new argument
parser.add_argument(
    '--interactive',
    action='store_true',
    help='Enable interactive mode (pause after each agent)'
)

parser.add_argument(
    '--resume',
    type=str,
    metavar='RUN_ID',
    help='Resume interrupted run from saved state'
)

# In main()
async def _run_task(...):
    # Load state if resuming
    if args.resume:
        state = ExecutionState.load(run_dir / args.resume / "state.json")
        pipeline.restore_state(state)

    # Enable interactive mode
    if args.interactive:
        pipeline.enable_interactive_mode()

    # Run pipeline
    await pipeline.run(args, cfg)
```

### State Persistence

#### State File Structure
```json
{
  "run_id": "2025-12-31_15-30-45",
  "config_path": "config/developer_main.json",
  "task": "Implement user login",
  "workspace": "/path/to/project",
  "timestamp": 1704034245.0,
  "completed_agents": [
    "architect_1",
    "implementer_1"
  ],
  "current_agent": "tester_1",
  "agent_outputs": {
    "architect_1": "# Architektur\n...",
    "implementer_1": "# Implementierung\n..."
  },
  "snapshot": "<snapshot_hash>",
  "metadata": {
    "interactive_edits": ["implementer_1"],
    "retries": {"architect_1": 1}
  }
}
```

#### Storage Location
```
.multi_agent_runs/2025-12-31_15-30-45/
├── state.json              # Execution state
├── snapshot.txt            # Workspace snapshot
├── architect_1.md          # Completed outputs
├── implementer_1.md
└── implementer_1.edited    # User-edited version
```

## Implementation Steps

### Phase 1: Core Infrastructure (Day 1)
1. ✅ Create `interactive.py` with `InteractiveController`
2. ✅ Create `execution_state.py` with state persistence
3. ✅ Create `interactive_actions.py` with action handling
4. ✅ Add unit tests for state save/load

### Phase 2: Pipeline Integration (Day 2)
1. ✅ Modify `pipeline.py` to add checkpoint calls
2. ✅ Implement resume-from-state logic
3. ✅ Add state cleanup on successful completion
4. ✅ Handle interruption (Ctrl+C) gracefully

### Phase 3: User Interface (Day 3)
1. ✅ Implement terminal menu with `rich` library
2. ✅ Add editor integration (EDITOR env var, fallback to nano)
3. ✅ Add output preview with syntax highlighting
4. ✅ Add progress indicator showing pipeline position

### Phase 4: Testing & Polish
1. ✅ Integration tests for interactive flow
2. ✅ Test resume functionality
3. ✅ Test all action types (continue, retry, edit, skip, abort)
4. ✅ Documentation and examples

## Technical Details

### Terminal UI (using `rich`)
```python
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt

def show_interactive_menu(agent_name: str, output: str) -> InteractiveAction:
    console = Console()

    # Show output preview
    syntax = Syntax(output[:1000], "markdown", theme="monokai")
    console.print(Panel(syntax, title=f"Output from {agent_name}"))

    # Show menu
    console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
    console.print("  [1] Continue to next agent")
    console.print("  [2] Retry this agent (edit prompt)")
    console.print("  [3] Edit output before continuing")
    console.print("  [4] Skip this agent")
    console.print("  [5] Save state and exit")
    console.print("  [6] Abort pipeline")

    choice = Prompt.ask("Choice", choices=["1", "2", "3", "4", "5", "6"], default="1")

    action_map = {
        "1": InteractiveAction.CONTINUE,
        "2": InteractiveAction.RETRY,
        "3": InteractiveAction.EDIT,
        "4": InteractiveAction.SKIP,
        "5": InteractiveAction.SAVE,
        "6": InteractiveAction.ABORT
    }

    return action_map[choice]
```

### Editor Integration
```python
import os
import subprocess
import tempfile

def edit_text(text: str, title: str = "Edit") -> str:
    """Open editor for text modification."""
    editor = os.environ.get('EDITOR', 'nano')

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as f:
        f.write(f"# {title}\n\n")
        f.write(text)
        temp_path = f.name

    try:
        subprocess.run([editor, temp_path], check=True)
        with open(temp_path, 'r') as f:
            content = f.read()
            # Remove title header
            lines = content.split('\n')
            if lines[0].startswith('# '):
                return '\n'.join(lines[2:])  # Skip title and blank line
            return content
    finally:
        os.unlink(temp_path)
```

## Configuration

### defaults.json Addition
```json
{
  "interactive": {
    "enabled": false,
    "auto_save_interval": 300,
    "editor": "$EDITOR",
    "output_preview_lines": 50,
    "checkpoint_delay_sec": 2
  }
}
```

### Per-Role Configuration
```json
{
  "roles": [
    {
      "id": "architect",
      "interactive_checkpoint": true,  // Always pause after this role
      "auto_continue": false
    },
    {
      "id": "implementer",
      "interactive_checkpoint": false,  // Don't pause (unless --interactive)
      "auto_continue": true
    }
  ]
}
```

## Error Handling

### Scenarios
1. **User aborts during edit**: Revert to original output, show menu again
2. **Editor fails to launch**: Fallback to inline editing (prompt for input)
3. **State file corrupted**: Error message, refuse to resume
4. **Disk full during state save**: Warning, continue without save
5. **Interrupted network during retry**: Preserve state, allow resume

## Backward Compatibility
- Interactive mode is **opt-in** via `--interactive` flag
- Default behavior unchanged (non-interactive)
- Existing scripts/CI pipelines unaffected
- State files optional, only created when needed

## Dependencies
- `rich>=13.0.0` - Terminal UI
- No additional dependencies (uses stdlib for editor, tempfile)

## Testing Strategy

### Unit Tests
```python
# tests/test_interactive.py
def test_state_save_load():
    state = ExecutionState(...)
    state.save(path)
    loaded = ExecutionState.load(path)
    assert state == loaded

def test_checkpoint_continue():
    controller = InteractiveController(enabled=True)
    # Mock user input "1" (continue)
    action = controller.checkpoint(...)
    assert action == InteractiveAction.CONTINUE
```

### Integration Tests
```python
# tests/integration/test_interactive_pipeline.py
async def test_interactive_resume():
    # Start pipeline with --interactive
    # Simulate user choosing "save and exit" after architect
    # Resume with --resume <run_id>
    # Verify architect output reused, tester runs next
```

## Documentation Updates
- [ ] Update README.md with `--interactive` flag
- [ ] Add interactive mode section to QUICKSTART.md
- [ ] Create INTERACTIVE_MODE.md guide with examples
- [ ] Add troubleshooting section for resume issues

## Future Enhancements
- Web UI for remote interactive sessions
- Automatic checkpoints at high-risk agents (based on failure history)
- Collaborative mode (multiple users review outputs)
- Output diff view (compare retry attempts)
