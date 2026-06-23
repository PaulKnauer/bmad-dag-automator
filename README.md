# BMAD DAG Automator

DAG-aware autonomous agent orchestration — extends BMAD with topological dependency scheduling, elastic agent scaling, and production-hardened run management.

**Tests:** 52 passing (17 core + 8 resume + 9 validator + 12 failure + 6 benchmarks)

## Quick Install

```bash
git clone https://github.com/nousresearch/bmad-dag-automator.git
cd bmad-dag-automator
python dag_scheduler.py validate examples/auth-system.yaml   # check it works
```

> **📖 Full install walkthrough:** [INSTALL.md](INSTALL.md) — covers dependencies, virtualenv setup, and troubleshooting.

## Getting Started

New to the DAG Automator? Start with the beginner's guide:

- **[GETTING_STARTED.md](GETTING_STARTED.md)** — step-by-step walkthrough with the auth system example
- Validate a story set: `python dag_scheduler.py validate examples/auth-system.yaml`
- Dry-run full orchestration: `python dag_scheduler.py orchestrate examples/auth-system.yaml --dry-run`

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

All commands are run via `dag_scheduler.py`. Six subcommands available:

### `validate` — Validate story YAML for structural correctness
```bash
python dag_scheduler.py validate examples/auth-system.yaml
```
Checks: dangling refs, cycles, dep stats. Exit code 0 = valid.

### `schedule` — Build topological DAG and generate execution manifest
```bash
python dag_scheduler.py schedule examples/auth-system.yaml --mode automatic
```
Outputs `dag-manifest.yaml` with levels, critical path, node metadata.

### `orchestrate` — Run the full DAG orchestrator (live or dry-run)
```bash
python dag_scheduler.py orchestrate examples/auth-system.yaml --dry-run
python dag_scheduler.py orchestrate examples/auth-system.yaml --project . --agent claude-code --resume
```
Full flags: `--project`, `--mode`, `--agent`, `--model`, `--max-concurrent`, `--dry-run`, `--resume`.

### `validate-dag` — Validate DAG consistency from a prior run's artifacts
```bash
python dag_scheduler.py validate-dag --project /path/to/project
```
Checks: manifest vs state doc, orphaned nodes, node existence, level boundaries. Exit: 0=PASS, 1=FAIL, 2=WARN.

### `inspect` — Dump full DAG internal state as YAML
```bash
python dag_scheduler.py inspect examples/auth-system.yaml
```
Shows all nodes, edges, levels, and status in a single output.

### `apply-llm` — Apply LLM-generated edge suggestions from stdin
```bash
cat llm_output.json | python dag_scheduler.py apply-llm examples/auth-system.yaml
```
Applies inferred dependencies without re-running the LLM.

---

## Documentation Map

| Document | Audience | Purpose |
|----------|----------|---------|
| [INSTALL.md](INSTALL.md) | New users | Step-by-step installation guide |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Beginners | First-time walkthrough with the auth system |
| [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) | Operators / Devs | In-depth CLI reference, config, production tips |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Contributors | Test suite reference, patterns, CI notes |

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
