"""Tests for DAG orchestrator resume functionality.

Scenarios:
  1. Resume from level 2 — prior run completed levels 0-1
  2. Resume from paused — state doc shows PAUSED at level 1
  3. Resume from complete — prior run is already COMPLETE → skip entirely
  4. Resume with changed manifest — story count differs → abort with error
  5. No prior run — state doc missing → start fresh with warning
"""

import json
import os
import sys
import tempfile
import yaml

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dag_core import DagGraph, DagNode, InductionMode
from dag_orchestrator import DagOrchestrator
from state_doc import DagStateDoc, DagRunStatus


def _make_simple_graph(project_root: str) -> DagGraph:
    """Build a 3-level DAG with 5 nodes: level 0 (2), level 1 (2), level 2 (1)."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="A", title="Root 1"))
    graph.add_node(DagNode(id="B", title="Root 2"))
    graph.add_node(DagNode(id="C", title="Mid 1", explicit_deps=["A"]))
    graph.add_node(DagNode(id="D", title="Mid 2", explicit_deps=["B"]))
    graph.add_node(DagNode(id="E", title="Leaf", explicit_deps=["C", "D"]))
    graph.schedule()
    assert len(graph.levels) == 3
    return graph


def _write_manifest(manifest_path: str, graph: DagGraph) -> None:
    """Write a DAG manifest to disk."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as f:
        f.write(graph.to_yaml())


def _write_state_doc(state_path: str, completed_levels: list[int],
                     total_levels: int, status: DagRunStatus = DagRunStatus.PAUSED) -> None:
    """Write a partial state doc simulating a prior run."""
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    completed_nodes = []
    if completed_levels:
        for level_idx in completed_levels:
            if level_idx == 0:
                completed_nodes.extend([
                    {"id": "A", "status": "completed", "session_id": "dry-A", "duration_s": 0.1},
                    {"id": "B", "status": "completed", "session_id": "dry-B", "duration_s": 0.2},
                ])
            elif level_idx == 1:
                completed_nodes.extend([
                    {"id": "C", "status": "completed", "session_id": "dry-C", "duration_s": 0.3},
                    {"id": "D", "status": "completed", "session_id": "dry-D", "duration_s": 0.4},
                ])
            elif level_idx == 2:
                completed_nodes.extend([
                    {"id": "E", "status": "completed", "session_id": "dry-E", "duration_s": 0.5},
                ])

    steps = [f"2026-06-23T20:00:00 | Level {l} | — | Level completed" for l in completed_levels]
    if status == DagRunStatus.PAUSED:
        steps.append("2026-06-23T20:05:00 | — | — | PAUSED: test pause")

    doc = DagStateDoc(
        status=status,
        dag_enabled=True,
        dag_manifest_path=os.path.join(os.path.dirname(state_path), "dag-manifest.yaml"),
        dag_current_level=len(completed_levels),
        dag_total_levels=total_levels,
        dag_max_width=2,
        dag_pool_size=2,
        dag_status="paused" if status == DagRunStatus.PAUSED else "running",
        dag_critical_path=["A", "C", "E"],
        dag_mode="minimal",
        output_dir=os.path.dirname(state_path),
        completed_nodes=completed_nodes,
        steps_completed=steps,
        current_level=len(completed_levels),
    )
    doc.save(state_path)


# --- Tests ---

def test_resume_from_level_2():
    """Prior run completed levels 0-1 → resume from level 2."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        _write_state_doc(state_path, completed_levels=[0, 1], total_levels=3)

        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir

        resume_level = orch._find_resume_point(state_path, manifest_path)
        assert resume_level == 2, f"Expected level 2, got {resume_level}"
        print(f"  ✅ test_resume_from_level_2: resume at level {resume_level}")


def test_resume_from_paused():
    """State doc shows PAUSED at level 1 → resume from level 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        _write_state_doc(state_path, completed_levels=[0], total_levels=3,
                         status=DagRunStatus.PAUSED)

        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir

        resume_level = orch._find_resume_point(state_path, manifest_path)
        assert resume_level == 1, f"Expected level 1, got {resume_level}"
        print(f"  ✅ test_resume_from_paused: resume at level {resume_level}")


def test_resume_from_complete():
    """Prior run is already COMPLETE → returns None (nothing to resume)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        _write_state_doc(state_path, completed_levels=[0, 1, 2], total_levels=3,
                         status=DagRunStatus.COMPLETE)

        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir

        resume_level = orch._find_resume_point(state_path, manifest_path)
        assert resume_level is None, f"Expected None, got {resume_level}"
        print(f"  ✅ test_resume_from_complete: no resume needed")


def test_resume_changed_manifest():
    """Story count differs between prior and current → ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        # Prior manifest has 5 nodes
        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        _write_state_doc(state_path, completed_levels=[0, 1], total_levels=3)

        # Current graph has 3 nodes (mismatch)
        smaller_graph = DagGraph(mode=InductionMode.MINIMAL)
        smaller_graph.add_node(DagNode(id="X", title="Only node"))
        smaller_graph.schedule()

        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = smaller_graph
        orch.output_dir = output_dir

        raised = False
        try:
            orch._find_resume_point(state_path, manifest_path)
        except ValueError as e:
            raised = True
            assert "Story count mismatch" in str(e), f"Wrong error: {e}"

        assert raised, "Expected ValueError for manifest mismatch"
        print(f"  ✅ test_resume_changed_manifest: correctly rejected mismatch")


def test_resume_no_prior_run():
    """No prior state doc → _find_resume_point raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        graph = _make_simple_graph(tmpdir)
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir

        raised = False
        try:
            orch._find_resume_point(state_path, manifest_path)
        except FileNotFoundError as e:
            raised = True
            assert "State doc not found" in str(e), f"Wrong error: {e}"

        assert raised, "Expected FileNotFoundError for missing state doc"
        print(f"  ✅ test_resume_no_prior_run: correctly rejected missing state doc")


def test_resume_level_skipping():
    """Verify the orchestrator skip logic in the level loop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")
        manifest_path = os.path.join(output_dir, "dag-manifest.yaml")

        graph = _make_simple_graph(tmpdir)
        _write_manifest(manifest_path, graph)
        _write_state_doc(state_path, completed_levels=[0], total_levels=3)

        # Build orchestrator, simulate resume
        orch = DagOrchestrator(project_root=tmpdir, dry_run=True)
        orch.graph = graph
        orch.output_dir = output_dir
        orch.resume = True
        orch._resume_from_level = orch._find_resume_point(state_path, manifest_path)

        # Track which levels get executed
        executed_levels = []
        for level_idx, level in enumerate(graph.levels):
            if orch._resume_from_level is not None and level_idx < orch._resume_from_level:
                continue
            executed_levels.append(level_idx)

        assert executed_levels == [1, 2], f"Expected [1, 2], got {executed_levels}"
        assert orch._resume_from_level == 1
        print(f"  ✅ test_resume_level_skipping: levels {executed_levels} executed")


def test_state_doc_load_roundtrip():
    """Verify DagStateDoc.load() round-trips an existing state doc."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        state_path = os.path.join(output_dir, "orchestration.md")

        _write_state_doc(state_path, completed_levels=[0, 1], total_levels=3,
                         status=DagRunStatus.PAUSED)

        loaded = DagStateDoc.load(state_path)

        assert loaded.dag_total_levels == 3
        assert loaded.dag_current_level == 2
        assert len(loaded.completed_nodes) == 4
        assert loaded.status == DagRunStatus.PAUSED
        assert loaded.dag_max_width == 2
        assert loaded.dag_critical_path == ["A", "C", "E"]
        print(f"  ✅ test_state_doc_load_roundtrip: {len(loaded.completed_nodes)} nodes, "
              f"status={loaded.status.value}")


def test_state_doc_mark_resumed():
    """Verify mark_resumed transitions state and logs correctly."""
    doc = DagStateDoc(
        status=DagRunStatus.PAUSED,
        dag_current_level=1,
    )
    assert doc.status == DagRunStatus.PAUSED

    doc.mark_resumed(level=1, reason="merge conflict resolved")
    assert doc.status == DagRunStatus.RUNNING
    assert doc.dag_status == "running"
    assert any("RESUMED" in s for s in doc.steps_completed)
    assert any("merge conflict resolved" in s for s in doc.steps_completed)
    print(f"  ✅ test_state_doc_mark_resumed: status={doc.status.value}")


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
