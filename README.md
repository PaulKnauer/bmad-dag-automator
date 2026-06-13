# BMAD DAG Automator

DAG-aware autonomous agent orchestration — extends BMAD with topological dependency scheduling and elastic agent scaling.

## Flow

```
BMAD Sprint Planning → DAG Induction → Level-by-Level Execution → Finalize
```

Three modes for dependency inference: `minimal`, `assisted`, `automatic`.

## Files

| Module | Purpose |
|--------|---------|
| `dag_core.py` | DAG data model, Kahn's algorithm, critical path |
| `dag_induction.py` | Story parsing + LLM-based implicit dependency inference |
| `dag_scheduler.py` | CLI: schedule, validate, orchestrate |
| `dag_orchestrator.py` | Full execution loop (induct → level loop → finalize) |
| `agent_pool.py` | Elastic tmux session manager per DAG level |
| `artifact_bridge.py` | Git branch-per-level management |
| `state_doc.py` | Markdown state document (automator-compatible) |

## Quick Start

```bash
# Validate a story set
python dag_scheduler.py validate examples/auth-system.yaml

# Schedule with explicit deps only
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Full dry-run orchestrator
python dag_scheduler.py --mode minimal orchestrate examples/auth-system.yaml --dry-run
```

## Tests

```bash
python tests/test_dag_core.py
python tests/test_dry_run.py
```
