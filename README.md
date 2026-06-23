# BMAD DAG Automator

DAG-aware autonomous agent orchestration — extends BMAD with topological dependency scheduling, elastic agent scaling, and production-hardened run management.

**Tests:** 52 passing (17 core + 8 resume + 9 validator + 12 failure + 6 benchmarks)

---

## Flow

```
BMAD Sprint Planning → DAG Induction → Level-by-Level Execution → Finalize
```

Three modes for dependency inference: `minimal`, `assisted`, `automatic`.

---

## Files

| Module | Purpose |
|--------|---------|
| `dag_core.py` | DAG data model, Kahn's algorithm, critical path |
| `dag_induction.py` | Story parsing + LLM-based implicit dependency inference |
| `dag_scheduler.py` | CLI: validate, schedule, orchestrate, inspect, apply-llm |
| `dag_orchestrator.py` | Full execution loop (induct → level loop → finalize) |
| `agent_pool.py` | Elastic tmux session manager per DAG level |
| `artifact_bridge.py` | Git branch-per-level management |
| `state_doc.py` | Markdown state document (automator-compatible) |
| `dag_validator.py` | DAG consistency checks (manifest vs state, orphans, boundaries) |
| `benchmarks/` | Scheduling performance benchmarks (4 DAG shapes) |

---

## Quick Start

```bash
# Validate a story set
python dag_scheduler.py validate examples/auth-system.yaml

# Schedule with explicit deps only
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Full dry-run orchestrator (no tmux, no git)
python dag_scheduler.py --mode minimal orchestrate examples/auth-system.yaml --dry-run
```

---

## CLI Reference

### `validate` — Validate story YAML
```bash
python dag_scheduler.py validate examples/auth-system.yaml
```
Checks: dangling refs, cycles, explicit dep stats. Exit code 0 = valid.

### `schedule` — Build DAG and schedule execution
```bash
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml
python dag_scheduler.py --mode assisted schedule examples/auth-system.yaml --llm-output edges.json
```
Outputs `dag-manifest.yaml` with levels, critical path, and node metadata.

### `orchestrate` — Run full DAG orchestrator
```bash
# Dry run (no tmux, no git)
python dag_scheduler.py orchestrate examples/auth-system.yaml --dry-run

# Live run with claude-code
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project \
    --mode automatic \
    --agent claude-code \
    --model sonnet \
    --max-concurrent 4

# Resume from last incomplete level
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project --resume
```

### `validate-dag` — Validate DAG consistency from prior run
```bash
python dag_scheduler.py validate-dag --project /path/to/project
```
Checks: manifest vs state doc, orphaned nodes, node existence, level boundaries.
Output:
```
  ✅ DAG Validation: PASS
  ──────────────────────────────────────────────────
  PASS — 4 passed

  ✅ Manifest vs State Doc    · 8 nodes, 4 levels
  ✅ Orphaned Nodes           · All 8 completed nodes exist in manifest
  ✅ Node Existence           · All 8 node(s) resolved
  ✅ Level Boundaries         · Level 0: 2/2 ✅  Level 1: 2/2 ✅
```
Exit code: 0 = PASS, 1 = FAIL, 2 = WARN.

### `inspect` — Show full DAG internal state
```bash
python dag_scheduler.py inspect examples/auth-system.yaml
```
Dumps the complete DAG as YAML (nodes, edges, levels, status).

### `apply-llm` — Apply LLM edge suggestions
```bash
cat llm_output.json | python dag_scheduler.py apply-llm examples/auth-system.yaml
```

---

## Phase 5: Production Hardening

### Resume from any DAG level

The orchestrator can resume from the last incomplete level after an interruption:

```bash
# Start a run
python dag_scheduler.py orchestrate examples/auth-system.yaml --project .

# If interrupted (Ctrl+C), state is saved with PAUSED status
# Resume later:
python dag_scheduler.py orchestrate examples/auth-system.yaml --project . --resume
```

Resume behaviour:
- Detects last completed level from `orchestration.md`
- Validates DAG manifest consistency (same nodes, same levels)
- Skips completed levels, starts from first incomplete level
- Gracefully warns if no prior state exists and starts fresh

### Graceful shutdown

On Ctrl+C (SIGINT):
1. Active sessions can be managed externally
2. State doc saved with PAUSED status
3. Resume flag shown for later continuation

### Edge case handling

| Scenario | Behaviour |
|----------|-----------|
| Empty story list | Early return with clear message |
| tmux not installed | `AgentResult(status=FAILED)` with descriptive error |
| Deep DAG (50+ levels) | Kahn's algorithm handles any depth |
| Single-story sprint | One level, one node, no overhead |

---

## Benchmarks

```bash
python benchmarks/bench_dag.py
```

Measures scheduling overhead across 4 DAG shapes:

```
Shape                Nodes  Lvls  Width  Sched   Serial  Par  Speed  Util
──────────────────── ────── ──── ─────── ─────── ─────── ──── ────── ─────
Serial Chain            10   10      1   0.10ms    10     1  10.0x  100%
Full Parallel           10    1     10   0.04ms    10    10   1.0x  100%
Fan-out/fan-in           7    3      5   0.05ms     7     5   1.4x  100%
Mixed                    8    5      2   0.05ms     8     2   4.0x  100%
```

---

## Tests

```bash
python tests/test_dag_core.py      # 17 tests — core algorithms
python tests/test_resume.py        # 8 tests — resume functionality
python tests/test_validator.py     # 9 tests — DAG validation
python tests/test_failure_modes.py # 12 tests — failure injection
python tests/test_benchmarks.py    # 6 tests — benchmark harness

# Or run all:
for t in tests/test_*.py; do python "$t"; done
```
