"""Tests for the DAG Validator — consistency checks.

Scenarios:
  1. Manifest matches state doc
  2. No orphaned nodes
  3. All nodes exist in manifest
  4. Level boundaries consistent
  5. Missing manifest handled gracefully
  6. Full clean run returns PASS verdict
"""

import os
import sys
import tempfile

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dag_core import DagGraph, DagNode, InductionMode
from dag_validator import DagValidator
from state_doc import DagRunStatus


def _make_test_graph() -> DagGraph:
    """3 levels: L0 (A,B), L1 (C,D), L2 (E)."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="A", title="Root 1"))
    graph.add_node(DagNode(id="B", title="Root 2"))
    graph.add_node(DagNode(id="C", title="Mid 1", explicit_deps=["A"]))
    graph.add_node(DagNode(id="D", title="Mid 2", explicit_deps=["B"]))
    graph.add_node(DagNode(id="E", title="Leaf", explicit_deps=["C", "D"]))
    graph.schedule()
    return graph


def _write_manifest(manifest_path: str, graph: DagGraph,
                    extra_nodes: list[str] | None = None,
                    missing_nodes: list[str] | None = None) -> None:
    """Write manifest, optionally with extra or missing nodes."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    manifest = graph.to_dict()

    if extra_nodes:
        for nid in extra_nodes:
            manifest["nodes"][nid] = {"id": nid, "title": nid}

    # Remove nodes that should be missing but referenced
    if missing_nodes:
        for nid in missing_nodes:
            manifest["nodes"].pop(nid, None)

    import yaml
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)


def _write_state_doc(state_path: str, completed_count: int,
                     extra_nodes: list[dict] | None = None) -> None:
    """Write a state doc with a given number of completed nodes."""
    import yaml
    from state_doc import DagStateDoc

    ids = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    completed = [
        {"id": ids[i], "status": "completed", "session_id": "dry", "duration_s": 0.1}
        for i in range(completed_count)
    ]
    if extra_nodes:
        completed.extend(extra_nodes)

    doc = DagStateDoc(
        status=DagRunStatus.RUNNING,
        dag_total_levels=3,
        completed_nodes=completed,
        output_dir=os.path.dirname(state_path),
    )
    doc.save(state_path)


# --- Tests ---

def test_manifest_matches_state():
    """Manifest has 5 nodes, state doc has 5 completed → pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 5)

        v = DagValidator()
        result = v.validate_manifest_vs_state(manifest_path, state_path)
        assert result["status"] == "pass", f"Expected pass, got {result['status']}"
        print(f"  ✅ test_manifest_matches_state" + "")


def test_manifest_mismatch():
    """State doc reports more completed than manifest nodes → fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        # Report 6 completed when manifest only has 5
        _write_state_doc(state_path, 6)

        v = DagValidator()
        result = v.validate_manifest_vs_state(manifest_path, state_path)
        assert result["status"] == "fail", f"Expected fail, got {result['status']}"
        print(f"  ✅ test_manifest_mismatch" + "")


def test_no_orphaned_nodes():
    """All completed nodes exist in manifest → pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 3)

        v = DagValidator()
        result = v.validate_orphaned_nodes(manifest_path, state_path)
        assert result["status"] == "pass", f"Expected pass, got {result['status']}"
        print(f"  ✅ test_no_orphaned_nodes" + "")


def test_orphaned_nodes_detected():
    """State doc has nodes not in manifest → fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 3, extra_nodes=[
            {"id": "GHOST", "status": "completed"}
        ])

        v = DagValidator()
        result = v.validate_orphaned_nodes(manifest_path, state_path)
        assert result["status"] == "fail", f"Expected fail, got {result['status']}"
        assert "GHOST" in str(result["errors"]), "GHOST should be in errors"
        print(f"  ✅ test_orphaned_nodes_detected" + "")


def test_all_nodes_exist():
    """All manifest level nodes resolve → pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")

        _write_manifest(manifest_path, _make_test_graph())

        v = DagValidator()
        result = v.validate_node_existence(manifest_path)
        assert result["status"] == "pass", f"Expected pass, got {result['status']}"
        print(f"  ✅ test_all_nodes_exist" + "")


def test_level_boundaries_complete():
    """All upstream levels completed → pass."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 5)

        v = DagValidator()
        result = v.validate_level_boundaries(manifest_path, state_path)
        assert result["status"] == "pass", f"Expected pass, got {result['status']}"
        print(f"  ✅ test_level_boundaries_complete" + "")


def test_level_boundaries_partial():
    """Only level 0 complete → pass for partial, no broken boundary."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 2)

        v = DagValidator()
        result = v.validate_level_boundaries(manifest_path, state_path)
        assert result["status"] == "pass", f"Expected pass, got {result['status']}"
        print(f"  ✅ test_level_boundaries_partial" + "")


def test_missing_manifest():
    """No manifest file → graceful fail on manifest checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")

        v = DagValidator()
        result = v.validate_node_existence(manifest_path)
        assert result["status"] == "fail", f"Expected fail, got {result['status']}"
        print(f"  ✅ test_missing_manifest" + "")


def test_full_clean_report():
    """All checks pass → verdict PASS, exit_code 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = os.path.join(tmpdir, "_bmad-output", "dag-automator")
        manifest_path = os.path.join(output, "dag-manifest.yaml")
        state_path = os.path.join(output, "orchestration.md")

        _write_manifest(manifest_path, _make_test_graph())
        _write_state_doc(state_path, 5)

        v = DagValidator()
        report = v.validate_all(manifest_path, state_path)
        assert report["verdict"] == "PASS", f"Expected PASS, got {report['verdict']}"
        assert report["exit_code"] == 0
        assert len(report["checks"]) == 4
        print(f"  ✅ test_full_clean_report: {report['summary']}")


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
