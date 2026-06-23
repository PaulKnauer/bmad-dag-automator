# BMAD DAG Automator — Testing & Quality Guide

## Table of Contents

1. [Overview](#overview)
2. [Test Suite Structure](#test-suite-structure)
3. [How to Run Tests](#how-to-run-tests)
4. [Test File Reference](#test-file-reference)
   - [test_dag_core.py — Core Algorithms (17 tests)](#test_dag_corepy--core-algorithms-17-tests)
   - [test_resume.py — Resume Flow (8 tests)](#test_resumepy--resume-flow-8-tests)
   - [test_validator.py — DAG Consistency Checks (9 tests)](#test_validatorpy--dag-consistency-checks-9-tests)
   - [test_failure_modes.py — Failure Injection (12 tests)](#test_failure_modespy--failure-injection-12-tests)
   - [test_benchmarks.py — Benchmark Harness (6 tests)](#test_benchmarkspy--benchmark-harness-6-tests)
5. [Test Patterns & How to Write New Tests](#test-patterns--how-to-write-new-tests)
6. [Edge Case Coverage Summary](#edge-case-coverage-summary)
7. [Failure Injection Tests Deep Dive](#failure-injection-tests-deep-dive)
8. [Benchmark Harness](#benchmark-harness)
9. [Continuous Integration Notes](#continuous-integration-notes)

---

## Overview

The BMAD DAG Automator test suite contains **52 tests across 5 files**, plus a standalone benchmark harness. Tests cover the full pipeline: DAG construction, topological scheduling, LLM-assisted induction, resume from partial state, consistency validation, failure injection handling, and scheduling performance. The suite is designed to run **without external dependencies** (no tmux, no real agent spawning, no network calls) — all tests use in-memory graphs, temporary directories, and mocked subsystems.

**Quick stats:**

| Metric | Value |
|---|---|
| Total tests | 52 |
| Test files | 5 |
| Source modules covered | `dag_core`, `dag_induction`, `dag_orchestrator`, `dag_validator`, `state_doc`, `agent_pool` |
| Benchmark shapes | 4 (serial, parallel, fan, mixed) |
| External deps | None (pure Python, tempfile-based) |
| Test framework | Self-discovering (`__main__` runner, no pytest required) |

---

## Test Suite Structure

```
tests/
├── test_dag_core.py       # 17 tests — scheduling, leveling, cycles, induction
├── test_resume.py         #  8 tests — resume from state doc scenarios
├── test_validator.py      #  9 tests — manifest vs state consistency checks
├── test_failure_modes.py  # 12 tests — failure injection, retry, abort logic
└── test_benchmarks.py     #  6 tests — benchmark shape generation and validation

benchmarks/
└── bench_dag.py           # Benchmark harness: 4 shape generators + runner + printer
```

Each test file is **self-contained** — they all share the same pattern:

1. `sys.path.insert(0, ...)` adds the project root to the module search path
2. Test functions are standalone (no class hierarchy)
3. A `__main__` block auto-discovers all functions starting with `test_` and runs them with pass/fail reporting

There is no `conftest.py` or `pytest.ini` — the suite is designed to run without pytest, though pytest works too.

---

## How to Run Tests

### Run all tests (no pytest needed)

```bash
cd /home/ubuntu/github/bmad-dag-automator
python tests/test_dag_core.py
python tests/test_resume.py
python tests/test_validator.py
python tests/test_failure_modes.py
python tests/test_benchmarks.py
```

Each file prints a pass/fail summary:

```
  ✅ test_basic_dag
  ✅ test_parallel_dag
  ...
  17 passed, 0 failed
```

Exit code is `0` if all pass, `1` if any fail.

### Run all tests via a single script

```bash
for f in tests/test_*.py; do echo "=== $f ===" && python "$f"; done
```

### Run with pytest (if installed)

```bash
cd /home/ubuntu/github/bmad-dag-automator
python -m pytest tests/ -v
```

Note: The `__name__ == "__main__"` blocks are protected — they only run when the file is executed directly, so pytest imports them cleanly.

### Run benchmarks

```bash
python benchmarks/bench_dag.py
```

Output example:

```
  DAG Scheduling Benchmarks
  ========================================================================

  Shape                  Nodes  Lvls  Width    Sched   Serial   Par  Speed   Util
  ────────────────────   ─────  ────  ─────   ───────  ───────  ────  ─────  ─────
  Serial Chain              10    10      1   0.02ms     10      1   10.0x   100%
  Full Parallel             10     1     10   0.01ms     10     10    1.0x   100%
  Fan-out/fan-in             7     3      5   0.01ms      7      5    1.4x   100%
  Mixed                      8     4      2   0.01ms      8      2    4.0x   100%

  ──────────────────────────────────────────────────────────────────────────────
  Scheduling overhead: 0.05ms total (35 nodes across 4 shapes)
```

---

## Test File Reference

### test_dag_core.py — Core Algorithms (17 tests)

**Source module tested:** `dag_core` (DagGraph, DagNode, GraphStatus, InductionMode), `dag_induction` (DagInductor)

**Test Coverage:**

| # | Test | What it verifies |
|---|------|------------------|
| 1 | `test_basic_dag` | Serial chain A→B→C: 3 levels, critical path [A,B,C], max_width=1 |
| 2 | `test_parallel_dag` | 3 independent nodes: 1 level, width=3, max_width=3 |
| 3 | `test_fan_out` | A→B, A→C: 2 levels, level 1 width=2, max_width=2 |
| 4 | `test_fan_in` | A→C, B→C: 2 levels, level 0 width=2 |
| 5 | `test_complex_dag` | 8-node auth-system shape: 4 levels, max_width=3, correct critical path |
| 6 | `test_cycle_detection` | A→B→C→A: `has_cycle=True`, status=`aborted`, error contains "cycle" |
| 7 | `test_dangling_ref` | A→Z (Z missing): status=`aborted`, error contains "dangling" |
| 8 | `test_induction_apply_automatic` | AUTOMATIC mode: LLM edges applied immediately as `implicit_deps` |
| 9 | `test_induction_apply_assisted` | ASSISTED mode: LLM edges go to `suggested_deps`, not `implicit_deps` |
| 10 | `test_induction_promote_reject` | Promote moves from suggested→implicit; Reject removes both |
| 11 | `test_induction_minimal_skips_llm` | MINIMAL mode: `get_llm_context()` returns empty string |
| 12 | `test_from_story_list_roundtrip` | `from_story_list()` → schedule → `to_dict()`: 3 nodes, 3 levels |
| 13 | `test_critical_path_alternative` | Two equal-length paths: critical path picks one, length=3 |
| 14 | `test_edge_case_single_node` | 1 node: 1 level, width=1, critical_path=[only] |
| 15 | `test_edge_case_no_nodes` | Empty graph: 0 levels, empty critical path |
| 16 | `test_edge_case_self_dep` | A→A: `has_cycle=True` |
| 17 | `test_elastic_agent_allocation` | 10 parallel nodes: pool_size = min(max_agents=4, width=10) = 4 |

**Key assertions pattern:**

```python
# Typical schedule-and-verify pattern
graph = DagGraph()
graph.add_node(DagNode(id="A", title="Story A"))
graph.add_node(DagNode(id="B", title="Story B", explicit_deps=["A"]))
graph.schedule()

assert graph.status.value == "validated"
assert len(graph.levels) == 2
assert graph.levels[0].node_ids == ["A"]
assert graph.to_dict()["dag"]["max_width"] == 1
```

---

### test_resume.py — Resume Flow (8 tests)

**Source module tested:** `dag_orchestrator` (DagOrchestrator), `state_doc` (DagStateDoc, DagRunStatus)

**Helper functions (shared setup):**

- `_make_simple_graph(tmpdir)` — builds a 3-level DAG with 5 nodes (A,B,C,D,E)
- `_write_manifest(path, graph)` — writes `dag-manifest.yaml` from `graph.to_yaml()`
- `_write_state_doc(path, completed_levels, total_levels, status)` — writes a partial `orchestration.md` with simulated prior-run state

**Test Coverage:**

| # | Test | Scenario | Expected behaviour |
|---|------|----------|-------------------|
| 1 | `test_resume_from_level_2` | Prior run completed levels 0-1 | `_find_resume_point` returns `2` |
| 2 | `test_resume_from_paused` | State doc shows PAUSED at level 1 | Returns `1` |
| 3 | `test_resume_from_complete` | Prior run already COMPLETE | Returns `None` (skip) |
| 4 | `test_resume_changed_manifest` | Prior manifest had 5 nodes, current has 3 | `ValueError` with "Story count mismatch" |
| 5 | `test_resume_no_prior_run` | No state doc exists | `FileNotFoundError` with "State doc not found" |
| 6 | `test_resume_level_skipping` | Resume from level 1 via skip logic | `executed_levels == [1, 2]` |
| 7 | `test_state_doc_load_roundtrip` | Save then load a PAUSED state doc | All fields round-trip correctly |
| 8 | `test_state_doc_mark_resumed` | Call `mark_resumed()` on PAUSED doc | Status → RUNNING, "RESUMED" logged |

**Key assertions pattern:**

```python
# Resume-from-level test
resume_level = orch._find_resume_point(state_path, manifest_path)
assert resume_level == 2, f"Expected level 2, got {resume_level}"

# Completed-run test  
resume_level = orch._find_resume_point(state_path, manifest_path)
assert resume_level is None, f"Expected None, got {resume_level}"

# Manifest mismatch test
raised = False
try:
    orch._find_resume_point(state_path, manifest_path)
except ValueError as e:
    raised = True
    assert "Story count mismatch" in str(e)
assert raised, "Expected ValueError"
```

---

### test_validator.py — DAG Consistency Checks (9 tests)

**Source module tested:** `dag_validator` (DagValidator)

**Helper functions:**

- `_make_test_graph()` — same 5-node, 3-level DAG used across resume tests
- `_write_manifest(path, graph, extra_nodes, missing_nodes)` — writes YAML manifest with optional corruption
- `_write_state_doc(path, completed_count, extra_nodes)` — writes state doc with optional ghost nodes

**Validator checks tested:**

| Check method | What it validates |
|---|---|
| `validate_manifest_vs_state()` | Manifest node count matches state doc completed count |
| `validate_orphaned_nodes()` | All completed nodes in state doc exist in manifest |
| `validate_node_existence()` | All nodes referenced in manifest levels resolve to node definitions |
| `validate_level_boundaries()` | Level boundaries are consistent (no gaps, no partial levels) |

**Test Coverage:**

| # | Test | What it verifies |
|---|------|------------------|
| 1 | `test_manifest_matches_state` | 5 nodes in manifest, 5 completed → status="pass" |
| 2 | `test_manifest_mismatch` | 5 nodes in manifest, 6 completed → status="fail" |
| 3 | `test_no_orphaned_nodes` | All completed nodes exist in manifest → pass |
| 4 | `test_orphaned_nodes_detected` | State doc has "GHOST" node not in manifest → fail, "GHOST" in errors |
| 5 | `test_all_nodes_exist` | All manifest level nodes resolve → pass |
| 6 | `test_level_boundaries_complete` | All upstream levels completed → pass |
| 7 | `test_level_boundaries_partial` | Only level 0 complete → pass (partial is valid for resume) |
| 8 | `test_missing_manifest` | No manifest file → fail on node existence check |
| 9 | `test_full_clean_report` | All 4 checks pass → verdict="PASS", exit_code=0, checks count=4 |

**Key assertions pattern:**

```python
result = v.validate_manifest_vs_state(manifest_path, state_path)
assert result["status"] == "pass", f"Expected pass, got {result['status']}"

report = v.validate_all(manifest_path, state_path)
assert report["verdict"] == "PASS"
assert report["exit_code"] == 0
assert len(report["checks"]) == 4
```

---

### test_failure_modes.py — Failure Injection (12 tests)

**Source module tested:** `dag_orchestrator` (DagOrchestrator), `agent_pool` (AgentPool), `state_doc` (DagStateDoc, DagRunStatus)

**Helper functions:**

- `_make_graph(shape)` — builds graphs in 3 shapes: `"serial"` (A→B→C), `"parallel"` (A,B,C independent), `"fan"` (A→B, A→C, B+C→D)
- `_simulate_level_complete(orch, level_idx, failed_node_ids)` — simulates agent completion with selective failures, updates state doc

**Test Coverage:**

| # | Test | What it verifies |
|---|------|------------------|
| 1 | `test_single_node_retry` | Node B fails in serial A→B→C: 1 failure recorded, state doc saved |
| 2 | `test_multi_node_failure_exhausted` | All 3 parallel nodes fail: 3 failures recorded |
| 3 | `test_downstream_blocking` | A→B, A→C: A fails → downstream = [B, C] |
| 4 | `test_level_wide_failure_abort_detection` | A fails in serial A→B→C: level-wide failure, 0 completed |
| 5 | `test_empty_story_list` | Empty DagGraph → 0 levels, manifest passes validation |
| 6 | `test_self_dep_cycle_detection` | A→A: has_cycle=True, status=ABORTED |
| 7 | `test_single_node_happy_path` | Single node → 1 level, status=VALIDATED |
| 8 | `test_failure_recorded_in_state_doc` | A fails → reload state doc → 1 failure persisted |
| 9 | `test_deep_dag_50_levels` | 52-node serial chain: 52 levels, critical path length=52 |
| 10 | `test_empty_story_list_orchestrator` | Orchestrator with 0 nodes → result["status"]="complete" |
| 11 | `test_single_story_sprint` | 1 node completes: 1 completed node in state |
| 12 | `test_tmux_unavailable_handling` | Mock `subprocess.run` → `FileNotFoundError` → AgentStatus.FAILED with "tmux" in error |

**Key assertions pattern:**

```python
# Failure injection
_simulate_level_complete(orch, 0, set())        # Level 0 all succeed
_simulate_level_complete(orch, 1, {"B"})        # Level 1: B fails

assert len(orch.state.failed_nodes) == 1
assert orch.state.failed_nodes[0]["id"] == "B"

# State doc persistence
loaded = DagStateDoc.load(state_path)
assert len(loaded.failed_nodes) == 1

# Mock-based failure
def mock_run(*args, **kwargs):
    raise FileNotFoundError("tmux not found")
subprocess.run = mock_run

result = p.spawn_node(...)
assert result.status == pool.AgentStatus.FAILED
assert "tmux" in (result.error or "").lower()
```

---

### test_benchmarks.py — Benchmark Harness (6 tests)

**Source module tested:** `benchmarks.bench_dag` (all shape functions + runner)

**Test Coverage:**

| # | Test | What it verifies |
|---|------|------------------|
| 1 | `test_serial_chain_shape` | `serial_chain(10)` → 10 levels, max width=1, 10 nodes |
| 2 | `test_full_parallel_shape` | `full_parallel(10)` → 1 level, width=10 |
| 3 | `test_fan_out_fan_in_shape` | `fan_out_fan_in(5)` → 3 levels, max width=5 |
| 4 | `test_mixed_shape` | `mixed_shape()` → 8 nodes |
| 5 | `test_benchmark_runs_all_shapes` | `run_benchmark()` returns 4 results, all valid stats |
| 6 | `test_serial_speedup_gt_1` | Serial speedup ≥ 9.0x (10/1), Parallel speedup = 1.0x (10/10) |

**Key assertions pattern:**

```python
graph = serial_chain(10)
graph.schedule()
assert len(graph.levels) == 10
assert max(l.width for l in graph.levels) == 1

results = run_benchmark()
assert len(results) == 4
for r in results:
    assert r["nodes"] > 0
    assert r["speedup"] > 0

serial_result = [r for r in results if r["shape"] == "Serial Chain"][0]
assert serial_result["speedup"] >= 9.0
```

---

## Test Patterns & How to Write New Tests

The test suite follows consistent, testable patterns. Here's how to add new tests.

### Pattern 1: DAG Schedule-Then-Verify

Use for core scheduling, leveling, and cycle detection tests.

```python
def test_my_new_shape():
    """Docstring describing the graph shape and expected result."""
    graph = DagGraph()
    
    # Add nodes with explicit dependencies
    graph.add_node(DagNode(id="A", title="Root"))
    graph.add_node(DagNode(id="B", title="Child", explicit_deps=["A"]))
    
    # Run topological sort + level assignment
    graph.schedule()
    
    # Assert structural properties
    assert graph.status.value == "validated"
    assert not graph.has_cycle
    assert len(graph.levels) == 2
    assert graph.levels[0].node_ids == ["A"]
    assert graph.critical_path == ["A", "B"]
    assert graph.to_dict()["dag"]["max_width"] == 1
```

### Pattern 2: Induction Mode Tests

Use for LLM edge injection and manual promote/reject flow.

```python
def test_my_induction_case():
    """Describe the induction mode behaviour."""
    graph = DagGraph(mode=InductionMode.AUTOMATIC)  # or ASSISTED, MINIMAL
    graph.add_node(DagNode(id="A", title="Model", interfaces_provides=["User"]))
    graph.add_node(DagNode(id="B", title="API", consumes_interfaces=["User"]))
    
    inductor = DagInductor(graph)
    
    llm_output = json.dumps({
        "edges": [
            {"from": "B", "to": "A", "reasoning": "...", "confidence": "high"}
        ]
    })
    
    applied = inductor.apply_llm_edges(llm_output)
    assert len(applied) == 1
    
    # Check mode-specific behaviour
    if graph.mode == InductionMode.AUTOMATIC:
        assert "A" in graph.nodes["B"].implicit_deps
    else:
        assert "A" in graph.nodes["B"].suggested_deps
```

### Pattern 3: Tempfile-Based State & File Tests

Use for resume, validation, and persistence tests. Always use `tempfile.TemporaryDirectory()` for isolation.

```python
def test_my_state_operation():
    """Describe the state doc or file-based operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up paths
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")
        
        # Build and write test fixtures
        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        
        # Create orchestrator/validator
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        
        # Execute and assert
        result = orch._find_resume_point(state_path, manifest_path)
        assert result == expected_value
```

### Pattern 4: Failure Injection

Use for orchestrator failure handling tests.

```python
def test_my_failure_scenario():
    """Describe the failure scenario and expected handling."""
    graph = _make_graph("serial")  # or "parallel" or "fan"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)
        
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        orch.state = DagStateDoc.from_manifest(graph.to_dict(), output_dir=output_dir)
        
        # Simulate level completion with failures
        _simulate_level_complete(orch, 0, {"A"})  # A fails
        
        # Assertions
        assert len(orch.state.failed_nodes) == 1
        assert orch.state.failed_nodes[0]["id"] == "A"
```

### Pattern 5: Mock-Based Failure Tests

Use for testing external system failures (tmux, git, etc.).

```python
def test_my_external_failure():
    """Describe the external dependency failure."""
    pool = AgentPool(project_root="/tmp", max_concurrent=1, dry_run=False)
    
    import subprocess
    original = subprocess.run
    
    def mock_fail(*args, **kwargs):
        raise FileNotFoundError("some external tool not found")
    
    subprocess.run = mock_fail
    try:
        result = pool.spawn_node(...)
        assert result.status == AgentStatus.FAILED
        assert "not found" in (result.error or "").lower()
    finally:
        subprocess.run = original  # Always restore
```

### Pattern 6: Benchmark Validation Tests

```python
def test_my_benchmark_shape():
    """Verify a benchmark shape generator produces expected structure."""
    graph = fan_out_fan_in(3)  # parameterized shape
    graph.schedule()
    assert len(graph.levels) == 3
    assert graph.levels[1].width == 3  # n_fan value
```

---

## Edge Case Coverage Summary

The suite specifically targets these edge cases:

| Edge case | Files covering it |
|---|---|
| **Empty graph** (0 nodes) | `test_dag_core` (#15), `test_failure_modes` (#5, #10) |
| **Single node** | `test_dag_core` (#14), `test_failure_modes` (#7, #11) |
| **Self-referencing dependency** | `test_dag_core` (#16), `test_failure_modes` (#6) |
| **Dangling reference** (node depends on missing node) | `test_dag_core` (#7) |
| **Cycle detection** (3-node cycle + self-cycle) | `test_dag_core` (#6, #16), `test_failure_modes` (#6) |
| **Deep DAG** (52-level serial chain) | `test_failure_modes` (#9) |
| **Max-width computation** (flat, fan, mixed) | `test_dag_core` (#1-5) |
| **All-nodes-fail level** | `test_failure_modes` (#2, #4) |
| **Partial failure with downstream** | `test_failure_modes` (#1, #3) |
| **Resume from every level** (0, 1, 2, complete) | `test_resume` (#1-3, #6) |
| **Manifest/story-count change across resume** | `test_resume` (#4) |
| **Missing state doc** (first run) | `test_resume` (#5) |
| **Missing manifest file** | `test_validator` (#8) |
| **Orphaned nodes in state** (ghost nodes) | `test_validator` (#4) |
| **Mismatched completed count** | `test_validator` (#2) |
| **External tool unavailable** (tmux) | `test_failure_modes` (#12) |

---

## Failure Injection Tests Deep Dive

The failure injection tests (`test_failure_modes.py`) simulate **real orchestrator failure paths without spawning actual processes**. The key abstraction is `_simulate_level_complete()`:

```python
def _simulate_level_complete(orch, level_idx, failed_node_ids):
    """Builds AgentResult-like dicts and feeds them through the 
    orchestrator's level completion path."""
    level = orch.graph.levels[level_idx]
    level_nodes = [orch.graph.nodes[nid] for nid in level.node_ids]
    
    results = []
    for node in level_nodes:
        failed = node.id in failed_node_ids
        results.append({
            "id": node.id,
            "status": "failed" if failed else "completed",
            "session_id": f"dry-{node.id}",
            "duration_s": 0.1,
            "error": f"Simulated failure for {node.id}" if failed else None,
        })
    
    orch._level_results[level_idx] = results
    orch.state.record_level_complete(level_idx, results)
    orch.state.save(...)
```

**What's tested via failure injection:**

1. **Single node failure** — verifies failed_nodes list, state doc persistence, downstream node tracking
2. **Multi-node exhaustion** — all nodes in a level fail, verifies count and IDs
3. **Downstream blocking** — root failure correctly identifies all dependents
4. **Level-wide abort signal** — all nodes in a level fail → level-wide abort is detectable
5. **State doc round-trip** — failures persist in the state doc and survive load/save
6. **Mock external failure** — `subprocess.run` replaced to simulate tmux not being installed

---

## Benchmark Harness

The benchmark harness lives at `benchmarks/bench_dag.py` and provides:

### Shape Generators

| Function | Parameters | Structure | Nodes | Levels |
|---|---|---|---|---|
| `serial_chain(n)` | `n` (default 10) | N0→N1→...→N{n-1} | n | n |
| `full_parallel(n)` | `n` (default 10) | All independent | n | 1 |
| `fan_out_fan_in(n_fan)` | `n_fan` (default 5) | root → n children → leaf | n_fan + 2 | 3 |
| `mixed_shape()` | none | 8 nodes, 4 levels, varying widths | 8 | 4 |

### Runner & Reporter

```python
run_benchmark() -> list[dict]
```

Returns a list of dicts, each containing:

| Field | Description |
|---|---|
| `shape` | Name of the shape |
| `nodes` | Node count |
| `levels` | Level count |
| `max_width` | Maximum level width |
| `sched_ms` | Scheduling time in milliseconds |
| `serial_units` | Abstract serial time (= node count) |
| `parallel_units` | Abstract parallel time (= max_width) |
| `speedup` | Theoretical speedup = nodes / max_width |
| `utilisation_pct` | Agent utilisation percentage |

### Writing New Benchmarks

Add a new entry to the `SHAPES` list:

```python
def my_custom_shape(n: int = 6) -> DagGraph:
    """Describe the shape."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    # ... add nodes ...
    return graph

SHAPES.append(("My Shape", my_custom_shape, {"n": 6}))
```

The `run_benchmark()` and `print_results()` functions will automatically pick it up.

### Benchmark Assertion Pattern in Tests

```python
def test_my_shape_speedup():
    results = run_benchmark()
    my_result = [r for r in results if r["shape"] == "My Shape"][0]
    assert my_result["nodes"] > 0
    assert my_result["speedup"] == expected_value
```

---

## Continuous Integration Notes

The test suite is designed for CI compatibility:

- **No network required** — all tests are self-contained
- **No external binaries** — pure Python, tempfile-based
- **Deterministic** — same inputs always produce same results
- **Fast** — all 52 tests complete in under 2 seconds
- **Isolated** — each test uses `tempfile.TemporaryDirectory()`; no shared state
- **Self-discovering** — the `__main__` runner finds all `test_*` functions automatically

To add a new test file, follow the existing pattern:

```python
#!/usr/bin/env python3
"""Description of what this test file covers."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from module_under_test import Thing

def test_my_thing():
    """Docstring."""
    # ... test body ...

if __name__ == "__main__":
    test_functions = [name for name in dir() if name.startswith("test_")]
    passed = 0
    failed = 0
    for name in sorted(test_functions):
        try:
            globals()[name]()
            print(f"  ✅ {name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
```
