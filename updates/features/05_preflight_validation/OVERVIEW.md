# Feature 05: Pre-Flight Validation & Cost Estimation

## Quick Summary
Show execution plan, estimate cost/time, validate task before running pipeline.

## Priority: 🟡 SHOULD HAVE
- **Impact**: ⭐⭐
- **Effort**: Medium (2-3 days)
- **ROI**: High (transparency, no surprises)

## Key Features
1. **Dry-Run Mode**: Show plan without execution
2. **Cost Estimation**: Token count → API cost estimate
3. **Time Estimation**: Based on historical runs + role timeouts
4. **File Impact Preview**: Which files will be modified
5. **Sanity Checks**: Task mentions non-existent files → warn

## Example Output
```
🔍 Pre-Flight Check: developer_main.json

Execution Plan:
  1. architect (1 instance, ~800 tokens, ~45s)
  2. implementer (1 instance, ~1200 tokens, ~90s)
  3. tester (1 instance, ~600 tokens, ~30s)
  4. reviewer (1 instance, ~400 tokens, ~20s)
  5. integrator (1 instance, ~300 tokens, ~15s)

Estimated:
  Total Time: ~3.5 minutes
  Total Tokens: ~3300 tokens
  Cost (GPT-4): ~$0.10

File Impact:
  Will likely modify: src/auth/*.py, tests/test_auth.py

⚠️  Warnings:
  - Task mentions 'user_model.py' which doesn't exist in snapshot

Continue? [Y/n]
```

## Implementation
```python
class PreFlightValidator:
    def validate(self, task: str, config: AppConfig, workspace: Path):
        # 1. Estimate token usage
        # 2. Estimate time from historical data
        # 3. Check file references in task
        # 4. Validate dependencies
        # 5. Return ValidationResult

    def estimate_cost(self, token_count: int, model: str) -> float:
        # Model-specific pricing
        pass
```

## Files
- `multi_agent/preflight.py` (new, ~250 lines)
- `multi_agent/cli.py` (add --dry-run, ~20 lines)

See `IMPLEMENTATION.md` for full details.
