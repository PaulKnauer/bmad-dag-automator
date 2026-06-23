"""
BMAD DAG Scheduler — CLI entry point.

Usage:
  # DAG scheduling (standalone)
  python dag_scheduler.py schedule examples/stories.yaml --mode automatic
  python dag_scheduler.py schedule examples/stories.yaml --mode assisted
  python dag_scheduler.py schedule examples/stories.yaml --mode minimal
  python dag_scheduler.py schedule examples/stories.yaml --mode assisted --llm-output edges.json

  # Validation
  python dag_scheduler.py validate examples/stories.yaml     # validate + display DAG

  # Dry-run orchestrator (no tmux, no git)
  python dag_scheduler.py orchestrate examples/stories.yaml --dry-run

  # Full DAG orchestrator run
  python dag_scheduler.py orchestrate examples/auth-system.yaml \\
      --project /path/to/project --mode automatic
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import yaml

from dag_core import DagGraph, InductionMode
from dag_induction import DagInductor
from dag_orchestrator import DagOrchestrator


def load_stories(path: str) -> list[dict]:
    """Load stories from YAML or JSON."""
    with open(path) as f:
        if path.endswith(".json"):
            data = json.load(f)
        else:
            data = yaml.safe_load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return data.get("stories", [data])
    else:
        raise ValueError(f"Unexpected data format in {path}")


def cmd_schedule(args: argparse.Namespace) -> int:
    """Build DAG from stories and schedule it."""
    stories = load_stories(args.stories_file)
    architecture_context = ""
    if args.architecture:
        with open(args.architecture) as f:
            architecture_context = f.read()

    print(f"\n  📋 Loaded {len(stories)} stories from {args.stories_file}")
    print(f"  ⚙️  Mode: {args.mode}")

    # Phase 1: Build initial graph from explicit deps
    graph = DagGraph.from_story_list(stories, mode=args.mode)
    print(f"  🔗 Explicit edges: {sum(len(n.explicit_deps) for n in graph.nodes.values())}")

    # Phase 2: Induce implicit deps via LLM (unless minimal)
    inductor = DagInductor(graph)
    inductor.induct(stories, architecture_context)

    if args.mode != InductionMode.MINIMAL.value:
        if args.llm_output:
            # Load pre-computed LLM output from file
            with open(args.llm_output) as f:
                llm_result = f.read()
            applied = inductor.apply_llm_edges(llm_result)
        else:
            # Print the LLM context for manual/agent execution
            print("\n  🤖 LLM inference required for implicit dependencies.")
            print(f"  Mode: {args.mode}")
            print("\n  --- LLM PROMPT ---")
            print(inductor.get_llm_context())
            print("  --- END PROMPT ---")
            print(f"\n  Run: python dag_scheduler.py apply-llm {args.stories_file} < llm_output.json")
            print(f"  Or: python dag_scheduler.py schedule {args.stories_file} --llm-output <file>")
            return 2

        flagged = [e for e in applied if e.get("status") == "flagged"]
        added = [e for e in applied if e.get("status") == "added"]
        skipped = [e for e in applied if e.get("status", "").startswith("skip")]
        print(f"  🔗 Implicit edges added: {len(added)}")
        print(f"  🔗 Suggested edges (flagged for review): {len(flagged)}")
        if skipped:
            print(f"  ⚠️  Skipped: {len(skipped)}")

    # Phase 3: Schedule (validate → levels → critical path)
    graph.schedule()

    if graph.error:
        print(f"\n  ❌ Error: {graph.error}")
        return 1

    if graph.has_cycle:
        print(f"\n  ❌ Cycle detected at nodes: {graph.cycle_path}")
        return 1

    # Print results
    print(f"\n  📊 DAG Schedule:")
    print(f"     Nodes: {graph.to_dict()['dag']['total_nodes']}")
    print(f"     Levels: {graph.to_dict()['dag']['total_levels']}")
    print(f"     Max width: {graph.to_dict()['dag']['max_width']}")
    print(f"     Critical path: {' → '.join(graph.critical_path) if graph.critical_path else '(empty)'}")

    print(f"\n  📐 Level Breakdown:")
    for level in graph.levels:
        bar = "▓" * level.width + "░" * (max(5, graph.to_dict()['dag']['max_width']) - level.width)
        node_names = ", ".join(level.node_ids)
        print(f"     Level {level.index}: {bar}  ({level.width} agents)  [{node_names}]")

    # Write output
    output_path = args.output or "dag-manifest.yaml"
    manifest = graph.to_yaml()
    with open(output_path, "w") as f:
        f.write(manifest)
    print(f"\n  ✅ Manifest written to: {output_path}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a YAML story list without scheduling."""
    stories = load_stories(args.stories_file)

    graph = DagGraph.from_story_list(stories, mode=args.mode)

    # Check for common issues
    issues = []

    # No stories
    if len(graph.nodes) == 0:
        issues.append("❌ No stories found in input")
    else:
        print(f"\n  ✅ {len(graph.nodes)} stories loaded")

    # Dangling refs
    dangling = graph.find_dangling_refs()
    if dangling:
        issues.append(f"⚠️  Dangling references: {dangling}")
    else:
        print(f"  ✅ No dangling references")

    # Cycle detection
    if graph.detect_cycles():
        issues.append(f"❌ Cycle detected: {graph.cycle_path}")
    else:
        print(f"  ✅ No cycles detected")

    # Display explicit dep stats
    total_explicit = sum(len(n.explicit_deps) for n in graph.nodes.values())
    print(f"  🔗 {total_explicit} explicit dependency edges")

    if issues:
        print()
        for issue in issues:
            print(f"  {issue}")
        return 1 if any("❌" in i for i in issues) else 0

    print(f"\n  ✅ Stories file is valid")
    return 0


def cmd_apply_llm(args: argparse.Namespace) -> int:
    """Apply LLM output (from stdin) to a stories file."""
    stories = load_stories(args.stories_file)
    graph = DagGraph.from_story_list(stories, mode=args.mode)
    inductor = DagInductor(graph)

    llm_input = sys.stdin.read()
    applied = inductor.apply_llm_edges(llm_input)

    flagged = [e for e in applied if e.get("status") == "flagged"]
    added = [e for e in applied if e.get("status") == "added"]
    errors = [e for e in applied if "error" in e]

    print(f"\n  LLM edges applied:")
    print(f"    Added (automatic): {len(added)}")
    print(f"    Flagged (assisted): {len(flagged)}")
    if errors:
        print(f"    Errors: {len(errors)}")
        for e in errors:
            print(f"      ⚠️  {e.get('error', 'unknown error')[:100]}")

    # Now schedule
    graph.schedule()
    if graph.error:
        print(f"\n  ❌ Scheduling error: {graph.error}")
        return 1

    print(f"\n  📊 DAG Schedule:")
    print(f"     Levels: {len(graph.levels)}, Max width: {max((l.width for l in graph.levels), default=0)}")
    for level in graph.levels:
        print(f"     Level {level.index}: [{', '.join(level.node_ids)}]")

    output_path = args.output or "dag-manifest.yaml"
    with open(output_path, "w") as f:
        f.write(graph.to_yaml())
    print(f"\n  ✅ Manifest written to: {output_path}")

    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Show full internal state of the DAG."""
    stories = load_stories(args.stories_file)
    graph = DagGraph.from_story_list(stories, mode=args.mode)
    inductor = DagInductor(graph)
    inductor.induct(stories)

    print(yaml.dump(graph.to_dict(), default_flow_style=False, sort_keys=False))
    return 0


def cmd_orchestrate(args: argparse.Namespace) -> int:
    """Run the full DAG orchestrator pipeline."""
    stories = load_stories(args.stories_file)
    project_root = os.path.abspath(args.project)

    orch = DagOrchestrator(
        project_root=project_root,
        mode=args.mode,
        max_concurrent=args.max_concurrent,
        dry_run=args.dry_run,
    )
    orch.resume = args.resume
    orch.load_stories_from_dict(stories)
    result = orch.run_dag(
        architecture_context=args.architecture or "",
        llm_edges_path=args.llm_output,
        agent_tool=args.agent,
        agent_model=args.model,
    )

    if result.get("status") == "error":
        return 1
    if result.get("status") == "paused":
        return 2
    return 0


def cmd_validate_dag(args: argparse.Namespace) -> int:
    """Validate DAG consistency from prior run artifacts."""
    from dag_validator import DagValidator

    project_root = os.path.abspath(args.project)
    output_dir = os.path.join(project_root, "_bmad-output", "dag-automator")
    manifest_path = os.path.join(output_dir, "dag-manifest.yaml")
    state_path = os.path.join(output_dir, "orchestration.md")

    validator = DagValidator()
    report = validator.validate_all(manifest_path, state_path)
    validator.print_report(report)
    return report["exit_code"]


def main() -> int:
    parser = argparse.ArgumentParser(description="BMAD DAG Scheduler")
    parser.add_argument("--mode", choices=["minimal", "assisted", "automatic"],
                        default="automatic", help="DAG induction mode")
    sub = parser.add_subparsers(dest="command", required=True)

    # schedule
    p_sched = sub.add_parser("schedule", help="Build DAG and schedule execution")
    p_sched.add_argument("stories_file", help="YAML/JSON file with story list")
    p_sched.add_argument("--architecture", "-a", help="Architecture context file")
    p_sched.add_argument("--llm-output", help="Pre-computed LLM output JSON file")
    p_sched.add_argument("--output", "-o", default="dag-manifest.yaml", help="Output manifest path")
    p_sched.set_defaults(func=cmd_schedule)

    # validate
    p_val = sub.add_parser("validate", help="Validate story YAML without scheduling")
    p_val.add_argument("stories_file", help="YAML/JSON file with story list")
    p_val.set_defaults(func=cmd_validate)

    # validate-dag
    p_val_dag = sub.add_parser("validate-dag", help="Validate DAG consistency from prior run artifacts")
    p_val_dag.add_argument("--project", "-p", default=".",
                           help="Project root directory (default: current dir)")
    p_val_dag.set_defaults(func=cmd_validate_dag)

    # apply-llm
    p_llm = sub.add_parser("apply-llm", help="Apply LLM edges from stdin to stories file")
    p_llm.add_argument("stories_file", help="YAML/JSON file with story list")
    p_llm.add_argument("--output", "-o", default="dag-manifest.yaml", help="Output manifest path")
    p_llm.set_defaults(func=cmd_apply_llm)

    # inspect
    p_inspect = sub.add_parser("inspect", help="Show full DAG internal state")
    p_inspect.add_argument("stories_file", help="YAML/JSON file with story list")
    p_inspect.set_defaults(func=cmd_inspect)

    # orchestrate
    p_orch = sub.add_parser("orchestrate", help="Run full DAG orchestrator")
    p_orch.add_argument("stories_file", help="YAML/JSON file with story list")
    p_orch.add_argument("--project", "-p", default=".",
                        help="Project root directory (default: current dir)")
    p_orch.add_argument("--architecture", "-a", help="Architecture context file")
    p_orch.add_argument("--llm-output", help="Pre-computed LLM output JSON file")
    p_orch.add_argument("--max-concurrent", type=int, default=4,
                        help="Max concurrent agents (default: 4)")
    p_orch.add_argument("--agent", choices=["claude-code", "codex", "opencode"],
                        default="claude-code", help="Agent tool (default: claude-code)")
    p_orch.add_argument("--model", default="sonnet",
                        help="Model alias (default: sonnet)")
    p_orch.add_argument("--dry-run", action="store_true",
                        help="Simulate without tmux or git")
    p_orch.add_argument("--resume", action="store_true",
                        help="Resume from last incomplete DAG level")
    p_orch.set_defaults(func=cmd_orchestrate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
