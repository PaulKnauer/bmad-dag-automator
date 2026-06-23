# BMAD DAG Automator — Project Context

## Overview

DAG-aware autonomous agent orchestration tool. Extends the BMAD methodology with topological dependency scheduling, LLM-assisted dependency induction, and elastic agent scaling via tmux sessions.

**Flow:** BMAD Sprint Planning → DAG Induction → Level-by-Level Execution → Finalize

**Dependency modes:** `minimal` (explicit only), `assisted` (LLM suggests, user approves), `automatic` (LLM adds immediately)

---

## 1. Technology Stack

- **Python 3** (stdlib + pyyaml) — no framework, no virtualenv tracked
- **Testing:** pytest, tests in `tests/` directory
- **No CI/CD pipeline**
- **No build system** (pure Python, no setup.py/pyproject.toml/Dockerfile)

## 2. Module Map

| Module | Purpose |
|--------|---------|
| `dag_core.py` | Core data model (DagNode, DagGraph, DagLevel), Kahn's algorithm, cycle detection, critical path computation |
| `dag_induction.py` | Story parsing + LLM-based implicit dependency inference (3 modes) |
| `dag_scheduler.py` | CLI entry point: `validate`, `schedule`, `orchestrate` commands |
| `dag_orchestrator.py` | Full execution loop: induct → level loop → finalize |
| `agent_pool.py` | Elastic tmux session manager (scales per DAG level width) |
| `artifact_bridge.py` | Git branch-per-level management |
| `state_doc.py` | Markdown state document (human + machine readable) |

## 3. Language & Style Rules

- **Snake_case** for functions and variables
- **PascalCase** for classes and enums
- **Module names:** snake_case
- **Type hints:** used throughout (`from __future__ import annotations`)
- **Error handling:** raise exceptions (no silent failures), error messages stored in `DagGraph.error`
- **Dataclasses** used for data models (DagNode, DagGraph, DagLevel, AgentConfig, etc.)
- **Enums** for status/state (NodeStatus, GraphStatus, InductionMode, AgentStatus, etc.)
- **No type stubs** — inline annotations only

## 4. Key Data Structures

### DagNode
- Fields: `id`, `title`, `explicit_deps`, `implicit_deps`, `suggested_deps`, `file_scope`, `interfaces_provides`, `consumes_interfaces`, `level`, `status`
- Property: `all_deps` = explicit + implicit (excludes suggestions)
- Method: `to_dict()` for serialization

### DagGraph
- Fields: `mode`, `nodes` (dict[str, DagNode]), `levels` (list[DagLevel]), `status`, `critical_path`, `has_cycle`, `cycle_path`, `error`
- Methods: `add_node()`, `get_node()`, `schedule()`, `to_dict()`, `to_yaml()`
- Static: `from_story_list(stories, mode)` — factory from dict list
- Internal: `_build_adjacency()`, `find_dangling_refs()`, `detect_cycles()`, `topological_levels()`, `compute_critical_path()`

### Scheduling Pipeline (`schedule()`)
1. Validate for dangling refs
2. Cycle detection (Kahn's algorithm)
3. Topological level assignment
4. Critical path (longest path via DP)

### Induction Modes
- **MINIMAL:** skip LLM pass entirely, explicit deps only
- **ASSISTED:** LLM suggested edges go to `suggested_deps`, user promotes/rejects
- **AUTOMATIC:** LLM edges go directly to `implicit_deps`

## 5. CLI Usage

```bash
# Validate a story set
python dag_scheduler.py validate examples/auth-system.yaml

# Schedule with explicit deps only
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Full dry-run orchestrator (no tmux, no git)
python dag_scheduler.py --mode minimal orchestrate examples/auth-system.yaml --dry-run
```

## 6. Testing Rules

- **Framework:** pytest-style assertions (no pytest runner required — tests use `if __name__ == "__main__"` with manual test runner)
- **Location:** all tests in `tests/` directory
- **Test setup:** `sys.path.insert(0, ..)` to add project root
- **Test coverage focus:** core algorithms (DAG scheduling, cycle detection, induction modes, critical path, edge cases)
- **Pattern:** pure unit tests — no mocking, no fixtures, no external dependencies
- **No coverage tool configured**
- **Edge cases tested:** single node, empty graph, self-dependency, elastic allocation

## 7. BMAD Workflow Rules

- **Branch-per-level model** — each DAG level gets its own branch
- **Phase order:** BMM → BMB → CIS → TEA lifecycle
- **Dossiers** precede implementation (research docs in `dossiers/`)
- **YAML specs** define DAG schedules before coding
- **Examples directory** (`examples/`) contains reference YAML/JSON schedules

## 8. Security

- No auth, secrets, credentials, or network calls in this project
- Local-only orchestration tool (reads YAML, spawns tmux, manages git branches)
