# Feature 04: Output Quality Scoring

## Quick Summary
Evaluate agent output quality with automated scoring metrics (completeness, confidence, diff quality, consistency).

## Priority: 🟡 SHOULD HAVE
- **Impact**: ⭐⭐
- **Effort**: Medium (3-4 days)
- **ROI**: High (better quality, automatic rejection of poor outputs)

## Key Components
1. **CompletenessScorer**: Checks expected_sections, required fields
2. **ConfidenceScorer**: Analyzes agent self-assessment, uncertainty markers
3. **DiffQualityScorer**: Evaluates diff size, file count, complexity
4. **ConsistencyScorer**: Detects contradictions, logical errors

## Implementation Highlights
```python
@dataclass
class QualityScore:
    completeness: float  # 0.0-1.0
    confidence: float
    diff_quality: float
    consistency: float
    overall: float       # Weighted average

    def is_acceptable(self, threshold: float = 0.7) -> bool:
        return self.overall >= threshold

# Usage
scorer = QualityScorer()
score = scorer.evaluate(output, role_config, context)

if not score.is_acceptable():
    # Automatic retry with feedback
    retry_with_quality_feedback(score)
```

## Configuration
```json
{
  "quality_scoring": {
    "enabled": true,
    "threshold": 0.7,
    "auto_reject_below": 0.5,
    "weights": {
      "completeness": 0.4,
      "confidence": 0.2,
      "diff_quality": 0.3,
      "consistency": 0.1
    }
  }
}
```

## Files
- `multi_agent/quality_scoring.py` (new, ~300 lines)
- `multi_agent/pipeline.py` (integrate scoring, ~50 lines modified)

See `IMPLEMENTATION.md` for full details.
