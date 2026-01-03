# Streaming Guide

This guide explains the real-time streaming feature (Feature 02).

## Overview

Streaming shows live agent output while a CLI provider is running. It adds:

- Live output preview (last N lines)
- Token counter (heuristic or tiktoken)
- Elapsed time and progress estimate
- Graceful Ctrl+C handling

## Requirements

- Optional: `rich` for the TUI progress display
- Optional: `tiktoken` for accurate token counting

Without `rich`, streaming falls back to plain line-by-line output.

## Configuration

Add (or override) the streaming config in your family config:

```json
{
  "streaming": {
    "enabled": true,
    "refresh_rate_hz": 4,
    "output_preview_lines": 10,
    "buffer_max_lines": 1000,
    "token_counting": "heuristic"
  }
}
```

`token_counting` accepts `heuristic` or `tiktoken` (if installed).

## CLI Flags

- Disable streaming: `--no-streaming`

## Runtime Behavior

- Streaming runs only on TTY outputs (auto-disabled in CI/non-TTY).
- Parallel roles/instances keep streaming enabled, but fall back to plain output with instance prefixes (`role_id#n`).
- Output is still collected and written to `.multi_agent_runs/` as before.
- Retries also stream output.

## Cancellation

- First Ctrl+C: mark run as cancelled, stop the current process.
- Second Ctrl+C: force quit.

The run meta is still saved to `run.json`.

## Resume

If a run is cancelled, a `resume.json` file is written in the run directory.
You can resume from the next role with:

```bash
python multi_agent_codex.py task --resume-run <run_id_or_path>
```

The original snapshot is reused during resume.

## Troubleshooting

If you see no live output:

1. Ensure `rich` is installed (optional but recommended).
2. Check you are in a TTY shell.
3. Ensure `--no-streaming` is not set.
