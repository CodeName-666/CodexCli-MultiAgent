# Implementation: Creator Scripts CLI-Provider Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Creator CLI Layer                         │
│  (multi_family_creator.py, multi_role_agent_creator.py)    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──> --auto-providers
                     ├──> --interactive-providers
                     ├──> --provider-template <name>
                     ├──> --migrate-cli-providers
                     │
           ┌─────────▼──────────┐
           │ ProviderSelector   │
           │  (NEW MODULE)      │
           └─────────┬──────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌─────────┐  ┌──────────┐  ┌──────────┐
  │  Auto   │  │Interactive│  │ Template │
  │ Selector│  │ Selector  │  │ Selector │
  └─────────┘  └──────────┘  └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
           ┌─────────▼──────────┐
           │  ProviderConfig    │
           │   Generator        │
           └─────────┬──────────┘
                     │
                     ▼
            Generated role config
            with cli_provider fields
```

## Component Design

### 1. ProviderSelector (Core Logic)

**File**: `multi_agent/provider_selector.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class ProviderRecommendation:
    """Recommendation for a specific role."""
    provider_id: str  # "codex", "claude", "gemini"
    model: str  # "sonnet", "opus", "gemini-2.5-flash", etc.
    parameters: Dict[str, any]
    confidence: float  # 0.0-1.0
    reasoning: str  # Why this provider was chosen
    estimated_cost: float  # Cost per 1M tokens


@dataclass
class RoleProfile:
    """Profile of a role for provider selection."""
    role_id: str
    role_name: str
    role_description: str
    role_type: str  # "architect", "implementer", "tester", etc.
    complexity: str  # "low", "medium", "high"
    requires_code_gen: bool
    requires_analysis: bool
    requires_planning: bool
    expected_output_size: str  # "small", "medium", "large"


class ProviderSelector:
    """
    Intelligent CLI Provider selection for roles.

    Supports three modes:
    - Auto: Automatic selection based on role profile
    - Interactive: User selects with recommendations
    - Template: Use predefined template
    """

    def __init__(self, cli_config_path: Path):
        self.cli_config_path = cli_config_path
        self.templates = self._load_templates()
        self.cli_providers = self._load_cli_providers()

    def recommend_provider(
        self,
        role_profile: RoleProfile
    ) -> ProviderRecommendation:
        """
        Recommend optimal provider for a role.

        Decision Logic:
        1. High complexity + planning -> Claude Sonnet/Opus
        2. Code generation -> Codex
        3. Simple analysis/testing -> Gemini Flash
        4. Review/quality -> Claude Opus
        5. Summary/integration -> Claude Haiku
        """
        # Implementation in next section
        pass

    def interactive_select(
        self,
        role_profile: RoleProfile
    ) -> ProviderRecommendation:
        """Interactive CLI selection with recommendations."""
        pass

    def from_template(
        self,
        template_name: str,
        role_profile: RoleProfile
    ) -> ProviderRecommendation:
        """Select provider based on template."""
        pass
```

### 2. Role Profiler (Analyze Roles)

**File**: `multi_agent/role_profiler.py`

```python
class RoleProfiler:
    """
    Analyzes role descriptions to create RoleProfile.

    Uses heuristics and keyword matching to determine:
    - Role type (architect, implementer, etc.)
    - Complexity level
    - Required capabilities
    """

    # Keywords for role type detection
    ROLE_TYPE_KEYWORDS = {
        "architect": ["architektur", "design", "plan", "struktur"],
        "implementer": ["implementier", "code", "entwickl", "program"],
        "tester": ["test", "qa", "validier", "prüf"],
        "reviewer": ["review", "check", "analyse", "audit"],
        "integrator": ["integr", "zusammen", "merge", "final"]
    }

    # Complexity indicators
    COMPLEXITY_HIGH = ["komplex", "fortgeschritten", "advanced", "multi"]
    COMPLEXITY_LOW = ["einfach", "simple", "basic", "quick"]

    def profile_role(
        self,
        role_id: str,
        role_data: Dict,
        nl_description: Optional[str] = None
    ) -> RoleProfile:
        """
        Create profile from role data and optional NL description.

        Args:
            role_id: Role identifier
            role_data: Role config dict (from JSON)
            nl_description: Optional natural language description

        Returns:
            RoleProfile with analyzed characteristics
        """
        role_name = role_data.get("name", role_id)
        role_desc = role_data.get("role", "")
        prompt_template = role_data.get("prompt_template", "")

        # Combine all text for analysis
        combined_text = f"{role_desc} {prompt_template}"
        if nl_description:
            combined_text += f" {nl_description}"

        combined_lower = combined_text.lower()

        # Detect role type
        role_type = self._detect_role_type(combined_lower)

        # Detect complexity
        complexity = self._detect_complexity(combined_lower)

        # Detect capabilities needed
        requires_code = any(kw in combined_lower for kw in
                           ["code", "implement", "diff", "```"])
        requires_analysis = any(kw in combined_lower for kw in
                               ["analys", "review", "check", "validier"])
        requires_planning = any(kw in combined_lower for kw in
                               ["plan", "architektur", "design", "struktur"])

        # Estimate output size from expected_sections or prompt
        expected_sections = role_data.get("expected_sections", [])
        if len(expected_sections) > 8:
            output_size = "large"
        elif len(expected_sections) > 4:
            output_size = "medium"
        else:
            output_size = "small"

        return RoleProfile(
            role_id=role_id,
            role_name=role_name,
            role_description=role_desc,
            role_type=role_type,
            complexity=complexity,
            requires_code_gen=requires_code,
            requires_analysis=requires_analysis,
            requires_planning=requires_planning,
            expected_output_size=output_size
        )
```

### 3. Provider Recommendation Logic

**Selection Rules** (in ProviderSelector):

```python
def recommend_provider(
    self,
    role_profile: RoleProfile
) -> ProviderRecommendation:
    """
    Provider selection decision tree:

    1. ARCHITECT/PLANNING
       - High complexity -> Claude Opus (max quality)
       - Medium/Low -> Claude Sonnet (balanced)

    2. IMPLEMENTER/CODE
       - Always -> Codex (specialized for code)
       - Fallback -> Claude Sonnet

    3. TESTER
       - Simple tests -> Gemini Flash (fast, cheap)
       - Complex tests -> Claude Sonnet

    4. REVIEWER
       - Critical review -> Claude Opus (best quality)
       - Standard review -> Claude Sonnet

    5. INTEGRATOR/SUMMARY
       - Always -> Claude Haiku (fast, cheap, sufficient)
    """

    # Get base recommendation
    if role_profile.role_type == "architect":
        if role_profile.complexity == "high":
            return ProviderRecommendation(
                provider_id="claude",
                model="opus",
                parameters={
                    "max_turns": 5,
                    "allowed_tools": "Read,Glob,Grep",
                    "append_system_prompt": "Fokus auf skalierbare Architektur."
                },
                confidence=0.95,
                reasoning="Architektur mit hoher Komplexität benötigt maximale Denkleistung",
                estimated_cost=0.015  # per 1k tokens
            )
        else:
            return ProviderRecommendation(
                provider_id="claude",
                model="sonnet",
                parameters={
                    "max_turns": 3,
                    "allowed_tools": "Read,Glob,Grep"
                },
                confidence=0.90,
                reasoning="Architektur-Planung, balancierte Qualität",
                estimated_cost=0.003
            )

    elif role_profile.role_type == "implementer":
        return ProviderRecommendation(
            provider_id="codex",
            model=None,  # Uses codex default
            parameters={},
            confidence=0.85,
            reasoning="Code-Generierung ist Codex-Spezialität",
            estimated_cost=0.002
        )

    elif role_profile.role_type == "tester":
        if role_profile.complexity == "high":
            return ProviderRecommendation(
                provider_id="claude",
                model="sonnet",
                parameters={"max_turns": 2},
                confidence=0.80,
                reasoning="Komplexe Tests benötigen tiefes Verständnis",
                estimated_cost=0.003
            )
        else:
            return ProviderRecommendation(
                provider_id="gemini",
                model="gemini-2.5-flash",
                parameters={"temperature": 0.5},
                confidence=0.85,
                reasoning="Einfache Tests, Geschwindigkeit wichtiger als Perfektion",
                estimated_cost=0.0001
            )

    elif role_profile.role_type == "reviewer":
        return ProviderRecommendation(
            provider_id="claude",
            model="opus",
            parameters={
                "max_turns": 2,
                "append_system_prompt": "Fokus: Security, Performance, Maintainability"
            },
            confidence=0.95,
            reasoning="Review erfordert höchste Qualität für Fehler-Erkennung",
            estimated_cost=0.015
        )

    elif role_profile.role_type == "integrator":
        return ProviderRecommendation(
            provider_id="claude",
            model="haiku",
            parameters={"max_turns": 1},
            confidence=0.90,
            reasoning="Zusammenfassung ist einfache Task, Haiku reicht",
            estimated_cost=0.0008
        )

    # Default fallback
    return ProviderRecommendation(
        provider_id="codex",
        model=None,
        parameters={},
        confidence=0.50,
        reasoning="Fallback auf Standard-Provider",
        estimated_cost=0.002
    )
```

### 4. Template System

**File**: `~/.codex/templates/provider_templates.json`

```json
{
  "cost-optimized": {
    "name": "Kostenoptimiert",
    "description": "Minimale Kosten bei akzeptabler Qualität",
    "rules": {
      "architect": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {"max_turns": 2}
      },
      "implementer": {
        "provider": "codex",
        "model": null,
        "parameters": {}
      },
      "tester": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "parameters": {"temperature": 0.5}
      },
      "reviewer": {
        "provider": "claude",
        "model": "haiku",
        "parameters": {"max_turns": 1}
      },
      "integrator": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "parameters": {}
      },
      "default": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "parameters": {}
      }
    },
    "estimated_cost_per_run": 0.15
  },

  "quality-first": {
    "name": "Qualität zuerst",
    "description": "Beste Qualität, Kosten zweitrangig",
    "rules": {
      "architect": {
        "provider": "claude",
        "model": "opus",
        "parameters": {"max_turns": 5}
      },
      "implementer": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {"max_turns": 3}
      },
      "tester": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {"max_turns": 2}
      },
      "reviewer": {
        "provider": "claude",
        "model": "opus",
        "parameters": {"max_turns": 3}
      },
      "integrator": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {"max_turns": 1}
      },
      "default": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {}
      }
    },
    "estimated_cost_per_run": 1.80
  },

  "balanced": {
    "name": "Balanciert",
    "description": "Gute Balance zwischen Qualität und Kosten",
    "rules": {
      "architect": {
        "provider": "claude",
        "model": "sonnet",
        "parameters": {"max_turns": 3}
      },
      "implementer": {
        "provider": "codex",
        "model": null,
        "parameters": {}
      },
      "tester": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "parameters": {}
      },
      "reviewer": {
        "provider": "claude",
        "model": "opus",
        "parameters": {"max_turns": 2}
      },
      "integrator": {
        "provider": "claude",
        "model": "haiku",
        "parameters": {}
      },
      "default": {
        "provider": "codex",
        "model": null,
        "parameters": {}
      }
    },
    "estimated_cost_per_run": 0.45
  }
}
```

## Integration Points

### 1. Multi-Family Creator Integration

**File**: `creators/multi_family_creator.py`

```python
# Add new CLI arguments
parser.add_argument(
    "--auto-providers",
    action="store_true",
    help="Automatisch optimale CLI-Provider für Rollen wählen"
)
parser.add_argument(
    "--interactive-providers",
    action="store_true",
    help="Interaktive Provider-Auswahl für jede Rolle"
)
parser.add_argument(
    "--provider-template",
    type=str,
    choices=["cost-optimized", "quality-first", "balanced"],
    help="Vordefiniertes Provider-Template verwenden"
)
parser.add_argument(
    "--migrate-cli-providers",
    action="store_true",
    help="CLI-Provider zu existierender Config hinzufügen"
)

# In _build_main_config():
def _build_main_config(self, spec: Dict, role_entries: List[Dict]) -> Dict:
    # ... existing code ...

    # Add CLI provider configuration
    if self.args.auto_providers or self.args.interactive_providers or self.args.provider_template:
        role_entries = self._configure_role_providers(role_entries, spec)

    return main_config

def _configure_role_providers(self, role_entries: List[Dict], spec: Dict) -> List[Dict]:
    """Add CLI provider config to role entries."""
    from multi_agent.provider_selector import ProviderSelector, RoleProfiler

    selector = ProviderSelector(self.config_dir / "cli_config.json")
    profiler = RoleProfiler()

    for role_entry in role_entries:
        # Load role data for profiling
        role_path = self.config_dir / role_entry["file"]
        role_data = load_json(role_path)

        # Create profile
        profile = profiler.profile_role(
            role_id=role_entry["id"],
            role_data=role_data,
            nl_description=spec.get("roles", {}).get(role_entry["id"], {}).get("description")
        )

        # Get recommendation
        if self.args.provider_template:
            recommendation = selector.from_template(self.args.provider_template, profile)
        elif self.args.interactive_providers:
            recommendation = selector.interactive_select(profile)
        else:  # auto
            recommendation = selector.recommend_provider(profile)

        # Apply to role entry
        role_entry["cli_provider"] = recommendation.provider_id
        if recommendation.model:
            role_entry["model"] = recommendation.model
        if recommendation.parameters:
            role_entry["cli_parameters"] = recommendation.parameters

    return role_entries
```

### 2. Role Creator Integration

**File**: `creators/multi_role_agent_creator.py`

Similar integration but for single roles.

## Files to Create/Modify

### New Files
1. `multi_agent/provider_selector.py` (~400 lines)
2. `multi_agent/role_profiler.py` (~250 lines)
3. `multi_agent/provider_templates.py` (~150 lines)
4. `~/.codex/templates/provider_templates.json` (template file)

### Modified Files
1. `creators/multi_family_creator.py` (+150 lines)
2. `creators/multi_role_agent_creator.py` (+100 lines)
3. `creators/multi_role_agent_creator_legacy.py` (+50 lines)

## Testing Strategy

### Unit Tests
```python
# test_provider_selector.py
def test_architect_high_complexity_selects_opus():
    profile = RoleProfile(
        role_type="architect",
        complexity="high",
        # ...
    )
    selector = ProviderSelector(...)
    rec = selector.recommend_provider(profile)
    assert rec.provider_id == "claude"
    assert rec.model == "opus"

def test_tester_low_complexity_selects_gemini_flash():
    # ...
```

### Integration Tests
```bash
# Test auto-providers
python multi_agent_codex.py create-family \
  --description "Test team" \
  --auto-providers \
  --output-dir test_output

# Verify generated config has cli_provider fields
python -c "import json; config = json.load(open('test_output/test_main.json')); assert all('cli_provider' in r for r in config['roles'])"
```

## Migration Path

For existing configs:

```bash
# Migrate existing config
python multi_agent_codex.py create-family \
  --migrate-cli-providers \
  --config config/developer_main.json \
  --provider-template balanced

# Creates backup: config/developer_main.json.backup
# Updates: config/developer_main.json with cli_provider fields
```

## Performance Considerations

- **Profiling**: < 50ms per role
- **Interactive Mode**: User-driven, no performance concern
- **Template Loading**: Cache templates in memory

## Security Considerations

- **Template Injection**: Validate template JSON schema
- **Path Traversal**: Sanitize template file paths
- **Command Injection**: No exec/eval of user input

## Rollout Plan

### Phase 1: Core Implementation (Day 1-2)
- Implement ProviderSelector
- Implement RoleProfiler
- Add basic templates

### Phase 2: Creator Integration (Day 2-3)
- Integrate into Family Creator
- Integrate into Role Creator
- Add CLI flags

### Phase 3: Polish & Testing (Day 3)
- Interactive mode UI polish
- Comprehensive testing
- Documentation
- Migration script
