---
name: bmad-dag-schedule
description: "Run DAG scheduling on story YAML. Use when the user says 'run dag schedule', 'schedule stories', or 'build dag manifest'."
---

# BMAD DAG Schedule

## Overview

Runs the DAG Scheduler on a story YAML file — parses explicit deps, induces implicit edges (optional), and produces a topological schedule with levels, critical path, and node metadata.

## Usage

```bash
cd {project-root}

# Basic schedule (minimal mode — explicit deps only)
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Automatic mode (LLM adds implicit edges)
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml

# Assisted mode (LLM edges flagged for review)
python dag_scheduler.py --mode assisted schedule examples/auth-system.yaml --llm-output edges.json

# Validate (check dangling refs + cycles, no scheduling)
python dag_scheduler.py validate examples/auth-system.yaml

# Validate DAG consistency from prior run
python dag_scheduler.py validate-dag --project {project-root}
```

## Output

Writes `dag-manifest.yaml` with:
- Topological levels (parallelism at each depth)
- Critical path (longest path through the DAG)
- Per-node metadata (deps, file scope, interfaces)
- Node status (pending by default)

## Integration

The DAG Automator integrates with BMAD's existing `bmad-story-automator` — it replaces the linear story loop with level-based execution. Feed it a sprint-status.yaml or story YAML.
