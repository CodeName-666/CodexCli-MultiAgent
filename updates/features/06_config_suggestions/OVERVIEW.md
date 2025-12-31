# Feature 06: Workspace-Aware Config Suggestions

## Quick Summary
Auto-detect project type, suggest appropriate family, remember successful task→family mappings.

## Priority: 🟢 COULD HAVE
- **Impact**: ⭐⭐
- **Effort**: Medium (3-4 days)
- **ROI**: Faster onboarding, less manual config selection

## Key Features
1. **Project Type Detection**: package.json → developer, Figma → designer
2. **Task Analysis**: "Add login" → developer, "Color scheme" → designer
3. **.codexrc File**: Workspace-local preferences
4. **Learning System**: Remember successful mappings
5. **Interactive Wizard**: Guided config selection

## Example Workflow
```bash
$ python multi_agent_codex.py --task "Add authentication"

🔍 Analyzing workspace...
  Detected: Python project (found pyproject.toml)
  Task keywords: auth, security, backend

💡 Suggested config: config/developer_main.json
   (83% confidence based on project type + task analysis)

Use suggested config? [Y/n]
```

## Implementation
```python
class ConfigSuggester:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.history = self._load_history()

    def suggest(self, task: str) -> ConfigSuggestion:
        # 1. Detect project type
        project_type = detect_project_type(self.workspace)

        # 2. Analyze task keywords
        task_category = analyze_task(task)

        # 3. Check history
        historical_match = self.history.find_similar(task)

        # 4. Combine signals
        return self._rank_configs(project_type, task_category, historical_match)

# .codexrc support
{
  "default_family": "developer",
  "task_mappings": {
    "ui": "designer",
    "docs": "docs",
    "test": "qa"
  }
}
```

## Files
- `multi_agent/config_suggester.py` (new, ~400 lines)
- `multi_agent/history_tracker.py` (new, ~150 lines)
- `multi_agent/cli.py` (integrate suggestions, ~30 lines)

See `IMPLEMENTATION.md` for full details.
