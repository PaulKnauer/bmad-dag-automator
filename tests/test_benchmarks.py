"""Tests for the performance benchmark harness."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmarks.bench_dag import (
    serial_chain, full_parallel, fan_out_fan_in, mixed_shape,
    run_benchmark, SHAPES
)


def test_serial_chain_shape():
    """10-node serial chain → 10 levels, width 1."""
    graph = serial_chain(10)
    graph.schedule()
    assert len(graph.levels) == 10
    assert max(l.width for l in graph.levels) == 1
    assert len(graph.nodes) == 10
    print(f"  ✅ test_serial_chain_shape: 10 levels, width 1")


def test_full_parallel_shape():
    """10-node parallel → 1 level, width 10."""
    graph = full_parallel(10)
    graph.schedule()
    assert len(graph.levels) == 1
    assert graph.levels[0].width == 10
    print(f"  ✅ test_full_parallel_shape: 1 level, width 10")


def test_fan_out_fan_in_shape():
    """Fan shape: root → 5 children → merge → 3 levels."""
    graph = fan_out_fan_in(5)
    graph.schedule()
    assert len(graph.levels) == 3
    # Level 0: root (1), Level 1: children (5), Level 2: leaf +... wait
    # leaf depends on root + all children, so it's at level 2
    assert graph.levels[0].width == 1
    assert graph.levels[1].width == 5
    assert graph.levels[2].width == 1
    print(f"  ✅ test_fan_out_fan_in_shape: 3 levels, max width 5")


def test_mixed_shape():
    """Mixed shape → 8 nodes."""
    graph = mixed_shape()
    graph.schedule()
    assert len(graph.nodes) == 8
    print(f"  ✅ test_mixed_shape: 8 nodes")


def test_benchmark_runs_all_shapes():
    """run_benchmark() processes all 4 shapes."""
    results = run_benchmark()
    assert len(results) == 4
    # All shapes should have valid stats
    for r in results:
        assert r["nodes"] > 0
        assert r["levels"] > 0
        assert r["max_width"] > 0
        assert r["speedup"] > 0
    print(f"  ✅ test_benchmark_runs_all_shapes: 4 shapes, all valid")


def test_serial_speedup_gt_1():
    """Serial chain speedup = nodes (10x). Parallel speedup = 1x."""
    results = run_benchmark()
    serial_result = [r for r in results if r["shape"] == "Serial Chain"][0]
    parallel_result = [r for r in results if r["shape"] == "Full Parallel"][0]
    assert serial_result["speedup"] >= 9.0  # 10 nodes / 1 width = 10x
    assert parallel_result["speedup"] == 1.0  # 10 nodes / 10 width = 1x
    print(f"  ✅ test_serial_speedup_gt_1: serial={serial_result['speedup']}x, parallel={parallel_result['speedup']}x")


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
