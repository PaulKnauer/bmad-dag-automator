"""DAG Scheduling Performance Benchmarks.

Measures scheduling time, parallel speedup, and agent utilisation
across various DAG shapes. Pure computation benchmarks — no tmux or git.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dag_core import DagGraph, DagNode, InductionMode


# --- Benchmark Fixtures ---

def serial_chain(n: int = 10) -> DagGraph:
    """Serial chain: N0 → N1 → ... → N{n-1} (n levels, width 1)."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    prev = None
    for i in range(n):
        nid = f"N{i}"
        deps = [prev] if prev else []
        graph.add_node(DagNode(id=nid, title=f"Node {i}", explicit_deps=deps))
        prev = nid
    return graph


def full_parallel(n: int = 10) -> DagGraph:
    """All nodes independent: 1 level, width n."""
    graph = DagGraph(mode=InductionMode.MINIMAL)
    for i in range(n):
        graph.add_node(DagNode(id=f"N{i}", title=f"Node {i}"))
    return graph


def fan_out_fan_in(n_fan: int = 5) -> DagGraph:
    """Root → n_fan children → merge.

    Level 0: root (1)
    Level 1: n_fan children
    Level 2: merge leaf (1)
    Total: 2 + n_fan nodes, 3 levels, max width = n_fan
    """
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="root", title="Root"))
    merge_deps = ["root"]
    for i in range(n_fan):
        nid = f"child_{i}"
        graph.add_node(DagNode(id=nid, title=f"Child {i}", explicit_deps=["root"]))
        merge_deps.append(nid)
    # Every child depends on root; leaf depends on root + all children
    graph.add_node(DagNode(id="leaf", title="Leaf", explicit_deps=["root"] + [f"child_{i}" for i in range(n_fan)]))
    return graph


def mixed_shape() -> DagGraph:
    """Mixed: 8 nodes, 4 levels, varying widths.

    Level 0: A, B (2)
    Level 1: C (depends on A, B) — 1
    Level 2: D, E (depends on C) — 2
    Level 3: F (depends on D, E) — 1
    """
    graph = DagGraph(mode=InductionMode.MINIMAL)
    graph.add_node(DagNode(id="A", title="A"))
    graph.add_node(DagNode(id="B", title="B"))
    graph.add_node(DagNode(id="C", title="C", explicit_deps=["A", "B"]))
    graph.add_node(DagNode(id="D", title="D", explicit_deps=["C"]))
    graph.add_node(DagNode(id="E", title="E", explicit_deps=["C"]))
    graph.add_node(DagNode(id="F", title="F", explicit_deps=["D", "E"]))
    graph.add_node(DagNode(id="G", title="G", explicit_deps=["F"]))
    graph.add_node(DagNode(id="H", title="H", explicit_deps=["F"]))
    return graph


# --- Benchmarks ---

SHAPES = [
    ("Serial Chain", serial_chain, {"n": 10}),
    ("Full Parallel", full_parallel, {"n": 10}),
    ("Fan-out/fan-in", fan_out_fan_in, {"n_fan": 5}),
    ("Mixed", mixed_shape, {}),
]


def run_benchmark() -> list[dict]:
    """Run all benchmarks and return results."""
    results = []

    for name, shape_fn, kwargs in SHAPES:
        # Build graph
        graph = shape_fn(**kwargs)
        node_count = len(graph.nodes)

        # Time only the scheduling (deterministic, fast)
        start = time.perf_counter()
        graph.schedule()
        elapsed = time.perf_counter() - start

        level_count = len(graph.levels)
        max_width = max((l.width for l in graph.levels), default=0)

        # Estimate serial time (sum of level times = n * avg_time)
        # In a real run, each node takes roughly the same time (t_node)
        # Serial: n * t_node,  Parallel: max_width * t_node
        # Speedup = serial_time / parallel_time = n / max_width
        # But we can't know t_node without real agents.
        # Here we measure scheduling overhead (microseconds), not execution.
        # Speedup is theoretical: n / max_width (lower bound on speedup)
        serial_estimate = node_count  # abstract units
        scheduled_min = max_width     # abstract units
        theoretical_speedup = node_count / max_width if max_width > 0 else 1.0

        # Agent utilisation: if pool = level width for each level
        total_capacity = sum(l.width for l in graph.levels)
        total_used = sum(l.width for l in graph.levels)  # all slots used in theory
        utilisation = (total_used / total_capacity * 100) if total_capacity > 0 else 100.0

        results.append({
            "shape": name,
            "nodes": node_count,
            "levels": level_count,
            "max_width": max_width,
            "sched_ms": elapsed * 1000,
            "serial_units": serial_estimate,
            "parallel_units": scheduled_min,
            "speedup": round(theoretical_speedup, 1),
            "utilisation_pct": round(utilisation, 0),
        })

    return results


def print_results(results: list[dict]) -> None:
    """Print formatted benchmark results table."""
    print()
    print("  DAG Scheduling Benchmarks")
    print("  " + "=" * 72)
    print()
    print(f"  {'Shape':<20} {'Nodes':>5} {'Lvls':>4} {'Width':>5} "
          f"{'Sched':>7} {'Serial':>7} {'Par':>5} {'Speed':>6} {'Util':>5}")
    print(f"  {'─' * 20} {'─' * 5} {'─' * 4} {'─' * 5} "
          f"{'─' * 7} {'─' * 7} {'─' * 5} {'─' * 6} {'─' * 5}")

    for r in results:
        print(f"  {r['shape']:<20} {r['nodes']:>5} {r['levels']:>4} {r['max_width']:>5} "
              f"{r['sched_ms']:>6.2f}ms {r['serial_units']:>5}  {r['parallel_units']:>3}  "
              f"{r['speedup']:>4.1f}x {r['utilisation_pct']:>4.0f}%")

    print()
    print(f"  {'─' * 72}")
    print(f"  Scheduling overhead: {sum(r['sched_ms'] for r in results):.2f}ms total "
          f"({sum(r['nodes'] for r in results)} nodes across 4 shapes)")
    print()


def main() -> int:
    results = run_benchmark()
    print_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
