# Workflow Diagrams (Mermaid)

This document summarizes the most important runtime flows in the orchestrator
with Mermaid diagrams and short, implementation-focused notes.

## 1) Entry and Run Selection

```mermaid
graph TD
  A[CLI entrypoint] --> B[run_pipeline]
  B --> C{task_split enabled?}
  C --|no|--> D[pipeline run]
  C --|yes|--> E[run_split]
  D --> F[exit code]
  E --> F
```

Details:
- The CLI calls `run_pipeline`, which decides between a single run or task split.
- Task split is enabled via `--task-split` or `task_split.enabled`.
- Source: `multi_agent/run_helpers.py`

## 2) Task Split (Multi-Run Orchestration)

```mermaid
graph TD
  A[run_split] --> B[load_task_text]
  B --> C{needs_split?}
  C --|no|--> D[pipeline run single]
  C --|yes|--> E[build or load manifest]
  E --> F[create chunks]
  F --> G[write base chunks and manifest]
  G --> H[loop over chunks]
  H --> I[build chunk payload and carry over]
  I --> J[pipeline run per chunk]
  J --> K[update manifest and carry over]
  K --> H
  D --> L[exit code]
  H --> L
```

Details:
- Chunk creation uses heading-based splitting (config `heading_level`) and size limits.
- Optional LLM planning is used only if `task_split.llm_cmd` is set; otherwise it falls back.
- Each chunk run is a normal pipeline run with its own run id and output directory.
- Source: `multi_agent/run_helpers.py`, `multi_agent/task_split.py`

## 3) Pipeline Core Run

```mermaid
graph TD
  A[pipeline run] --> B[_prepare_task]
  B --> C[snapshot workspace]
  C --> D[initialize coordination]
  D --> E[_run_roles]
  E --> F{apply mode end?}
  F --|yes|--> G[apply diffs at end]
  F --|no|--> H[skip apply]
  G --> I[write logs and summary]
  H --> I
  I --> J[exit code]
```

Details:
- `_prepare_task` normalizes inline or `@file` tasks and writes `task_full.*` if needed.
- Snapshot text is injected into the prompt context for all roles.
- Coordination writes task-board and log entries under `.multi_agent_runs/<run_id>/`.
- Source: `multi_agent/pipeline.py`

## 4) Role Execution and Sharding

```mermaid
graph TD
  A[_run_roles] --> B[select ready roles]
  B --> C[_run_role per role]
  C --> D[create_shard_plan]
  D --> E[spawn role instances]
  E --> F[_run_role_instance]
  F --> G[claim task and build prompt]
  G --> H[execute agent and retries]
  H --> I[finalize instance]
  I --> J[validate shards overlaps and allowed paths]
  J --> K[combine outputs]
  K --> L{apply mode role?}
  L --|yes|--> M[apply diffs and resnapshot]
  L --|no|--> N[skip apply]
  M --> O[role complete]
  N --> O
```

Details:
- Sharding is per role and per run; it is not global.
- `headings` mode uses H1 sections; `files` mode infers allowed paths from task text.
- Shard validation uses diff extraction to detect overlaps and allowed path violations.
- Source: `multi_agent/pipeline.py`, `multi_agent/sharding.py`, `multi_agent/diff_utils.py`

## 5) Diff Application (Role or End)

```mermaid
graph TD
  A[diffs produced by role instances] --> B{apply mode}
  B --|role|--> C[apply diffs after role]
  B --|end|--> D[apply diffs after all roles]
  C --> E[update snapshot and last applied diff]
  D --> E
```

Details:
- `apply_mode=role` applies diffs per role and refreshes the snapshot used by next roles.
- `apply_mode=end` defers all changes until the pipeline finishes.
- Source: `multi_agent/pipeline.py`, `multi_agent/diff_applier.py`
