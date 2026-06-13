"""Quick debug script for the orchestrator dry-run."""
import yaml
import sys
sys.path.insert(0, ".")
from dag_orchestrator import DagOrchestrator

print("=== Testing Phase 1: Init ===")
orch = DagOrchestrator(project_root="/tmp/test", dry_run=True)

with open("examples/auth-system.yaml") as f:
    data = yaml.safe_load(f)
stories = data if isinstance(data, list) else data.get("stories", [])
orch.load_stories_from_dict(stories)

print("=== Testing Phase 2: Induct ===")
result = orch.induct()
print(f"Induct: {result['status']}")

print("=== Testing Phase 3: Init bridge + pool ===")
from artifact_bridge import ArtifactBridge
orch.bridge = ArtifactBridge(project_root="/tmp/test", dry_run=True)
orch.bridge.init_run()
print("Bridge init_run ok")

from agent_pool import AgentPool
orch.pool = AgentPool(project_root="/tmp/test", dry_run=True)
print("Pool init ok")

from state_doc import DagStateDoc
orch.state = DagStateDoc.from_manifest(
    orch.graph.to_dict(), output_dir="/tmp/test/_bmad-output/dag-automator"
)
orch.state.save("/tmp/test/_bmad-output/dag-automator/orchestration.md")
print("State doc ok")

print("=== Testing Phase 4: Level execution ===")
for level_idx, level in enumerate(orch.graph.levels):
    print(f"  Level {level_idx}: {level.width} nodes")
    level_nodes = [orch.graph.nodes[nid] for nid in level.node_ids]
    node_data = [{"id": n.id, "title": n.title, "specPath": f"stories/{n.id}.md", "spec": f"stories/{n.id}.md"} for n in level_nodes]

    level_branch = orch.bridge.create_level_branch(level_idx)
    print(f"  Created branch: {level_branch.branch_name}")

    from agent_pool import AgentConfig, AgentTool
    results = orch.pool.wait_level(
        nodes=node_data,
        config_map={n.id: AgentConfig(tool=AgentTool.CLAUDE_CODE, model="sonnet") for n in level_nodes},
        level_index=level_idx,
        upstream_branch=level_branch.branch_name,
        poll_interval=1,
        timeout_minutes=1,
    )
    print(f"  Got {len(results)} results for level {level_idx}")
    for r in results:
        print(f"    {r.node_id}: {r.status.value} ({r.duration_seconds}s)")

    merge_ok = orch.bridge.merge_level(level_idx)
    print(f"  Merge: {merge_ok}")
    orch.state.record_level_complete(level_idx, [{"id": r.node_id, "status": r.status.value} for r in results])
    orch.state.save("/tmp/test/_bmad-output/dag-automator/orchestration.md")

final_branch = orch.bridge.finalize_run()
print(f"Final branch: {final_branch}")
orch.state.mark_complete()
print("=== ALL OK ===")
