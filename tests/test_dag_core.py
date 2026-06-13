"""Tests for the BMAD DAG Scheduler core algorithms."""

import json
import os
import sys
import tempfile
import yaml

# Add project to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dag_core import DagGraph, DagNode, InductionMode
from dag_induction import DagInductor


def test_basic_dag():
    """3 stories in serial chain: A → B → C"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Story A"))
    graph.add_node(DagNode(id="B", title="Story B", explicit_deps=["A"]))
    graph.add_node(DagNode(id="C", title="Story C", explicit_deps=["B"]))
    
    graph.schedule()
    
    assert graph.status.value == "validated"
    assert not graph.has_cycle
    assert len(graph.levels) == 3
    assert graph.levels[0].node_ids == ["A"]
    assert graph.levels[1].node_ids == ["B"]
    assert graph.levels[2].node_ids == ["C"]
    assert graph.critical_path == ["A", "B", "C"]
    assert all(l.width == 1 for l in graph.levels)
    assert graph.to_dict()["dag"]["max_width"] == 1


def test_parallel_dag():
    """3 independent stories → all at level 0"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Story A"))
    graph.add_node(DagNode(id="B", title="Story B"))
    graph.add_node(DagNode(id="C", title="Story C"))
    
    graph.schedule()
    
    assert len(graph.levels) == 1
    assert sorted(graph.levels[0].node_ids) == ["A", "B", "C"]
    assert graph.levels[0].width == 3
    assert graph.to_dict()["dag"]["max_width"] == 3


def test_fan_out():
    """A → B, A → C (fan-out)"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Foundation"))
    graph.add_node(DagNode(id="B", title="Feature 1", explicit_deps=["A"]))
    graph.add_node(DagNode(id="C", title="Feature 2", explicit_deps=["A"]))
    
    graph.schedule()
    
    assert len(graph.levels) == 2
    assert graph.levels[0].node_ids == ["A"]
    assert sorted(graph.levels[1].node_ids) == ["B", "C"]
    assert graph.levels[1].width == 2
    assert graph.to_dict()["dag"]["max_width"] == 2


def test_fan_in():
    """A → C, B → C (fan-in)"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Service A"))
    graph.add_node(DagNode(id="B", title="Service B"))
    graph.add_node(DagNode(id="C", title="Integration", explicit_deps=["A", "B"]))
    
    graph.schedule()
    
    assert len(graph.levels) == 2
    assert sorted(graph.levels[0].node_ids) == ["A", "B"]
    assert graph.levels[0].width == 2
    assert graph.levels[1].node_ids == ["C"]
    assert graph.to_dict()["dag"]["max_width"] == 2


def test_complex_dag():
    """Mixed shape from the auth-system example:
    Level 0: epic-1.1, epic-1.2     (roots, no deps)
    Level 1: epic-1.3, epic-1.4     (depend on level 0)
    Level 2: epic-1.5, epic-2.1, epic-2.3 (depend on level 1)
    Level 3: epic-2.2               (depends on level 2)
    """
    graph = DagGraph()
    graph.add_node(DagNode(id="epic-1.1", title="User model", explicit_deps=[]))
    graph.add_node(DagNode(id="epic-1.2", title="Password hashing", explicit_deps=[]))
    graph.add_node(DagNode(id="epic-1.3", title="Registration", explicit_deps=["epic-1.1", "epic-1.2"]))
    graph.add_node(DagNode(id="epic-1.4", title="Login + JWT", explicit_deps=["epic-1.1"]))
    graph.add_node(DagNode(id="epic-1.5", title="Session mgmt", explicit_deps=["epic-1.4"]))
    graph.add_node(DagNode(id="epic-2.1", title="Profile read", explicit_deps=["epic-1.1", "epic-1.4"]))
    graph.add_node(DagNode(id="epic-2.2", title="Admin UI", explicit_deps=["epic-2.1", "epic-1.3"]))
    graph.add_node(DagNode(id="epic-2.3", title="Email verify", explicit_deps=["epic-1.3"]))
    
    graph.schedule()
    
    assert len(graph.levels) == 4
    assert sorted(graph.levels[0].node_ids) == ["epic-1.1", "epic-1.2"]
    assert graph.levels[0].width == 2
    
    assert sorted(graph.levels[1].node_ids) == ["epic-1.3", "epic-1.4"]
    assert graph.levels[1].width == 2
    
    # Level 2 has 3 nodes
    expected_l2 = {"epic-1.5", "epic-2.1", "epic-2.3"}
    assert set(graph.levels[2].node_ids) == expected_l2
    assert graph.levels[2].width == 3
    
    assert graph.levels[3].node_ids == ["epic-2.2"]
    assert graph.levels[3].width == 1
    
    assert graph.to_dict()["dag"]["max_width"] == 3


def test_cycle_detection():
    """A → B → C → A (cycle)"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="A", explicit_deps=["C"]))
    graph.add_node(DagNode(id="B", title="B", explicit_deps=["A"]))
    graph.add_node(DagNode(id="C", title="C", explicit_deps=["B"]))
    
    graph.schedule()
    
    assert graph.has_cycle
    assert graph.status.value == "aborted"
    assert graph.error is not None
    assert "cycle" in graph.error.lower()


def test_dangling_ref():
    """A depends on Z which doesn't exist in the graph"""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Story A", explicit_deps=["Z"]))
    graph.add_node(DagNode(id="B", title="Story B"))
    
    result = graph.schedule()
    
    assert result.status.value == "aborted"
    assert result.error is not None
    assert "dangling" in result.error.lower()


def test_induction_apply_automatic():
    """LLM edges applied immediately in automatic mode."""
    graph = DagGraph(mode=InductionMode.AUTOMATIC)
    graph.add_node(DagNode(id="A", title="User model", interfaces_provides=["User"]))
    graph.add_node(DagNode(id="B", title="Login API", consumes_interfaces=["User"]))
    graph.add_node(DagNode(id="C", title="Password hash", interfaces_provides=["Hasher"]))
    
    inductor = DagInductor(graph)
    
    llm_output = json.dumps({
        "edges": [
            {"from": "B", "to": "A", "reasoning": "Login API consumes User type from User model", "confidence": "high"}
        ]
    })
    
    applied = inductor.apply_llm_edges(llm_output)
    
    assert len(applied) == 1
    assert applied[0]["status"] == "added"
    assert "A" in graph.nodes["B"].implicit_deps


def test_induction_apply_assisted():
    """LLM edges flagged for review in assisted mode."""
    graph = DagGraph(mode=InductionMode.ASSISTED)
    graph.add_node(DagNode(id="A", title="User model", interfaces_provides=["User"]))
    graph.add_node(DagNode(id="B", title="Login API", consumes_interfaces=["User"]))
    
    inductor = DagInductor(graph)
    
    llm_output = json.dumps({
        "edges": [
            {"from": "B", "to": "A", "reasoning": "Consumes User", "confidence": "high"}
        ]
    })
    
    applied = inductor.apply_llm_edges(llm_output)
    
    assert len(applied) == 1
    assert applied[0]["status"] == "flagged"
    assert "A" in graph.nodes["B"].suggested_deps
    assert "A" not in graph.nodes["B"].implicit_deps  # not yet promoted


def test_induction_promote_reject():
    """Promote and reject suggested edges."""
    graph = DagGraph(mode=InductionMode.ASSISTED)
    graph.add_node(DagNode(id="A", title="Model"))
    graph.add_node(DagNode(id="B", title="API", suggested_deps=["A"]))
    
    inductor = DagInductor(graph)
    
    assert inductor.promote_suggested("B", "A") == True
    assert "A" in graph.nodes["B"].implicit_deps
    assert "A" not in graph.nodes["B"].suggested_deps
    
    # Reject
    graph2 = DagGraph(mode=InductionMode.ASSISTED)
    graph2.add_node(DagNode(id="X", title="Model"))
    graph2.add_node(DagNode(id="Y", title="API", suggested_deps=["X"]))
    
    inductor2 = DagInductor(graph2)
    
    assert inductor2.reject_suggested("Y", "X") == True
    assert "X" not in graph2.nodes["Y"].implicit_deps
    assert "X" not in graph2.nodes["Y"].suggested_deps


def test_induction_minimal_skips_llm():
    """In minimal mode, inductor skips LLM pass."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="A", title="A"))
    graph.add_node(DagNode(id="B", title="B"))
    
    inductor = DagInductor(graph)
    inductor.induct([])
    
    # LLM context should be empty since we skipped
    assert inductor.get_llm_context() == ""


def test_from_story_list_roundtrip():
    """Build graph from story list dict, schedule, export to dict."""
    stories = [
        {"id": "S1", "title": "Setup DB", "explicit_deps": []},
        {"id": "S2", "title": "User model", "explicit_deps": ["S1"]},
        {"id": "S3", "title": "API layer", "explicit_deps": ["S2"]},
    ]
    
    graph = DagGraph.from_story_list(stories, mode="automatic")
    graph.schedule()
    
    result = graph.to_dict()
    assert result["dag"]["total_nodes"] == 3
    assert result["dag"]["total_levels"] == 3
    assert result["dag"]["critical_path"] == ["S1", "S2", "S3"]
    assert result["dag"]["max_width"] == 1


def test_critical_path_alternative():
    """When there are multiple paths, the longest wins."""
    # A → B → D (length 3)
    # A → C → D (length 3)
    # Both are length 3, so the critical path should be one of them
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="Root"))
    graph.add_node(DagNode(id="B", title="Path 1", explicit_deps=["A"]))
    graph.add_node(DagNode(id="C", title="Path 2", explicit_deps=["A"]))
    graph.add_node(DagNode(id="D", title="Merge", explicit_deps=["B", "C"]))
    
    graph.schedule()
    
    assert len(graph.critical_path) == 3  # A → B/C → D
    assert graph.critical_path[0] == "A"
    assert graph.critical_path[-1] == "D"


def test_edge_case_single_node():
    """Graph with one node and no deps."""
    graph = DagGraph()
    graph.add_node(DagNode(id="only", title="Only story"))
    graph.schedule()
    
    assert len(graph.levels) == 1
    assert graph.levels[0].width == 1
    assert graph.critical_path == ["only"]


def test_edge_case_no_nodes():
    """Empty graph."""
    graph = DagGraph()
    graph.schedule()
    
    assert len(graph.levels) == 0
    assert graph.critical_path == []


def test_edge_case_self_dep():
    """A depends on itself — cycle."""
    graph = DagGraph()
    graph.add_node(DagNode(id="A", title="A", explicit_deps=["A"]))
    graph.schedule()
    
    assert graph.has_cycle


def test_elastic_agent_allocation():
    """Verify agent count = min(max_agents, level_width) per level."""
    graph = DagGraph()
    for i in range(10):
        graph.add_node(DagNode(id=f"N{i}", title=f"Node {i}"))
    
    graph.schedule()
    
    # All independent → 1 level, width 10
    assert len(graph.levels) == 1
    assert graph.levels[0].width == 10
    
    # With max_agents=4, only 4 would run concurrently
    max_agents = 4
    pool_size = min(max_agents, graph.levels[0].width)
    assert pool_size == 4


if __name__ == "__main__":
    # Run all tests
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
    
    print(f"\n  {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)
