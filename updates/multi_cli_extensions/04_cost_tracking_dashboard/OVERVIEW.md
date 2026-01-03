# Feature 4: Cost Tracking Dashboard

## Quick Summary
Umfassendes Dashboard für Echtzeit-Kosten-Tracking, Budget-Management und ROI-Analyse über alle CLI-Provider.

## Priority: 🟡 MEDIUM
- **Impact**: ⭐⭐⭐⭐ (Budget-Kontrolle, Transparenz)
- **Effort**: Medium-High (4-5 Tage)
- **ROI**: Hoch - ermöglicht datenbasierte Optimierung

## Key Features

### 1. Real-time Cost Tracking
- Live-Berechnung während Pipeline-Ausführung
- Token-basierte Kosten pro Provider/Modell
- Granulare Aufteilung nach Agent und Rolle

### 2. Budget Management
- Budget-Limits setzen (täglich, wöchentlich, monatlich)
- Alerts bei Überschreitung
- Auto-Pause bei Budget-Erreichen (optional)

### 3. Analytics & Reporting
- Kosten-Trends über Zeit
- Provider-Vergleich
- ROI-Berechnung
- Exportierbare Reports (CSV, PDF)

### 4. Optimization Insights
- Teuerste Rollen identifizieren
- Provider-Switch Empfehlungen
- Cost-per-Success Metriken

## Database Schema

```sql
-- Run Costs
CREATE TABLE run_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    family_id TEXT,
    task TEXT,
    total_cost_usd REAL,
    total_tokens INTEGER,
    duration_sec REAL,
    status TEXT,  -- success, failed
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

-- Agent Costs (per agent execution)
CREATE TABLE agent_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    role_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,  -- codex, claude, gemini
    model TEXT,  -- sonnet, opus, gemini-2.5-flash
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd REAL,
    duration_sec REAL,
    timestamp INTEGER,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

-- Budget Settings
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period TEXT NOT NULL,  -- daily, weekly, monthly
    limit_usd REAL NOT NULL,
    alert_threshold REAL,  -- 0.0-1.0 (e.g., 0.8 = 80%)
    auto_pause BOOLEAN DEFAULT 0,
    created_at INTEGER,
    updated_at INTEGER
);

-- Budget Usage (tracking)
CREATE TABLE budget_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_id INTEGER NOT NULL,
    period_start INTEGER,
    period_end INTEGER,
    spent_usd REAL DEFAULT 0,
    run_count INTEGER DEFAULT 0,
    FOREIGN KEY(budget_id) REFERENCES budgets(id)
);
```

## Cost Calculation

### Provider Pricing (from cli_config.json)

```json
{
  "cost_tracking": {
    "enabled": true,
    "providers": {
      "codex": {
        "input_cost_per_1k": 0.002,
        "output_cost_per_1k": 0.006
      },
      "claude": {
        "sonnet": {
          "input_cost_per_1m": 3.0,
          "output_cost_per_1m": 15.0
        },
        "opus": {
          "input_cost_per_1m": 15.0,
          "output_cost_per_1m": 75.0
        },
        "haiku": {
          "input_cost_per_1m": 0.80,
          "output_cost_per_1m": 4.0
        }
      },
      "gemini": {
        "gemini-2.5-pro": {
          "input_cost_per_1m": 1.25,
          "output_cost_per_1m": 5.0
        },
        "gemini-2.5-flash": {
          "input_cost_per_1m": 0.075,
          "output_cost_per_1m": 0.30
        }
      }
    }
  }
}
```

### Cost Calculation Logic

```python
def calculate_agent_cost(
    provider_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing: Dict
) -> float:
    """Calculate cost for single agent execution."""

    provider_pricing = pricing["providers"][provider_id]

    if provider_id == "codex":
        # Codex: per 1k tokens
        input_cost = (input_tokens / 1000) * provider_pricing["input_cost_per_1k"]
        output_cost = (output_tokens / 1000) * provider_pricing["output_cost_per_1k"]

    elif provider_id in ["claude", "gemini"]:
        # Claude/Gemini: per 1M tokens
        model_pricing = provider_pricing.get(model, provider_pricing["default"])
        input_cost = (input_tokens / 1_000_000) * model_pricing["input_cost_per_1m"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output_cost_per_1m"]

    return input_cost + output_cost
```

## Dashboard Views

### 1. Overview Dashboard

```
┌──────────────────────────────────────────────────────────┐
│  Cost Dashboard                        [Export] [Settings]│
├──────────────────────────────────────────────────────────┤
│                                                            │
│  Current Month                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Total Spent  │  │  Total Runs  │  │ Avg per Run  │   │
│  │   $45.32     │  │     127      │  │    $0.36     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                            │
│  Budget: $100.00    Used: ████████░░ 45%                 │
│  Remaining: $54.68                                        │
│                                                            │
│  Cost Trend (Last 30 Days)                                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  $                                                  │  │
│  │ 5│                                        ●         │  │
│  │ 4│                              ●       ●           │  │
│  │ 3│                    ●       ●                     │  │
│  │ 2│          ●       ●                               │  │
│  │ 1│    ●   ●                                         │  │
│  │ 0├─────────────────────────────────────────────────┤  │
│  │   Dec 1        Dec 10       Dec 20      Dec 31     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  Top 5 Costliest Runs                                     │
│  ┌────┬────────────────┬────────┬──────────┬─────────┐   │
│  │ # │ Run ID          │ Family │ Cost     │ Date    │   │
│  ├────┼────────────────┼────────┼──────────┼─────────┤   │
│  │ 1 │ 2025-12-30_...  │ dev    │ $2.45    │ Dec 30  │   │
│  │ 2 │ 2025-12-28_...  │ design │ $1.82    │ Dec 28  │   │
│  │ 3 │ 2025-12-25_...  │ dev    │ $1.67    │ Dec 25  │   │
│  └────┴────────────────┴────────┴──────────┴─────────┘   │
└──────────────────────────────────────────────────────────┘
```

### 2. Provider Breakdown

```
┌──────────────────────────────────────────────────────────┐
│  Provider Cost Breakdown                                  │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────────────────────────────────────────────┐  │
│  │                                                     │  │
│  │    Codex        Claude         Gemini              │  │
│  │   ████████      ██████         ███                 │  │
│  │   $18.20        $22.10         $5.02               │  │
│  │   (40%)         (49%)          (11%)               │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  Claude Model Breakdown                                   │
│  - Opus:   $12.50 (56%)                                   │
│  - Sonnet: $8.30  (38%)                                   │
│  - Haiku:  $1.30  (6%)                                    │
│                                                            │
│  Optimization Suggestion:                                 │
│  💡 Switch Opus → Sonnet for reviewer role                │
│     Potential savings: ~$4.20/month (9%)                  │
│     Impact: Minimal quality difference for this use case  │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 3. Role Cost Analysis

```
┌──────────────────────────────────────────────────────────┐
│  Cost by Role                                             │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────┬──────────┬──────────┬───────────┬──────┐ │
│  │ Role       │ Avg Cost │ Runs     │ Provider  │ %    │ │
│  ├────────────┼──────────┼──────────┼───────────┼──────┤ │
│  │ architect  │  $0.18   │  127     │ claude    │ 50%  │ │
│  │ implementer│  $0.08   │  127     │ codex     │ 22%  │ │
│  │ reviewer   │  $0.06   │  98      │ claude    │ 17%  │ │
│  │ tester     │  $0.03   │  127     │ gemini    │  8%  │ │
│  │ integrator │  $0.01   │  127     │ claude    │  3%  │ │
│  └────────────┴──────────┴──────────┴───────────┴──────┘ │
│                                                            │
│  📊 Insight: Architect role accounts for 50% of costs     │
│     Consider: Haiku for simple architecture tasks         │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

## Budget Management

### Setting Budgets

```python
from multi_agent.cost_tracker import CostTracker

tracker = CostTracker()

# Monthly budget
tracker.set_budget(
    period="monthly",
    limit_usd=100.00,
    alert_threshold=0.8,  # Alert at 80%
    auto_pause=False  # Don't auto-pause runs
)

# Check current usage
usage = tracker.get_current_usage("monthly")
print(f"Spent: ${usage.spent_usd} / ${usage.limit_usd}")
print(f"Remaining: ${usage.remaining_usd}")
```

### Budget Alerts

```python
# In pipeline.py, before starting run
def check_budget_before_run(estimated_cost: float):
    tracker = CostTracker()
    usage = tracker.get_current_usage("monthly")

    if usage.spent_usd + estimated_cost > usage.limit_usd:
        raise BudgetExceededError(
            f"This run would exceed monthly budget. "
            f"Spent: ${usage.spent_usd}, "
            f"Estimated: ${estimated_cost}, "
            f"Limit: ${usage.limit_usd}"
        )

    if usage.percent_used > 0.8:
        print(f"⚠️  Warning: 80% of monthly budget used ({usage.percent_used:.0%})")
```

## Reporting & Export

### CSV Export

```python
# Export run costs
tracker.export_run_costs(
    start_date="2025-12-01",
    end_date="2025-12-31",
    output_path="reports/december_costs.csv"
)

# CSV format:
# run_id,timestamp,family,task,provider,model,tokens,cost_usd,duration_sec
```

### PDF Report

```python
# Generate monthly report
tracker.generate_report(
    period="monthly",
    year=2025,
    month=12,
    output_path="reports/december_2025.pdf"
)

# Includes:
# - Summary statistics
# - Cost trends chart
# - Provider breakdown
# - Top runs table
# - Optimization suggestions
```

## Implementation

### New Files
1. `multi_agent/cost_tracker.py` (~400 lines)
   - Cost calculation
   - Budget management
   - Database operations

2. `multi_agent/cost_db.py` (~200 lines)
   - SQLite schema
   - Query builders

3. `multi_agent/cost_reporter.py` (~250 lines)
   - Report generation
   - Export functions
   - Visualization

4. `multi_agent/cost_optimizer.py` (~150 lines)
   - Analysis
   - Optimization suggestions

### Modified Files
1. `multi_agent/pipeline.py` (+80 lines)
   - Track costs during execution
   - Budget checks
   - Store cost data

2. `multi_agent/codex.py` (+30 lines)
   - Token counting
   - Cost calculation per agent

3. `multi_agent_codex.py` (+40 lines)
   - `--show-costs` flag
   - `--budget-check` flag

## CLI Commands

```bash
# Show cost summary
python multi_agent_codex.py costs summary

# Show cost breakdown
python multi_agent_codex.py costs breakdown --by provider

# Export costs
python multi_agent_codex.py costs export \
  --format csv \
  --start-date 2025-12-01 \
  --output december.csv

# Set budget
python multi_agent_codex.py costs budget \
  --period monthly \
  --limit 100.00 \
  --alert-at 80%

# Get optimization suggestions
python multi_agent_codex.py costs optimize
```

## Testing

### Unit Tests
- Cost calculation accuracy
- Budget tracking
- Alert triggering

### Integration Tests
- End-to-end cost tracking
- Database persistence
- Export formats

## Success Metrics

- **Tracking Accuracy**: 99%+ correct cost calculations
- **Adoption**: 80%+ users enable cost tracking
- **Budget Compliance**: < 5% budget overruns
- **ROI**: Users save 20%+ through insights

## Rollout Plan

### Week 1 (Days 1-2): Core Tracking
- Database schema
- Cost calculation logic
- Pipeline integration

### Week 2 (Days 3-4): Budget Management
- Budget setting/tracking
- Alerts system
- Auto-pause feature

### Week 3 (Day 5): Reporting
- CLI commands
- Export functions
- Report generation

### Week 4: Integration with Web-UI
- Dashboard views
- Charts
- Real-time updates
