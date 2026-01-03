# TEST_PLAN – Echte Parallelität via Sharding

## Unit Tests
1) ShardPlanner headings determinism
- Input: tasks/golden_path.md
- Expect: same shard ids/titles/goals every run

2) Diff touched files extraction
- Input: minimal unified diff
- Expect: set of touched file paths

3) Overlap policy forbid
- Input: two diffs touching same file
- Expect: validation fails with overlap report

## Integration Tests
1) Pipeline stage with mocked codex runner
- Setup: role.instances=3, shard_mode=headings
- Mock: runner returns diffs for files inside allowed paths per shard
- Expect:
  - 3 instance outputs
  - stage summary contains 3 shards, no overlaps
  - apply (if enabled) applies in shard order

## Golden Path Criteria
- No instance gets the full task when sharding is enabled
- Role summary artifact includes touched_files per shard
- When overlap occurs and policy forbid -> role fails clearly
