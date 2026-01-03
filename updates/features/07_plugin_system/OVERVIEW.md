# Feature 07: Plugin System for Custom Workflows

## Quick Summary
Extensible architecture for custom subcommands, metrics backends, and workflow plugins.

## Priority: 🟢 COULD HAVE
- **Impact**: ⭐⭐
- **Effort**: High (5-6 days)
- **ROI**: Power-user extensibility

## Key Features
1. **Custom Subcommands**: Plugin-based CLI extensions
2. **Workflow Hooks**: Pre/post agent execution hooks
3. **Metrics Backends**: Pluggable Prometheus, DataDog, etc.
4. **Output Formatters**: Custom output formats (JSON, HTML, etc.)
5. **Auto-Discovery**: Plugins loaded from `~/.codex/plugins/`

## Example Plugin
```python
# ~/.codex/plugins/pr_review/plugin.py

from multi_agent.plugin_api import Plugin, CLICommand, WorkflowHook

class PRReviewPlugin(Plugin):
    name = "pr-review"
    version = "1.0.0"

    def register_commands(self) -> List[CLICommand]:
        return [
            CLICommand(
                name="pr-review",
                handler=self.review_pr,
                help="Auto-review pull request"
            )
        ]

    async def review_pr(self, pr_number: int):
        # Fetch PR via GitHub API
        # Create task from PR diff
        # Run reviewer family
        # Post comments on PR
        pass

    def register_hooks(self) -> List[WorkflowHook]:
        return [
            WorkflowHook(
                event="agent.completed",
                handler=self.log_to_slack
            )
        ]

# Usage:
# python multi_agent_codex.py pr-review --pr 123
```

## Plugin API
```python
# multi_agent/plugin_api.py

class PluginAPI:
    """Stable API for plugin developers."""

    # Core pipeline access
    def run_family(self, family: str, task: str) -> RunResult
    def get_agent_output(self, agent_name: str) -> str
    def apply_diff(self, diff: str) -> bool

    # Configuration
    def get_config(self, key: str) -> Any
    def set_workspace_config(self, key: str, value: Any)

    # Events
    def on(self, event: str, handler: Callable)
    def emit(self, event: str, data: Any)
```

## Files
- `multi_agent/plugin_api.py` (new, ~300 lines)
- `multi_agent/plugin_loader.py` (new, ~200 lines)
- `multi_agent/cli.py` (plugin integration, ~50 lines)

See `IMPLEMENTATION.md` for full details.
