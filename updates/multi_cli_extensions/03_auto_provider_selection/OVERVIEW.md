# Feature 3: Automatische Provider-Auswahl basierend auf Task-Komplexität

## Quick Summary
Intelligentes System zur automatischen Auswahl des optimalen CLI-Providers basierend auf Task-Analyse, ohne manuelle Konfiguration.

## Priority: 🟢 HIGH
- **Impact**: ⭐⭐⭐⭐⭐ (30-50% Kostenersparnis automatisch)
- **Effort**: Medium (3-4 Tage)
- **ROI**: Massiv - "Fire and forget" Kostenoptimierung

## Key Features

### 1. Task Complexity Analyzer
Analysiert den User-Task und bestimmt Komplexitäts-Score:
- **Keyword Analysis**: "refactor", "implement", "quick fix"
- **Scope Detection**: Anzahl betroffener Dateien/Module
- **Historical Learning**: ML-Modell basierend auf vergangenen Runs

### 2. Dynamic Provider Selection
Wählt Provider pro Agent basierend auf:
- Task-Komplexität
- Agenten-Rolle (architect, implementer, etc.)
- Kosten-Budget (optional)
- Performance-Ziel (speed vs quality)

### 3. Adaptive Strategy
```python
# Example API
$ python multi_agent_codex.py --task "Quick bug fix" --auto-select-providers

[Auto Provider Selection]
Task Complexity: LOW (Score: 0.25)
Strategy: Cost-Optimized

Selected Providers:
  architect    -> claude (haiku)     [Simple bug analysis]
  implementer  -> codex              [Quick fix]
  tester       -> gemini (flash)     [Basic tests]

Estimated Cost: $0.08
Time: ~2 minutes
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                User Task Input                          │
└─────────────────┬───────────────────────────────────────┘
                  │
       ┌──────────▼────────────┐
       │  TaskAnalyzer         │
       │  - Keyword Extraction │
       │  - Scope Detection    │
       │  - Complexity Scoring │
       └──────────┬────────────┘
                  │
       ┌──────────▼─────────────┐
       │  StrategySelector      │
       │  - Cost-Optimized      │
       │  - Quality-First       │
       │  - Balanced            │
       │  - Custom (ML-based)   │
       └──────────┬─────────────┘
                  │
       ┌──────────▼─────────────┐
       │  ProviderMatcher       │
       │  Maps roles → providers│
       │  based on strategy     │
       └──────────┬─────────────┘
                  │
       ┌──────────▼─────────────┐
       │  Pipeline Execution    │
       │  with selected providers│
       └────────────────────────┘
```

## Task Complexity Scoring

### Factors
1. **Keyword-based** (40%):
   - "simple", "quick" → Low
   - "implement", "add feature" → Medium
   - "refactor", "redesign", "complex" → High

2. **Scope-based** (30%):
   - Files affected: 1-2 → Low, 3-10 → Medium, 10+ → High
   - Lines changed: < 50 → Low, 50-200 → Medium, 200+ → High

3. **Historical** (30%):
   - Similar tasks in the past
   - Success rate with different providers
   - Token usage patterns

### Score Calculation
```python
complexity_score = (
    keyword_score * 0.4 +
    scope_score * 0.3 +
    historical_score * 0.3
)

if complexity_score < 0.3:
    strategy = "cost-optimized"
elif complexity_score > 0.7:
    strategy = "quality-first"
else:
    strategy = "balanced"
```

## Selection Strategies

### 1. Cost-Optimized (Low Complexity)
```python
{
    "architect": ("gemini", "gemini-2.5-flash"),
    "implementer": ("codex", None),
    "tester": ("gemini", "gemini-2.5-flash"),
    "reviewer": ("claude", "haiku"),
    "integrator": ("gemini", "gemini-2.5-flash")
}
# Estimated cost: $0.10 - $0.20
```

### 2. Balanced (Medium Complexity)
```python
{
    "architect": ("claude", "sonnet"),
    "implementer": ("codex", None),
    "tester": ("gemini", "gemini-2.5-flash"),
    "reviewer": ("claude", "sonnet"),
    "integrator": ("claude", "haiku")
}
# Estimated cost: $0.40 - $0.60
```

### 3. Quality-First (High Complexity)
```python
{
    "architect": ("claude", "opus"),
    "implementer": ("claude", "sonnet"),
    "tester": ("claude", "sonnet"),
    "reviewer": ("claude", "opus"),
    "integrator": ("claude", "sonnet")
}
# Estimated cost: $1.50 - $2.50
```

## Machine Learning Enhancement

### Training Data
```json
{
  "task": "Add user login",
  "complexity_score": 0.65,
  "selected_strategy": "balanced",
  "providers": {
    "architect": "claude-sonnet",
    "implementer": "codex"
  },
  "outcome": {
    "success": true,
    "duration": 360,
    "tokens": 12453,
    "cost": 0.42
  }
}
```

### Model
- **Algorithm**: Random Forest Classifier
- **Features**: Task keywords (TF-IDF), historical metrics
- **Output**: Optimal strategy (cost-optimized, balanced, quality-first)
- **Training**: Periodic retraining on new run data

## Implementation Files

### New Files
1. `multi_agent/task_analyzer.py` (~300 lines)
   - Complexity scoring
   - Keyword extraction
   - Scope detection

2. `multi_agent/strategy_selector.py` (~200 lines)
   - Strategy selection logic
   - Provider mapping
   - Cost estimation

3. `multi_agent/ml_selector.py` (~250 lines, optional)
   - ML model training
   - Prediction
   - Feature extraction

### Modified Files
1. `multi_agent_codex.py` (+50 lines)
   - `--auto-select-providers` flag
   - `--strategy` override flag
   - Integration with TaskAnalyzer

2. `multi_agent/pipeline.py` (+30 lines)
   - Use auto-selected providers if enabled

## Usage Examples

### Example 1: Automatic Selection
```bash
$ python multi_agent_codex.py \
    --task "Fix bug in auth module" \
    --auto-select-providers \
    --apply

[Task Analysis]
Complexity: LOW (0.22)
Strategy: Cost-Optimized
Providers: gemini (flash), codex
Estimated: $0.12, 2m

Proceed? [Y/n]
```

### Example 2: Override Strategy
```bash
$ python multi_agent_codex.py \
    --task "Redesign database schema" \
    --auto-select-providers \
    --strategy quality-first \
    --apply

[Task Analysis]
Complexity: HIGH (0.85)
Strategy: Quality-First (user override)
Providers: claude (opus), claude (sonnet)
Estimated: $2.10, 12m

Proceed? [Y/n]
```

### Example 3: Budget Constraint
```bash
$ python multi_agent_codex.py \
    --task "Implement new feature X" \
    --auto-select-providers \
    --max-cost 0.50 \
    --apply

[Task Analysis]
Complexity: MEDIUM (0.58)
Strategy: Balanced → Cost-Optimized (budget constraint)
Max Budget: $0.50
Selected to stay under budget.

Providers: gemini (flash), codex, claude (haiku)
Estimated: $0.35

Proceed? [Y/n]
```

## Testing Strategy

### Unit Tests
- Task complexity scoring accuracy
- Strategy selection logic
- Provider mapping

### Integration Tests
- End-to-end with different task types
- Verify cost estimates
- Validate provider assignments

### A/B Testing
- Compare auto-selected vs manual configs
- Measure success rate
- Track cost savings

## Success Metrics

- **Cost Reduction**: 30-50% average savings
- **Accuracy**: 80%+ optimal strategy selection
- **User Adoption**: 70%+ use auto-select
- **Satisfaction**: 4.5/5 stars from users

## Rollout Plan

### Phase 1 (Day 1-2): Core Logic
- TaskAnalyzer implementation
- StrategySelector implementation
- Basic keyword matching

### Phase 2 (Day 2-3): Integration
- CLI integration
- Pipeline integration
- Testing

### Phase 3 (Day 3-4): ML Enhancement
- Historical data collection
- Model training
- Prediction integration

### Phase 4 (Day 4): Polish
- Documentation
- Examples
- User testing
