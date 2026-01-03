# Implementation Plan: Smart Error Recovery

## Architecture

### Core Components

#### 1. Error Classifier (`multi_agent/error_classifier.py`)
```python
from enum import Enum
from typing import Optional, Dict

class ErrorType(Enum):
    TIMEOUT = "timeout"
    EMPTY_OUTPUT = "empty_output"
    FORMAT_VALIDATION = "format_validation"
    MISSING_SECTIONS = "missing_sections"
    DIFF_PARSE_ERROR = "diff_parse_error"
    CONTEXT_ERROR = "context_error"
    UNKNOWN = "unknown"

class ErrorClassifier:
    """Classify agent failures into actionable error types."""

    @staticmethod
    def classify(
        returncode: int,
        stdout: str,
        stderr: str,
        validation_errors: List[str]
    ) -> ErrorType:
        """Determine error type from execution result."""

        if returncode == 124:
            return ErrorType.TIMEOUT

        if not stdout.strip():
            return ErrorType.EMPTY_OUTPUT

        if validation_errors:
            if any("missing section" in e.lower() for e in validation_errors):
                return ErrorType.MISSING_SECTIONS
            return ErrorType.FORMAT_VALIDATION

        if "diff --git" not in stdout and "apply_diff" in context:
            return ErrorType.DIFF_PARSE_ERROR

        if "KeyError" in stderr or "missing placeholder" in stderr.lower():
            return ErrorType.CONTEXT_ERROR

        return ErrorType.UNKNOWN

    @staticmethod
    def get_error_context(error_type: ErrorType, details: Dict) -> Dict:
        """Extract relevant context for error recovery."""
        # Returns: suggested fixes, retry strategy, user message
        pass
```

#### 2. Recovery Strategy Manager (`multi_agent/recovery_strategies.py`)
```python
from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class RecoveryStrategy:
    """Defines how to recover from a specific error type."""

    error_type: ErrorType
    max_retries: int
    backoff_multiplier: float
    prompt_modifier: Callable[[str, Dict], str]
    config_adjuster: Callable[[RoleConfig, Dict], RoleConfig]
    should_resume: bool  # Resume from this point vs. restart

class RecoveryStrategyManager:
    """Manages recovery strategies for different error types."""

    def __init__(self):
        self.strategies = self._init_strategies()

    def _init_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        return {
            ErrorType.TIMEOUT: RecoveryStrategy(
                error_type=ErrorType.TIMEOUT,
                max_retries=2,
                backoff_multiplier=1.5,
                prompt_modifier=self._simplify_task_prompt,
                config_adjuster=self._increase_timeout,
                should_resume=True
            ),
            ErrorType.MISSING_SECTIONS: RecoveryStrategy(
                error_type=ErrorType.MISSING_SECTIONS,
                max_retries=3,
                backoff_multiplier=1.0,
                prompt_modifier=self._emphasize_format_prompt,
                config_adjuster=lambda cfg, ctx: cfg,  # No config change
                should_resume=True
            ),
            ErrorType.EMPTY_OUTPUT: RecoveryStrategy(
                error_type=ErrorType.EMPTY_OUTPUT,
                max_retries=2,
                backoff_multiplier=1.2,
                prompt_modifier=self._add_explicit_output_request,
                config_adjuster=self._reduce_max_chars,
                should_resume=True
            ),
            # ... more strategies
        }

    def _simplify_task_prompt(self, prompt: str, context: Dict) -> str:
        """Simplify task for timeout recovery."""
        prefix = """
IMPORTANT: Previous attempt timed out. Focus on core requirements only.
Break down into smaller steps if needed.

"""
        return prefix + prompt

    def _emphasize_format_prompt(self, prompt: str, context: Dict) -> str:
        """Add format emphasis for section validation errors."""
        missing_sections = context.get('missing_sections', [])
        emphasis = f"""
CRITICAL: Your output MUST include these exact sections:
{chr(10).join(f"  {s}" for s in missing_sections)}

Double-check your output contains all required section headers.

"""
        # Insert after task description, before context
        parts = prompt.split("KONTEXT:")
        if len(parts) == 2:
            return parts[0] + emphasis + "KONTEXT:" + parts[1]
        return emphasis + prompt

    def _increase_timeout(self, cfg: RoleConfig, context: Dict) -> RoleConfig:
        """Increase timeout for retry."""
        new_timeout = int(cfg.timeout_sec * 1.5) if cfg.timeout_sec else 1800
        return dataclasses.replace(cfg, timeout_sec=new_timeout)

    def get_strategy(self, error_type: ErrorType) -> RecoveryStrategy:
        return self.strategies.get(error_type, self._default_strategy())

    def _default_strategy(self) -> RecoveryStrategy:
        """Fallback strategy for unknown errors."""
        return RecoveryStrategy(
            error_type=ErrorType.UNKNOWN,
            max_retries=1,
            backoff_multiplier=1.0,
            prompt_modifier=lambda p, c: p,
            config_adjuster=lambda cfg, c: cfg,
            should_resume=False
        )
```

#### 3. Resume Manager (`multi_agent/resume_manager.py`)
```python
class ResumeManager:
    """Manages partial pipeline resume from failure points."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.checkpoint_file = run_dir / "checkpoint.json"

    def save_checkpoint(
        self,
        completed_agents: List[str],
        failed_agent: str,
        outputs: Dict[str, str],
        config: AppConfig
    ):
        """Save checkpoint for resume."""
        checkpoint = {
            "timestamp": time.time(),
            "completed_agents": completed_agents,
            "failed_agent": failed_agent,
            "outputs": outputs,
            "config_path": str(config.path),
            "workspace": str(config.workspace)
        }
        self.checkpoint_file.write_text(json.dumps(checkpoint, indent=2))

    def can_resume(self, current_config: AppConfig) -> bool:
        """Check if resume is possible."""
        if not self.checkpoint_file.exists():
            return False

        checkpoint = json.loads(self.checkpoint_file.read_text())

        # Validate config hasn't changed significantly
        if checkpoint["config_path"] != str(current_config.path):
            return False

        return True

    def get_resume_point(self) -> Tuple[List[str], str, Dict[str, str]]:
        """Get state for resume."""
        checkpoint = json.loads(self.checkpoint_file.read_text())
        return (
            checkpoint["completed_agents"],
            checkpoint["failed_agent"],
            checkpoint["outputs"]
        )
```

### Integration Points

#### 1. Pipeline Error Handling (`multi_agent/pipeline.py`)
```python
# Modify _run_role_instance around line 300-400

async def _run_role_instance_with_recovery(self, ...):
    classifier = ErrorClassifier()
    strategy_manager = RecoveryStrategyManager()
    resume_manager = ResumeManager(self.run_dir)

    retry_count = 0
    current_prompt = original_prompt
    current_config = role_cfg

    while True:
        try:
            # Execute agent
            result = await self._exec_agent(
                current_config, current_prompt, ...
            )

            # Validate output
            validation_errors = self._validate_output(result, current_config)

            if result.ok and not validation_errors:
                # Success!
                return result

            # Classify error
            error_type = classifier.classify(
                result.returncode,
                result.stdout,
                result.stderr,
                validation_errors
            )

            # Get recovery strategy
            strategy = strategy_manager.get_strategy(error_type)

            if retry_count >= strategy.max_retries:
                # Max retries exceeded
                if strategy.should_resume:
                    # Save checkpoint for manual recovery
                    resume_manager.save_checkpoint(
                        self.completed_agents,
                        agent_name,
                        self.agent_outputs,
                        self.config
                    )
                raise RetryExhaustedError(error_type, retry_count)

            # Apply recovery strategy
            retry_count += 1

            print(f"\\n⚠️  {agent_name} failed ({error_type.value}). "
                  f"Retrying ({retry_count}/{strategy.max_retries})...\\n")

            # Modify prompt
            error_context = classifier.get_error_context(error_type, {
                'validation_errors': validation_errors,
                'missing_sections': self._extract_missing_sections(validation_errors)
            })
            current_prompt = strategy.prompt_modifier(current_prompt, error_context)

            # Adjust config
            current_config = strategy.config_adjuster(current_config, error_context)

            # Backoff delay
            await asyncio.sleep(strategy.backoff_multiplier * retry_count)

        except KeyboardInterrupt:
            # User cancelled - save checkpoint
            resume_manager.save_checkpoint(...)
            raise
```

#### 2. CLI Resume Support (`multi_agent/cli.py`)
```python
parser.add_argument(
    '--resume-from-failure',
    action='store_true',
    help='Resume pipeline from last failure point (reuses successful agents)'
)

# In main()
if args.resume_from_failure:
    resume_manager = ResumeManager(latest_run_dir)
    if resume_manager.can_resume(cfg):
        completed, failed, outputs = resume_manager.get_resume_point()
        print(f"Resuming from failure: {failed}")
        pipeline.restore_state(completed, outputs)
    else:
        print("Cannot resume: no checkpoint or config changed")
        sys.exit(1)
```

## Implementation Steps

### Phase 1: Error Classification (Day 1-2)
1. ✅ Implement ErrorClassifier
2. ✅ Add error pattern matching
3. ✅ Unit tests for all error types
4. ✅ Integrate into pipeline validation

### Phase 2: Recovery Strategies (Day 2-4)
1. ✅ Implement RecoveryStrategy dataclass
2. ✅ Create strategy for each error type
3. ✅ Implement prompt modifiers
4. ✅ Implement config adjusters
5. ✅ Test strategies with mock failures

### Phase 3: Resume Capability (Day 4-5)
1. ✅ Implement ResumeManager
2. ✅ Add checkpoint save/load
3. ✅ Validate config compatibility on resume
4. ✅ Test resume with various failure points

### Phase 4: Pipeline Integration (Day 6-7)
1. ✅ Modify pipeline retry logic
2. ✅ Add retry logging and user feedback
3. ✅ Integrate checkpoint saving
4. ✅ End-to-end testing with real failures

## Configuration

### defaults.json Addition
```json
{
  "error_recovery": {
    "enabled": true,
    "max_auto_retries": 3,
    "save_checkpoint_on_failure": true,
    "strategies": {
      "timeout": {
        "max_retries": 2,
        "timeout_multiplier": 1.5,
        "simplify_prompt": true
      },
      "missing_sections": {
        "max_retries": 3,
        "emphasize_format": true
      },
      "empty_output": {
        "max_retries": 2,
        "reduce_max_chars": true
      }
    }
  }
}
```

### Per-Role Override
```json
{
  "roles": [
    {
      "id": "implementer",
      "error_recovery": {
        "timeout": {
          "max_retries": 5,
          "custom_prompt_modifier": "implementer_timeout_prompt"
        }
      }
    }
  ]
}
```

## Error Recovery Examples

### Example 1: Timeout Recovery
```
[Attempt 1] implementer_1 (timeout=1200s) → TIMEOUT
[Auto-Retry 1/2] Increasing timeout to 1800s, simplifying prompt...
[Attempt 2] implementer_1 (timeout=1800s) → SUCCESS
```

### Example 2: Format Error Recovery
```
[Attempt 1] reviewer_1 → MISSING_SECTIONS: ["# Review", "- Findings:"]
[Auto-Retry 1/3] Emphasizing required sections in prompt...
[Attempt 2] reviewer_1 → SUCCESS
```

### Example 3: Resume from Checkpoint
```
$ python -m multi_agent.cli --task "..." --config developer_main.json

architect_1 → SUCCESS
implementer_1 → SUCCESS
tester_1 → FAILED (max retries exceeded)

Checkpoint saved: .multi_agent_runs/2025-12-31_16-00-00/checkpoint.json

# User fixes tester config, then:
$ python -m multi_agent.cli --resume-from-failure

Resuming from checkpoint...
Reusing: architect_1, implementer_1
Starting: tester_1 → SUCCESS
reviewer_1 → SUCCESS
```

## Testing Strategy

### Unit Tests
```python
def test_error_classification():
    # Timeout
    assert ErrorClassifier.classify(124, "", "", []) == ErrorType.TIMEOUT

    # Missing sections
    validation_errors = ["Missing section: # Tests"]
    assert ErrorClassifier.classify(0, "output", "", validation_errors) == ErrorType.MISSING_SECTIONS

def test_timeout_recovery_strategy():
    strategy = RecoveryStrategyManager().get_strategy(ErrorType.TIMEOUT)
    assert strategy.max_retries == 2

    # Test prompt modification
    modified = strategy.prompt_modifier("Task: X\\n\\nContext: Y", {})
    assert "timed out" in modified.lower()
```

### Integration Tests
```python
async def test_auto_recovery():
    # Mock agent that fails first time, succeeds second
    # Verify auto-retry with modified prompt
    # Verify success on retry
```

## Dependencies
- No new dependencies (uses stdlib)

## Documentation
- [ ] ERROR_RECOVERY.md guide
- [ ] Update README with --resume-from-failure
- [ ] Add troubleshooting section for recovery failures
