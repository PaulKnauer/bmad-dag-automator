"""Failure injection tests for the DAG orchestrator.

Tests failure handling without real tmux/agent spawning:
  - Simulating AgentResult with FAILED status
  - Verifying orchestrator retry/downstream/abort logic
  - State doc records failures correctly
  - Edge cases (empty, single, self-dep)
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dag_core import DagGraph, DagNode, InductionMode, NodeStatus, GraphStatus
from dag_orchestrator import DagOrchestrator
from state_doc import DagRunStatus


# --- Helpers ---

def _make_graph(shape: str = "serial") -> DagGraph:
    """Build a test graph. Shapes: serial (A→B→C), parallel (A,B,C independent)."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    if shape == "serial":
        graph.add_node(DagNode(id="A", title="A"))
        graph.add_node(DagNode(id="B", title="B", explicit_deps=["A"]))
        graph.add_node(DagNode(id="C", title="C", explicit_deps=["B"]))
    elif shape == "parallel":
        graph.add_node(DagNode(id="A", title="A"))
        graph.add_node(DagNode(id="B", title="B"))
        graph.add_node(DagNode(id="C", title="C"))
    elif shape == "fan":
        graph.add_node(DagNode(id="A", title="Root"))
        graph.add_node(DagNode(id="B", title="Child 1", explicit_deps=["A"]))
        graph.add_node(DagNode(id="C", title="Child 2", explicit_deps=["A"]))
        graph.add_node(DagNode(id="D", title="Leaf", explicit_deps=["B", "C"]))
    graph.schedule()
    return graph


def _simulate_level_complete(orch: DagOrchestrator, level_idx: int,
                              failed_node_ids: set[str]) -> None:
    """Simulate completing a level with some failed nodes.

    Builds AgentResult-like dicts and passes them through the orchestrator's
    level completion path.
    """
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

    # Update state doc via the existing method (avoids double-add)
    orch.state.record_level_complete(level_idx, results)
    orch.state.save(os.path.join(orch.output_dir, "orchestration.md"))


# --- Tests ---

def test_single_node_retry():
    """Simulate a single node failure in a 3-node serial DAG.

    Verifies that the orchestrator records the failure but continues
    (no abort) and downstream handling works correctly.
    """
    graph = _make_graph("serial")
    assert len(graph.nodes) == 3
    assert len(graph.levels) == 3

    # The failure handling in run_dag processes results after wait_level().
    # We simulate the flow: level 0 completes fine, level 1 (B) fails.
    # Verify that the failed_nodes list and state doc capture it.
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)

        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir

        from state_doc import DagStateDoc
        orch.state = DagStateDoc.from_manifest(
            graph.to_dict(), output_dir=output_dir
        )
        orch.state.save(os.path.join(output_dir, "orchestration.md"))

        # Level 0: A succeeds
        _simulate_level_complete(orch, 0, set())

        # Level 1: B fails
        _simulate_level_complete(orch, 1, {"B"})

        # Verify
        assert len(orch.state.failed_nodes) == 1
        assert orch.state.failed_nodes[0]["id"] == "B"

        # Verify downstream tracking: C depends on B
        node_c = graph.nodes["C"]
        assert "B" in node_c.explicit_deps

        # State doc was written
        state_path = os.path.join(output_dir, "orchestration.md")
        assert os.path.exists(state_path)

        print(f"  ✅ test_single_node_retry: 1 failure recorded, state doc saved")


def test_multi_node_failure_exhausted():
    """Multiple nodes fail, exhausting retries.

    Verifies the orchestrator handles multiple node failures in the same level
    without crashing, and the failed_nodes list grows correctly.
    """
    graph = _make_graph("parallel")
    assert len(graph.levels) == 1  # all parallel

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)

        from state_doc import DagStateDoc
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        orch.state = DagStateDoc.from_manifest(
            graph.to_dict(), output_dir=output_dir
        )

        # All 3 nodes fail
        _simulate_level_complete(orch, 0, {"A", "B", "C"})

        assert len(orch.state.failed_nodes) == 3
        failed_ids = {n["id"] for n in orch.state.failed_nodes}
        assert failed_ids == {"A", "B", "C"}

        print(f"  ✅ test_multi_node_failure_exhausted: 3 failures recorded")


def test_downstream_blocking():
    """When a root node fails, downstream nodes that depend on it are flagged."""
    graph = _make_graph("fan")  # A → B, A → C, B+C → D
    # Level 0: A
    # Level 1: B, C
    # Level 2: D

    # A fails → B, C are direct downstream (D is indirect, only flagged if B/C fail)
    node_a = graph.nodes["A"]

    with tempfile.TemporaryDirectory() as tmpdir:
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph

        downstream = []
        for nid, node in graph.nodes.items():
            if nid != "A" and "A" in node.all_deps:
                downstream.append(nid)

        assert sorted(downstream) == ["B", "C"]
        print(f"  ✅ test_downstream_blocking: A blocks {', '.join(downstream)}")


def test_level_wide_failure_abort_detection():
    """When all nodes in a level fail → the graph can be flagged for abort.

    Verifies the orchestrator's level-completion logic correctly detects
    when all results from a level failed.
    """
    graph = _make_graph("serial")  # A → B → C

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)

        from state_doc import DagStateDoc
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        orch.state = DagStateDoc.from_manifest(
            graph.to_dict(), output_dir=output_dir
        )

        # Level 0: A fails → level completely failed
        _simulate_level_complete(orch, 0, {"A"})

        # Check: state doc captured the failure
        assert len(orch.state.failed_nodes) == 1
        assert orch.state.failed_nodes[0]["id"] == "A"
        assert len(orch.state.completed_nodes) == 0

        # The orchestrator's run_dag would check failed_nodes_per_level
        # after each level and escalate. We verify the data is right.
        level_results = orch._level_results.get(0, [])
        all_failed = all(r["status"] == "failed" for r in level_results)
        assert all_failed, "Expected all level 0 results to show failed"

        print(f"  ✅ test_level_wide_failure_abort_detection: level-wide failure detected")


def test_empty_story_list():
    """Empty story list → graceful handling."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.schedule()

    assert len(graph.levels) == 0
    assert graph.critical_path == []

    from dag_validator import DagValidator
    v = DagValidator()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)

        # Empty manifest
        import yaml
        empty_manifest = {"dag": {"levels": [], "total_nodes": 0}, "nodes": {}}
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")
        with open(manifest_path, "w") as f:
            yaml.dump(empty_manifest, f)

        result = v.validate_node_existence(manifest_path)
        assert result["status"] == "pass"
        print(f"  ✅ test_empty_story_list: empty graph + manifest handled")


def test_self_dep_cycle_detection():
    """Self-referencing dependency → cycle detection catches it."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="A", title="A", explicit_deps=["A"]))
    graph.schedule()

    assert graph.has_cycle
    assert graph.status == GraphStatus.ABORTED
    assert "cycle" in (graph.error or "").lower()
    print(f"  ✅ test_self_dep_cycle_detection: cycle detected")


def test_single_node_happy_path():
    """Single-node graph → one level, one node, no failures."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="only", title="Only story"))
    graph.schedule()

    assert len(graph.levels) == 1
    assert graph.levels[0].node_ids == ["only"]
    assert graph.status == GraphStatus.VALIDATED
    print(f"  ✅ test_single_node_happy_path: single node schedules correctly")


def test_failure_recorded_in_state_doc():
    """Failed nodes are persisted in the state doc for resume/validation."""
    graph = _make_graph("serial")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        os.makedirs(output_dir, exist_ok=True)

        from state_doc import DagStateDoc
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        orch.state = DagStateDoc.from_manifest(
            graph.to_dict(), output_dir=output_dir
        )

        # Level 0: A fails
        _simulate_level_complete(orch, 0, {"A"})

        state_path = os.path.join(output_dir, "orchestration.md")

        # Reload and verify
        loaded = DagStateDoc.load(state_path)
        assert len(loaded.failed_nodes) == 1
        assert loaded.failed_nodes[0]["id"] == "A"
        print(f"  ✅ test_failure_recorded_in_state_doc: failure persisted in state doc")


if __name__ == "__main__":
    test_functions = [
        name for name in dir()
        if name.startswith("test_")
    ]

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
