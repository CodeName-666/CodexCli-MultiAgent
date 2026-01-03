# Feature 08: Run Comparison & History Tracking

## Quick Summary
Database-backed run history with comparison, metrics dashboard, output reuse, and rollback capability.

## Priority: 🔵 NICE TO HAVE
- **Impact**: ⭐
- **Effort**: Medium-High (4-5 days)
- **ROI**: Debugging, optimization, learning

## Key Features
1. **SQLite History**: Store all runs with metadata
2. **Run Comparison**: `codex compare run1 run2` → diff outputs
3. **Metrics Dashboard**: Success rate, avg duration, token usage
4. **Output Reuse**: Successful agent outputs cached
5. **Rollback**: Revert applied diffs from previous run

## Example Usage
```bash
# List runs
$ codex runs
ID                     Date       Family     Task              Status   Duration
2025-12-31_10-00-00   10:00 AM   developer  Add login         Success  3m 45s
2025-12-31_09-30-00   09:30 AM   developer  Add login         Failed   2m 10s

# Compare runs
$ codex compare 2025-12-31_09-30-00 2025-12-31_10-00-00

Comparing runs:
  Run 1 (Failed):  architect ✓, implementer ✗ (missing sections)
  Run 2 (Success): architect ✓, implementer ✓, tester ✓

Output Diff (implementer):
  - Lines: 50 → 120 (+140%)
  - Sections: 2/4 → 4/4 (complete)
  - Files modified: 2 → 5

# Rollback applied changes
$ codex rollback 2025-12-31_10-00-00
Reverting 5 files modified in run 2025-12-31_10-00-00...
Done. Workspace restored to pre-run state.
```

## Database Schema
```sql
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    timestamp INTEGER,
    family TEXT,
    task TEXT,
    status TEXT,  -- success, failed, cancelled
    duration_sec REAL,
    total_tokens INTEGER,
    cost_usd REAL
);

CREATE TABLE agent_outputs (
    run_id TEXT,
    agent_name TEXT,
    output_md TEXT,
    tokens INTEGER,
    duration_sec REAL,
    status TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);

CREATE TABLE applied_diffs (
    run_id TEXT,
    file_path TEXT,
    diff_content TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
```

## Files
- `multi_agent/history_db.py` (new, ~300 lines)
- `multi_agent/run_comparator.py` (new, ~200 lines)
- `multi_agent/cli.py` (add subcommands, ~40 lines)

See `IMPLEMENTATION.md` for full details.
