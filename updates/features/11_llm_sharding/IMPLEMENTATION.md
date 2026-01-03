# Implementation Summary: LLM-basiertes Task-Sharding

## Status: ✅ COMPLETE

## Architektur

### Uebersicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        create_shard_plan()                          │
├─────────────────────────────────────────────────────────────────────┤
│  shard_mode?                                                        │
│  ├─ "none"     → return None                                        │
│  ├─ "headings" → _plan_shards_by_headings()                         │
│  ├─ "files"    → _plan_shards_by_files()                            │
│  └─ "llm"      → _plan_shards_by_llm() ◄─── NEU IMPLEMENTIEREN      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    _plan_shards_by_llm()                            │
├─────────────────────────────────────────────────────────────────────┤
│  1. LLM-Client aus role_cfg.cli_provider erstellen                  │
│  2. Sharding-Prompt generieren                                      │
│  3. LLM aufrufen (kurzer, schneller Call)                           │
│  4. Response parsen (JSON/TOON)                                     │
│  5. Shard-Objekte erstellen                                         │
│  6. Bei Fehler: Fallback auf Single-Shard                           │
└─────────────────────────────────────────────────────────────────────┘
```

### LLM-Provider Fluss

```
┌─────────────────────────────────────────────────────────────────────┐
│  RoleConfig                                                         │
│  ├─ cli_provider: "claude"     ──┐                                  │
│  ├─ model: "opus"                │                                  │
│  └─ shard_llm: (optional)        │                                  │
│      ├─ provider: "claude"       │ Falls shard_llm definiert,       │
│      └─ model: "haiku"       ◄───┘ nutze dieses statt cli_provider  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  _get_shard_llm_client(role_cfg)                                    │
│  ├─ if role_cfg.shard_llm:                                          │
│  │      return build_cli_client(shard_llm.provider, shard_llm.model)│
│  └─ else:                                                           │
│         return build_cli_client(cli_provider, model)                │
└─────────────────────────────────────────────────────────────────────┘
```

## Implementierung

### 1. Models erweitern (`multi_agent/models.py`)

```python
# Neue Dataclass fuer Shard-LLM Konfiguration
@dataclass(frozen=True)
class ShardLLMConfig:
    """Configuration for the LLM used in shard planning."""
    provider: str = ""      # "codex", "claude", "gemini"
    model: str = ""         # "opus", "haiku", "gpt-4o", etc.


@dataclass(frozen=True)
class ShardLLMOptions:
    """Options for LLM-based sharding."""
    timeout_sec: int = 60
    max_retries: int = 2
    fallback_mode: str = "single"  # "single", "headings", "error"
    output_format: str = "json"    # "json" or "toon"


# RoleConfig erweitern (bestehende Felder plus):
@dataclass(frozen=True)
class RoleConfig:
    # ... existing fields ...
    shard_llm: ShardLLMConfig | None = None
    shard_llm_options: ShardLLMOptions = field(default_factory=ShardLLMOptions)
```

### 2. Sharding implementieren (`multi_agent/sharding.py`)

```python
"""Shard planning for parallel agent execution."""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any

from .models import RoleConfig, Shard, ShardPlan, ShardLLMOptions
from .cli_adapter import build_cli_client, CLIClient

logger = logging.getLogger(__name__)


def create_shard_plan(
    role_cfg: RoleConfig,
    task_text: str,
) -> ShardPlan | None:
    """Create a shard plan for a role based on its configuration."""
    if role_cfg.shard_mode == "none":
        return None

    if role_cfg.instances <= 1:
        return None

    shard_count = role_cfg.shard_count or role_cfg.instances

    if role_cfg.shard_mode == "headings":
        shards = _plan_shards_by_headings(task_text, shard_count, role_cfg)
    elif role_cfg.shard_mode == "files":
        shards = _plan_shards_by_files(task_text, shard_count, role_cfg)
    elif role_cfg.shard_mode == "llm":
        shards = _plan_shards_by_llm(task_text, shard_count, role_cfg)
    else:
        raise ValueError(f"Unknown shard_mode: {role_cfg.shard_mode}")

    if not shards:
        return None

    return ShardPlan(
        role_id=role_cfg.id,
        shard_mode=role_cfg.shard_mode,
        shard_count=len(shards),
        shards=shards,
        overlap_policy=role_cfg.overlap_policy,
        enforce_allowed_paths=role_cfg.enforce_allowed_paths,
    )


def _plan_shards_by_llm(
    task_text: str,
    shard_count: int,
    role_cfg: RoleConfig,
) -> List[Shard]:
    """
    Plan shards using an LLM to analyze and split the task.

    Strategy:
    1. Get LLM client from role config (or dedicated shard_llm config)
    2. Send task with sharding prompt
    3. Parse JSON response into Shard objects
    4. Fallback to single shard on any error

    Args:
        task_text: The task text to shard
        shard_count: Target number of shards
        role_cfg: Role configuration

    Returns:
        List of Shard objects
    """
    options = role_cfg.shard_llm_options or ShardLLMOptions()

    try:
        # Get appropriate LLM client
        cli_client = _get_shard_llm_client(role_cfg)

        # Build sharding prompt
        prompt = _build_shard_prompt(task_text, shard_count, options.output_format)

        # Execute LLM call with retries
        response = _execute_shard_llm_call(
            cli_client=cli_client,
            prompt=prompt,
            timeout_sec=options.timeout_sec,
            max_retries=options.max_retries,
        )

        if not response:
            logger.warning(f"LLM sharding returned empty response for {role_cfg.id}")
            return _handle_fallback(task_text, shard_count, role_cfg, options)

        # Parse response into shards
        shards = _parse_shard_response(response, shard_count, options.output_format)

        if not shards:
            logger.warning(f"Failed to parse LLM sharding response for {role_cfg.id}")
            return _handle_fallback(task_text, shard_count, role_cfg, options)

        logger.info(f"LLM sharding created {len(shards)} shards for {role_cfg.id}")
        return shards

    except Exception as e:
        logger.error(f"LLM sharding failed for {role_cfg.id}: {e}")
        return _handle_fallback(task_text, shard_count, role_cfg, options)


def _get_shard_llm_client(role_cfg: RoleConfig) -> CLIClient:
    """
    Get the CLI client for shard planning.

    Uses dedicated shard_llm config if provided, otherwise falls back
    to the role's cli_provider and model.

    Args:
        role_cfg: Role configuration

    Returns:
        CLIClient instance for sharding
    """
    if role_cfg.shard_llm and role_cfg.shard_llm.provider:
        # Use dedicated sharding LLM
        return build_cli_client(
            provider=role_cfg.shard_llm.provider,
            model=role_cfg.shard_llm.model,
        )
    else:
        # Use role's configured LLM
        return build_cli_client(
            provider=role_cfg.cli_provider,
            model=role_cfg.model,
        )


def _build_shard_prompt(
    task_text: str,
    shard_count: int,
    output_format: str = "json",
) -> str:
    """
    Build the prompt for LLM-based shard planning.

    Args:
        task_text: The task to split
        shard_count: Number of shards to create
        output_format: "json" or "toon"

    Returns:
        Formatted prompt string
    """
    if output_format == "toon":
        return _build_shard_prompt_toon(task_text, shard_count)

    return f"""Du bist ein Task-Planner. Analysiere die folgende Aufgabe und teile sie in genau {shard_count} unabhaengige Teilaufgaben auf.

REGELN:
1. Jede Teilaufgabe muss eigenstaendig bearbeitbar sein
2. Die Teilaufgaben sollen sich nicht ueberschneiden
3. Zusammen muessen alle Teilaufgaben die gesamte Aufgabe abdecken
4. Gib fuer jede Teilaufgabe einen klaren Titel, ein Ziel und den Aufgabentext an
5. Falls Dateipfade erkennbar sind, ordne sie den passenden Teilaufgaben zu

AUSGABEFORMAT (nur JSON, keine Erklaerungen):
{{
  "shards": [
    {{
      "title": "Kurzer Titel der Teilaufgabe",
      "goal": "Was soll erreicht werden",
      "content": "Detaillierter Aufgabentext fuer diese Teilaufgabe",
      "allowed_paths": ["pfad/zu/dateien/**"]
    }}
  ]
}}

AUFGABE:
{task_text}

Antworte NUR mit dem JSON-Objekt:"""


def _build_shard_prompt_toon(task_text: str, shard_count: int) -> str:
    """Build TOON-format prompt for sharding."""
    return f"""Du bist ein Task-Planner. Teile die Aufgabe in {shard_count} Teilaufgaben.

AUSGABEFORMAT (nur TOON):
shards[{shard_count}]{{title,goal,content,allowed_paths}}:
  Titel1|Ziel1|Aufgabentext1|pfad1/**,pfad2/**
  Titel2|Ziel2|Aufgabentext2|pfad3/**

AUFGABE:
{task_text}

Antworte NUR im TOON-Format:"""


def _execute_shard_llm_call(
    cli_client: CLIClient,
    prompt: str,
    timeout_sec: int,
    max_retries: int,
) -> str | None:
    """
    Execute the LLM call for shard planning with retry logic.

    Args:
        cli_client: The CLI client to use
        prompt: The sharding prompt
        timeout_sec: Timeout per attempt
        max_retries: Maximum retry attempts

    Returns:
        LLM response text or None on failure
    """
    for attempt in range(max_retries + 1):
        try:
            result = cli_client.run_simple(
                prompt=prompt,
                timeout_sec=timeout_sec,
                max_turns=1,
            )

            if result and result.strip():
                return result.strip()

            logger.warning(f"Shard LLM attempt {attempt + 1} returned empty")

        except TimeoutError:
            logger.warning(f"Shard LLM attempt {attempt + 1} timed out")
        except Exception as e:
            logger.warning(f"Shard LLM attempt {attempt + 1} failed: {e}")

    return None


def _parse_shard_response(
    response: str,
    expected_count: int,
    output_format: str = "json",
) -> List[Shard]:
    """
    Parse LLM response into Shard objects.

    Args:
        response: Raw LLM response
        expected_count: Expected number of shards
        output_format: "json" or "toon"

    Returns:
        List of Shard objects (may be empty on parse failure)
    """
    if output_format == "toon":
        return _parse_shard_response_toon(response, expected_count)

    return _parse_shard_response_json(response, expected_count)


def _parse_shard_response_json(response: str, expected_count: int) -> List[Shard]:
    """Parse JSON-formatted shard response."""
    # Extract JSON from response (may have markdown wrapper)
    json_start = response.find("{")
    json_end = response.rfind("}") + 1

    if json_start == -1 or json_end <= json_start:
        logger.warning("No JSON object found in shard response")
        return []

    json_str = response[json_start:json_end]

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse shard JSON: {e}")
        return []

    shards_data = data.get("shards", [])
    if not isinstance(shards_data, list):
        logger.warning("'shards' is not a list in response")
        return []

    shards: List[Shard] = []
    for i, shard_data in enumerate(shards_data, start=1):
        if not isinstance(shard_data, dict):
            continue

        title = str(shard_data.get("title", f"Shard {i}")).strip()
        goal = str(shard_data.get("goal", title)).strip()
        content = str(shard_data.get("content", "")).strip()

        # Parse allowed_paths
        paths_raw = shard_data.get("allowed_paths", [])
        if isinstance(paths_raw, str):
            paths = [p.strip() for p in paths_raw.split(",") if p.strip()]
        elif isinstance(paths_raw, list):
            paths = [str(p).strip() for p in paths_raw if p]
        else:
            paths = ["**"]

        if not content:
            logger.warning(f"Shard {i} has no content, skipping")
            continue

        shards.append(Shard(
            id=f"shard-{i}",
            title=title,
            goal=goal,
            content=content,
            allowed_paths=paths if paths else ["**"],
        ))

    return shards


def _parse_shard_response_toon(response: str, expected_count: int) -> List[Shard]:
    """Parse TOON-formatted shard response."""
    # TOON parsing implementation
    # Format: title|goal|content|paths
    lines = response.strip().splitlines()
    shards: List[Shard] = []

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("shards["):
            continue

        parts = line.split("|")
        if len(parts) < 3:
            continue

        title = parts[0].strip()
        goal = parts[1].strip() if len(parts) > 1 else title
        content = parts[2].strip() if len(parts) > 2 else ""
        paths_str = parts[3].strip() if len(parts) > 3 else "**"
        paths = [p.strip() for p in paths_str.split(",") if p.strip()]

        if not content:
            continue

        shards.append(Shard(
            id=f"shard-{len(shards) + 1}",
            title=title,
            goal=goal,
            content=content,
            allowed_paths=paths if paths else ["**"],
        ))

    return shards


def _handle_fallback(
    task_text: str,
    shard_count: int,
    role_cfg: RoleConfig,
    options: ShardLLMOptions,
) -> List[Shard]:
    """
    Handle fallback when LLM sharding fails.

    Args:
        task_text: Original task text
        shard_count: Requested shard count
        role_cfg: Role configuration
        options: Sharding options

    Returns:
        Fallback shards (single shard or heading-based)
    """
    fallback_mode = options.fallback_mode

    if fallback_mode == "headings":
        logger.info(f"Falling back to headings-based sharding for {role_cfg.id}")
        return _plan_shards_by_headings(task_text, shard_count, role_cfg)

    elif fallback_mode == "error":
        raise RuntimeError(f"LLM sharding failed for {role_cfg.id} and fallback is 'error'")

    else:  # "single" (default)
        logger.info(f"Falling back to single shard for {role_cfg.id}")
        return [
            Shard(
                id="shard-1",
                title="Full Task",
                goal="Complete the task as described",
                content=task_text.strip(),
                allowed_paths=["**"],
            )
        ]
```

### 3. CLI-Adapter erweitern (`multi_agent/cli_adapter.py`)

```python
# Neue Methode fuer einfache, kurze LLM-Calls hinzufuegen

class CLIClient:
    """Base class for CLI clients."""

    def run_simple(
        self,
        prompt: str,
        timeout_sec: int = 60,
        max_turns: int = 1,
    ) -> str | None:
        """
        Execute a simple, single-turn LLM call.

        This is optimized for quick tasks like sharding prompts,
        not full agent execution.

        Args:
            prompt: The prompt to send
            timeout_sec: Maximum execution time
            max_turns: Number of turns (usually 1)

        Returns:
            Response text or None on failure
        """
        raise NotImplementedError("Subclasses must implement run_simple")


class CodexCLIClient(CLIClient):
    """Codex CLI client implementation."""

    def run_simple(
        self,
        prompt: str,
        timeout_sec: int = 60,
        max_turns: int = 1,
    ) -> str | None:
        """Execute simple Codex CLI call."""
        import subprocess

        cmd = [
            "codex",
            "--quiet",
            "--approval-mode", "full-auto",
            "--max-turns", str(max_turns),
        ]

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None


class ClaudeCLIClient(CLIClient):
    """Claude CLI client implementation."""

    def run_simple(
        self,
        prompt: str,
        timeout_sec: int = 60,
        max_turns: int = 1,
    ) -> str | None:
        """Execute simple Claude CLI call."""
        import subprocess

        cmd = [
            "claude",
            "--print",
            "--max-turns", str(max_turns),
        ]

        if self.model:
            cmd.extend(["--model", self.model])

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
```

### 4. Config-Loader erweitern (`multi_agent/config_loader.py`)

```python
# In der Funktion die RoleConfig erstellt:

def _parse_shard_llm(role_data: Dict) -> ShardLLMConfig | None:
    """Parse shard_llm configuration from role data."""
    shard_llm_data = role_data.get("shard_llm")
    if not shard_llm_data:
        return None

    return ShardLLMConfig(
        provider=shard_llm_data.get("provider", ""),
        model=shard_llm_data.get("model", ""),
    )


def _parse_shard_llm_options(role_data: Dict) -> ShardLLMOptions:
    """Parse shard_llm_options from role data."""
    options_data = role_data.get("shard_llm_options", {})

    return ShardLLMOptions(
        timeout_sec=int(options_data.get("timeout_sec", 60)),
        max_retries=int(options_data.get("max_retries", 2)),
        fallback_mode=str(options_data.get("fallback_mode", "single")),
        output_format=str(options_data.get("output_format", "json")),
    )


# In build_role_config():
def build_role_config(role_data: Dict, ...) -> RoleConfig:
    # ... existing code ...

    return RoleConfig(
        # ... existing fields ...
        shard_llm=_parse_shard_llm(role_data),
        shard_llm_options=_parse_shard_llm_options(role_data),
    )
```

## ACTUAL IMPLEMENTATION

### Simplified Approach
The actual implementation uses a simpler approach than the original plan:
- Uses `Dict[str, str]` for `shard_llm` instead of separate dataclass
- Uses `Dict[str, object]` for `shard_llm_options` instead of separate dataclass
- Uses subprocess directly instead of creating new CLI client methods
- Follows the same pattern as existing task_split.py implementation

### Implementation Completed:

#### Phase 1: Models ✅
- [x] Added `shard_llm: Dict[str, str] | None` to RoleConfig
- [x] Added `shard_llm_options: Dict[str, object] | None` to RoleConfig
- [x] Updated config_loader.py to parse these fields

#### Phase 2: LLM-Sharding Implementation ✅
- [x] `_build_llm_sharding_prompt()` - Creates structured prompt for LLM
- [x] `_parse_llm_sharding_response()` - Parses JSON response with error handling
- [x] `_plan_shards_by_llm()` - Main function with retry logic and fallback
- [x] `_create_single_shard()` - Fallback helper function
- [x] Updated `create_shard_plan()` to call LLM sharding mode

#### Phase 3: Configuration ✅
- [x] Created example_llm_sharding_basic.json
- [x] Created example_llm_sharding_advanced.json

### Files Modified:
1. `multi_agent/models.py` - Added shard_llm fields to RoleConfig
2. `multi_agent/sharding.py` - Implemented LLM sharding functions
3. `multi_agent/config_loader.py` - Added parsing for new fields
4. `updates/features/11_llm_sharding/example_llm_sharding_basic.json` - Basic example
5. `updates/features/11_llm_sharding/example_llm_sharding_advanced.json` - Advanced example

## Testplan

### Unit Tests

```python
# tests/test_llm_sharding.py

import pytest
from unittest.mock import Mock, patch
from multi_agent.sharding import (
    _plan_shards_by_llm,
    _parse_shard_response_json,
    _get_shard_llm_client,
    _build_shard_prompt,
)
from multi_agent.models import RoleConfig, Shard, ShardLLMConfig, ShardLLMOptions


class TestShardPromptBuilding:
    """Tests for shard prompt generation."""

    def test_build_shard_prompt_json(self):
        prompt = _build_shard_prompt("Task XYZ", 3, "json")
        assert "3" in prompt
        assert "Task XYZ" in prompt
        assert "JSON" in prompt or "json" in prompt

    def test_build_shard_prompt_includes_rules(self):
        prompt = _build_shard_prompt("Task", 2, "json")
        assert "unabhaengig" in prompt.lower() or "independent" in prompt.lower()


class TestShardResponseParsing:
    """Tests for parsing LLM responses."""

    def test_parse_valid_json_response(self):
        response = '''
        {"shards": [
            {"title": "Part 1", "goal": "Do X", "content": "Task X content", "allowed_paths": ["src/**"]},
            {"title": "Part 2", "goal": "Do Y", "content": "Task Y content", "allowed_paths": ["tests/**"]}
        ]}
        '''
        shards = _parse_shard_response_json(response, 2)
        assert len(shards) == 2
        assert shards[0].title == "Part 1"
        assert shards[0].goal == "Do X"
        assert shards[0].content == "Task X content"
        assert shards[0].allowed_paths == ["src/**"]

    def test_parse_json_with_markdown_wrapper(self):
        response = '''
        Here is the sharding plan:
        ```json
        {"shards": [{"title": "A", "goal": "G", "content": "C", "allowed_paths": []}]}
        ```
        '''
        shards = _parse_shard_response_json(response, 1)
        assert len(shards) == 1
        assert shards[0].title == "A"

    def test_parse_invalid_json_returns_empty(self):
        shards = _parse_shard_response_json("not json", 2)
        assert shards == []

    def test_parse_empty_content_skipped(self):
        response = '{"shards": [{"title": "A", "goal": "G", "content": ""}]}'
        shards = _parse_shard_response_json(response, 1)
        assert shards == []


class TestShardLLMClientSelection:
    """Tests for LLM client selection."""

    def test_uses_role_provider_when_no_shard_llm(self):
        role_cfg = RoleConfig(
            id="test",
            name="test",
            cli_provider="codex",
            model="gpt-4o",
            shard_llm=None,
        )
        with patch('multi_agent.sharding.build_cli_client') as mock:
            _get_shard_llm_client(role_cfg)
            mock.assert_called_with(provider="codex", model="gpt-4o")

    def test_uses_shard_llm_when_configured(self):
        role_cfg = RoleConfig(
            id="test",
            name="test",
            cli_provider="claude",
            model="opus",
            shard_llm=ShardLLMConfig(provider="claude", model="haiku"),
        )
        with patch('multi_agent.sharding.build_cli_client') as mock:
            _get_shard_llm_client(role_cfg)
            mock.assert_called_with(provider="claude", model="haiku")


class TestShardingFallback:
    """Tests for fallback behavior."""

    def test_fallback_single_on_empty_response(self):
        role_cfg = RoleConfig(
            id="test",
            instances=3,
            shard_mode="llm",
            shard_llm_options=ShardLLMOptions(fallback_mode="single"),
        )
        with patch('multi_agent.sharding._execute_shard_llm_call', return_value=None):
            shards = _plan_shards_by_llm("Task", 3, role_cfg)
            assert len(shards) == 1
            assert shards[0].title == "Full Task"

    def test_fallback_headings_mode(self):
        role_cfg = RoleConfig(
            id="test",
            instances=2,
            shard_mode="llm",
            shard_llm_options=ShardLLMOptions(fallback_mode="headings"),
        )
        task = "# Part 1\nContent 1\n\n# Part 2\nContent 2"
        with patch('multi_agent.sharding._execute_shard_llm_call', return_value=None):
            shards = _plan_shards_by_llm(task, 2, role_cfg)
            assert len(shards) == 2

    def test_fallback_error_raises(self):
        role_cfg = RoleConfig(
            id="test",
            instances=2,
            shard_mode="llm",
            shard_llm_options=ShardLLMOptions(fallback_mode="error"),
        )
        with patch('multi_agent.sharding._execute_shard_llm_call', return_value=None):
            with pytest.raises(RuntimeError):
                _plan_shards_by_llm("Task", 2, role_cfg)
```

### Integration Tests

```python
# tests/test_llm_sharding_integration.py

import pytest
from multi_agent.sharding import create_shard_plan
from multi_agent.models import RoleConfig


@pytest.mark.integration
@pytest.mark.slow
class TestLLMShardingIntegration:
    """Integration tests with real LLM calls."""

    def test_sharding_simple_task_codex(self):
        """Test sharding a simple task with Codex."""
        role_cfg = RoleConfig(
            id="implementer",
            name="Implementer",
            instances=3,
            shard_mode="llm",
            cli_provider="codex",
        )
        task = "Implementiere eine REST API mit User-Authentifizierung, Datenbank-Anbindung und Tests."

        plan = create_shard_plan(role_cfg, task)

        assert plan is not None
        assert len(plan.shards) >= 1
        assert len(plan.shards) <= 3
        for shard in plan.shards:
            assert shard.title
            assert shard.content

    def test_sharding_with_haiku_for_cost(self):
        """Test using cheaper model for sharding."""
        role_cfg = RoleConfig(
            id="implementer",
            name="Implementer",
            instances=2,
            shard_mode="llm",
            cli_provider="claude",
            model="opus",
            shard_llm=ShardLLMConfig(provider="claude", model="haiku"),
        )
        task = "Erstelle Unit Tests und Integration Tests fuer das Auth-Modul."

        plan = create_shard_plan(role_cfg, task)

        assert plan is not None
        assert len(plan.shards) >= 1
```

## Konfigurationsbeispiele

### defaults.json Erweiterung

```json
{
  "role_defaults": {
    "shard_mode": "none",
    "shard_llm_options": {
      "timeout_sec": 60,
      "max_retries": 2,
      "fallback_mode": "single",
      "output_format": "json"
    }
  }
}
```

### Beispiel Family Config

```json
{
  "roles": [
    {
      "id": "implementer",
      "file": "agents/implementer.json",
      "instances": 3,
      "cli_provider": "codex",
      "shard_mode": "llm",
      "shard_llm_options": {
        "timeout_sec": 45,
        "fallback_mode": "headings"
      }
    },
    {
      "id": "reviewer",
      "file": "agents/reviewer.json",
      "instances": 2,
      "cli_provider": "claude",
      "model": "opus",
      "shard_mode": "llm",
      "shard_llm": {
        "provider": "claude",
        "model": "haiku"
      }
    }
  ]
}
```

## Abhaengigkeiten
- Keine neuen externen Abhaengigkeiten
- Nutzt bestehende CLI-Adapter Infrastruktur

## Dokumentation
- [ ] SHARDING.md Guide aktualisieren
- [ ] README.md mit `shard_mode: "llm"` Beispiel erweitern
- [ ] Inline-Dokumentation (Docstrings) vollstaendig
