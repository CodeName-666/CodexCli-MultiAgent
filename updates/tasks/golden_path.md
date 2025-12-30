# Chunk 1: Add sharding config fields
## Goal
Add new RoleConfig fields and ensure JSON config loading + schema validation supports them.

## Allowed paths
- multi_agent/models.py
- multi_agent/config_loader.py
- multi_agent/schema_validator.py

## Definition of done
- Existing configs still work
- New fields are accepted and have defaults

# Chunk 2: Implement headings-based shard planner
## Goal
Create a deterministic ShardPlanner for headings-based splitting.

## Allowed paths
- multi_agent/sharding.py
- multi_agent/task_split.py (reuse allowed)
- multi_agent/run_logger.py (if needed for persistence)

## Definition of done
- Given this markdown task, planner returns 2+ shards deterministically

# Chunk 3: Pipeline uses shards for instances
## Goal
If role.instances > 1 AND shard_mode != none, each instance gets its own shard prompt and runs in parallel.

## Allowed paths
- multi_agent/pipeline.py
- multi_agent/sharding.py
- multi_agent/diff_utils.py

## Definition of done
- Instanz #1/#2/#3 run with different subtask text
- Stage barrier validates overlaps and writes summary json
