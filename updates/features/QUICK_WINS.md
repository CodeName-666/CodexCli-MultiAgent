# Quick Wins (<2 Days Each)

These features provide high value with minimal implementation effort.

---

## A. Config Auto-Migration

**Current**: Manual `migrate_configs.py` script
**Better**: Automatic migration on load with deprecation warnings

### Implementation
```python
# In multi_agent/config_loader.py

def load_app_config(config_path: Path) -> AppConfig:
    base_dir = config_path.parent
    defaults_path = base_dir / "defaults.json"

    # Load family config
    family_config = load_json(config_path)

    # Check if old format (has keys that should be in defaults)
    OLD_FORMAT_KEYS = {"system_rules", "codex", "messages", "snapshot"}
    has_old_keys = any(k in family_config for k in OLD_FORMAT_KEYS)

    if not defaults_path.exists() and has_old_keys:
        print("⚠️  Warning: Old config format detected.")
        print("   Consider running: python migrate_configs.py")
        # Use family_config as-is (backwards compatible)
        data = family_config
    elif defaults_path.exists():
        # New format: merge with defaults
        defaults = load_json(defaults_path)
        data = deep_merge(defaults, family_config)
    else:
        # Old format but defaults exists (migration completed elsewhere)
        data = family_config

    # ... rest of function
```

**Files to modify**: `multi_agent/config_loader.py` (5 lines added)
**Testing**: Unit test for detection, integration test for both formats
**Effort**: < 1 day

---

## B. Better Error Messages

**Current**: `"Fehler: Rolle {agent_name} lieferte rc=1. {error}"`
**Better**: Actionable error messages with suggestions

### Implementation
```python
# In multi_agent/error_formatter.py (new file)

from typing import Dict, List

class ErrorFormatter:
    """Format user-friendly error messages with suggestions."""

    ERROR_TEMPLATES = {
        "role_rc1_error": """
❌ Error: Agent '{agent_name}' failed (exit code 1)

Reason: {error}

💡 Suggestions:
{suggestions}

Debug Info:
  - Output: {output_file}
  - Config: {config_file}:{role_line}
  - Duration: {duration}s
""",
        "missing_sections": """
❌ Error: Agent '{agent_name}' output validation failed

Missing required sections:
{missing_sections}

💡 Suggestions:
  1. Check role prompt template for format instructions
  2. Review expected_sections in config
  3. Try adding explicit section requirements to prompt

Example expected output:
{example_format}
""",
        "timeout": """
⏱️  Error: Agent '{agent_name}' timed out after {timeout}s

💡 Suggestions:
  1. Increase timeout: --timeout {suggested_timeout}
  2. Simplify task (break into smaller chunks)
  3. Use task splitting: --task-split
  4. Check if Codex CLI is hanging (test: codex exec - < test_prompt.txt)
"""
    }

    @staticmethod
    def format(error_type: str, context: Dict) -> str:
        template = ErrorFormatter.ERROR_TEMPLATES.get(error_type)
        if not template:
            return context.get('error', 'Unknown error')

        # Add contextual suggestions
        suggestions = ErrorFormatter._generate_suggestions(error_type, context)
        context['suggestions'] = '\n'.join(f"  {i+1}. {s}" for i, s in enumerate(suggestions))

        return template.format(**context)

    @staticmethod
    def _generate_suggestions(error_type: str, context: Dict) -> List[str]:
        """Generate context-specific suggestions."""
        suggestions = []

        if error_type == "role_rc1_error":
            # Check common issues
            if context.get('timeout_sec', 0) < 600:
                suggestions.append(f"Increase timeout (current: {context['timeout_sec']}s)")

            if context.get('output_size', 0) == 0:
                suggestions.append("Agent produced no output - check prompt template")

            if "KeyError" in context.get('stderr', ''):
                suggestions.append("Missing placeholder in prompt - check template variables")

        elif error_type == "missing_sections":
            missing = context.get('missing_sections', [])
            suggestions.append(f"Add these sections to output: {', '.join(missing)}")
            suggestions.append("Review role's expected_sections configuration")

        return suggestions or ["Check logs for more details"]
```

**Usage in pipeline.py**:
```python
# Replace current error print with:
error_msg = ErrorFormatter.format("role_rc1_error", {
    'agent_name': agent_name,
    'error': str(exc),
    'output_file': output_path,
    'config_file': config_path,
    'role_line': get_line_number(role_cfg),
    'duration': duration,
    'timeout_sec': role_cfg.timeout_sec,
    'output_size': len(result.stdout),
    'stderr': result.stderr
})
print(error_msg, file=sys.stderr)
```

**Files**: New `multi_agent/error_formatter.py`, modify `pipeline.py`, `cli.py`
**Effort**: 1 day

---

## C. CLI Subcommand Help

**Current**: Custom help system, hard to discover
**Better**: Proper argparse subparsers

### Implementation
```python
# In multi_agent/cli.py - complete rewrite of argument parsing

def create_parser() -> argparse.ArgumentParser:
    """Create CLI parser with subcommands."""

    parser = argparse.ArgumentParser(
        prog='multi_agent_codex',
        description='Multi-Agent Codex CLI Orchestrator'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Task subcommand (default behavior)
    task_parser = subparsers.add_parser(
        'task',
        help='Run multi-agent task',
        description='Execute a task using configured agent family'
    )
    task_parser.add_argument('--config', default='config/developer_main.json')
    task_parser.add_argument('--task', required=True)
    # ... all existing task arguments

    # Create-family subcommand
    family_parser = subparsers.add_parser(
        'create-family',
        help='Create new agent family',
        description='Generate complete family from natural language description'
    )
    family_parser.add_argument('--description', required=True)
    # ... family creator arguments

    # Create-role subcommand
    role_parser = subparsers.add_parser(
        'create-role',
        help='Create new agent role',
        description='Generate role from natural language or manual spec'
    )
    role_parser.add_argument('--nl-description')
    # ... role creator arguments

    return parser

# Usage:
# python multi_agent_codex.py task --task "..." --config ...
# python multi_agent_codex.py create-family --description "..."
# python multi_agent_codex.py --help  (shows all subcommands)
# python multi_agent_codex.py task --help  (shows task-specific help)
```

**Files**: `multi_agent/cli.py` (refactor argument parsing section)
**Effort**: < 1 day

---

## D. Snapshot Auto-Optimization

**Current**: Manual `skip_dirs`, `skip_exts` configuration
**Better**: Auto-detect from `.gitignore` and project type

### Implementation
```python
# In multi_agent/snapshot.py

class SnapshotOptimizer:
    """Auto-optimize snapshot configuration."""

    @staticmethod
    def optimize_from_workspace(workspace: Path, base_config: Dict) -> Dict:
        """Enhance config with workspace-specific optimizations."""

        optimized = base_config.copy()

        # 1. Parse .gitignore
        gitignore_patterns = SnapshotOptimizer._parse_gitignore(workspace)
        if gitignore_patterns:
            # Add to skip_dirs
            optimized['skip_dirs'] = list(set(
                optimized.get('skip_dirs', []) + gitignore_patterns['dirs']
            ))
            # Add to skip patterns (for files)
            optimized.setdefault('skip_patterns', []).extend(gitignore_patterns['files'])

        # 2. Detect project type
        project_type = SnapshotOptimizer._detect_project_type(workspace)

        if project_type == 'python':
            optimized['skip_dirs'].extend(['__pycache__', '.pytest_cache', '.mypy_cache'])
            optimized['skip_exts'].extend(['.pyc', '.pyo'])
        elif project_type == 'javascript':
            optimized['skip_dirs'].extend(['node_modules', '.next', 'dist'])
        elif project_type == 'rust':
            optimized['skip_dirs'].extend(['target', 'Cargo.lock'])

        # 3. Detect large binary directories
        large_dirs = SnapshotOptimizer._find_large_directories(workspace)
        for dir_path in large_dirs:
            rel_path = dir_path.relative_to(workspace)
            optimized['skip_dirs'].append(str(rel_path))

        return optimized

    @staticmethod
    def _parse_gitignore(workspace: Path) -> Dict[str, List[str]]:
        """Extract skip patterns from .gitignore."""
        gitignore = workspace / ".gitignore"
        if not gitignore.exists():
            return {'dirs': [], 'files': []}

        dirs = []
        files = []

        for line in gitignore.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.endswith('/'):
                dirs.append(line.rstrip('/'))
            elif '*' in line:
                files.append(line)
            else:
                # Could be file or dir
                potential_path = workspace / line
                if potential_path.is_dir():
                    dirs.append(line)

        return {'dirs': dirs, 'files': files}

    @staticmethod
    def _detect_project_type(workspace: Path) -> str:
        """Detect project type from marker files."""
        markers = {
            'python': ['setup.py', 'pyproject.toml', 'requirements.txt'],
            'javascript': ['package.json', 'yarn.lock'],
            'rust': ['Cargo.toml'],
            'go': ['go.mod'],
            'java': ['pom.xml', 'build.gradle']
        }

        for project_type, marker_files in markers.items():
            if any((workspace / marker).exists() for marker in marker_files):
                return project_type

        return 'unknown'

    @staticmethod
    def _find_large_directories(workspace: Path, threshold_mb: int = 100) -> List[Path]:
        """Find directories larger than threshold."""
        large_dirs = []

        for item in workspace.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                try:
                    size_mb = sum(f.stat().st_size for f in item.rglob('*') if f.is_file()) / (1024 * 1024)
                    if size_mb > threshold_mb:
                        large_dirs.append(item)
                except (PermissionError, OSError):
                    pass

        return large_dirs

# Usage in snapshot generation:
optimized_config = SnapshotOptimizer.optimize_from_workspace(
    workspace, cfg.snapshot
)
snapshot = build_snapshot(workspace, optimized_config)
```

**Files**: `multi_agent/snapshot.py` (add SnapshotOptimizer class)
**Effort**: 1.5 days

---

## E. TUI for Output Navigation

**Current**: Manual file navigation
**Better**: Interactive terminal UI with navigation

### Implementation (using `rich`)
```python
# In multi_agent/output_browser.py (new file)

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt
from pathlib import Path

class OutputBrowser:
    """Interactive browser for agent outputs."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.console = Console()
        self.outputs = self._load_outputs()

    def _load_outputs(self) -> List[Tuple[str, Path]]:
        """Load all output files."""
        outputs = []
        for md_file in sorted(self.run_dir.glob("*.md")):
            agent_name = md_file.stem
            outputs.append((agent_name, md_file))
        return outputs

    def browse(self):
        """Start interactive browsing session."""
        current_idx = 0

        while True:
            self.console.clear()

            # Show file list
            self._show_file_list(current_idx)

            # Show current file content
            if self.outputs:
                self._show_file_content(self.outputs[current_idx][1])

            # Get user action
            action = Prompt.ask(
                "\\n[cyan]Action[/cyan]",
                choices=["n", "p", "q", "1-9"],
                default="n"
            )

            if action == "q":
                break
            elif action == "n" and current_idx < len(self.outputs) - 1:
                current_idx += 1
            elif action == "p" and current_idx > 0:
                current_idx -= 1
            elif action.isdigit() and 1 <= int(action) <= len(self.outputs):
                current_idx = int(action) - 1

    def _show_file_list(self, current_idx: int):
        """Display file list with highlighting."""
        table = Table(title=f"Run: {self.run_dir.name}")
        table.add_column("#", style="cyan")
        table.add_column("Agent", style="green")
        table.add_column("File", style="white")

        for idx, (agent_name, path) in enumerate(self.outputs):
            style = "bold yellow" if idx == current_idx else ""
            table.add_row(
                str(idx + 1),
                agent_name,
                path.name,
                style=style
            )

        self.console.print(table)

    def _show_file_content(self, path: Path):
        """Display file content with syntax highlighting."""
        content = path.read_text(encoding='utf-8')

        # Syntax highlighting
        syntax = Syntax(content, "markdown", theme="monokai", line_numbers=True)

        self.console.print(Panel(
            syntax,
            title=f"[cyan]{path.name}[/cyan]",
            subtitle="[n]ext [p]rev [1-9]jump [q]uit"
        ))

# Usage at end of pipeline:
if not args.no_browse:
    browser = OutputBrowser(run_dir)
    browser.browse()
```

**CLI Integration**:
```python
parser.add_argument('--no-browse', action='store_true', help='Skip output browser after completion')
```

**Files**: New `multi_agent/output_browser.py`, modify `cli.py`
**Dependencies**: `rich>=13.0.0` (already used)
**Effort**: 1 day

---

## Summary

| Quick Win | Effort | Impact | Dependencies |
|-----------|--------|--------|--------------|
| **A. Config Auto-Migration** | < 1 day | Medium | None |
| **B. Better Error Messages** | 1 day | High | None |
| **C. CLI Subcommand Help** | < 1 day | Medium | None |
| **D. Snapshot Auto-Optimization** | 1.5 days | High | None |
| **E. TUI Output Browser** | 1 day | Medium | rich (existing) |

**Total Effort**: ~5 days for all 5 quick wins
**Total Impact**: Significantly improved UX with minimal effort
