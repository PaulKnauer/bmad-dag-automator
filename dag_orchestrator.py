"""
DAG Orchestrator — main execution loop that ties together:

  1. DAG Scheduler (dag_core) → produces DAG manifest with levels + critical path
  2. AgentPool → elastic tmux child sessions per DAG node
  3. ArtifactBridge → git branch-per-level management
  4. StateDocument → markdown state doc (machine + human readable)

Flow per DAG level:
  create_level_branch()      → branch from upstream
  agent_pool.wait_level()    → spawn + monitor + collect results
  handle_failures()          → DAG-aware recovery per node
  artifact_bridge.merge_level() → merge node work into level branch
  state_doc.record_level_complete() → update state
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, Optional

import yaml

from agent_pool import AgentConfig, AgentPool, AgentStatus, AgentTool
from artifact_bridge import ArtifactBridge, MergeStrategy
from dag_core import DagGraph, InductionMode
from dag_induction import DagInductor
from state_doc import DagRunStatus, DagStateDoc


class DagOrchestrator:
    """Main orchestrator for DAG-based autonomous execution.

    Usage:
        orch = DagOrchestrator(project_root="/path/to/project")
        orch.load_stories("examples/auth-system.yaml")
        orch.run_dag()
    """

    def __init__(self, project_root: str, output_dir: str = "_bmad-output/dag-automator",
                 max_concurrent: int = 4, mode: str = "automatic",
                 dry_run: bool = False):
        self.project_root = os.path.abspath(project_root)
        self.output_dir = os.path.join(self.project_root, output_dir)
        self.max_concurrent = max_concurrent
        self.mode = InductionMode(mode)
        self.dry_run = dry_run

        # Components (lazy init)
        self.graph: Optional[DagGraph] = None
        self.inductor: Optional[DagInductor] = None
        self.pool: Optional[AgentPool] = None
        self.bridge: Optional[ArtifactBridge] = None
        self.state: Optional[DagStateDoc] = None

        # Resume support
        self.resume: bool = False
        self._resume_from_level: Optional[int] = None

        # Runtime state
        self._stories: list[dict] = []
        self._failed_nodes: list[dict] = []
        self._level_results: dict[int, list[dict]] = {}

    def load_stories(self, path: str) -> None:
        """Load story data from a YAML or JSON file."""
        with open(path) as f:
            if path.endswith(".json"):
                import json
                data = json.load(f)
            else:
                data = yaml.safe_load(f)

        if isinstance(data, list):
            self._stories = data
        elif isinstance(data, dict):
            self._stories = data.get("stories", [data])
        else:
            raise ValueError(f"Unexpected data format in {path}")

    def load_stories_from_dict(self, stories: list[dict]) -> None:
        """Load story data from a list of dicts."""
        self._stories = stories

    def induct(self, architecture_context: str = "",
               llm_edges_path: Optional[str] = None) -> dict:
        """Phase 1: DAG induction from stories.

        Returns the induction summary dict.
        """
        if not self._stories:
            raise RuntimeError("No stories loaded. Call load_stories() first.")

        print(f"\n  🔄 Phase 1: DAG Induction (mode={self.mode.value})", flush=True)

        # Build graph from explicit deps
        self.graph = DagGraph.from_story_list(self._stories, mode=self.mode.value)
        print(f"     {len(self.graph.nodes)} stories, "
              f"{sum(len(n.explicit_deps) for n in self.graph.nodes.values())} explicit edges",
              flush=True)

        # Induce implicit deps
        self.inductor = DagInductor(self.graph)
        self.inductor.induct(self._stories, architecture_context)

        applied_edges = []
        if self.mode != InductionMode.MINIMAL:
            if llm_edges_path:
                with open(llm_edges_path) as f:
                    llm_output = f.read()
                applied_edges = self.inductor.apply_llm_edges(llm_output)
                added = [e for e in applied_edges if e.get("status") == "added"]
                flagged = [e for e in applied_edges if e.get("status") == "flagged"]
                print(f"     LLM edges added: {len(added)}", flush=True)
                print(f"     LLM edges flagged: {len(flagged)}", flush=True)
            else:
                print(f"     ⚠️  No LLM output provided — using explicit deps only", flush=True)
                print(f"     Provide with: --llm-output <file>", flush=True)
        else:
            print(f"     Skipping LLM pass (minimal mode)", flush=True)

        # Schedule
        self.graph.schedule()

        if self.graph.error:
            print(f"     ❌ Scheduling error: {self.graph.error}", flush=True)
            return {"status": "error", "error": self.graph.error}

        if self.graph.has_cycle:
            print(f"     ❌ Cycle detected: {self.graph.cycle_path}", flush=True)
            return {"status": "error", "error": f"Cycle: {self.graph.cycle_path}"}

        print(f"     ✅ {len(self.graph.levels)} levels, "
              f"max width {self.graph.to_dict()['dag']['max_width']}, "
              f"critical path: {' → '.join(self.graph.critical_path)}", flush=True)

        return {
            "status": "ok",
            "total_nodes": len(self.graph.nodes),
            "total_levels": len(self.graph.levels),
            "max_width": self.graph.to_dict()["dag"]["max_width"],
            "critical_path": self.graph.critical_path,
            "applied_edges": applied_edges,
        }

    def _find_resume_point(self, state_path: str, manifest_path: str) -> Optional[int]:
        """Determine the DAG level to resume from.

        Loads the prior state doc and current DAG manifest, validates
        consistency, and returns the level index to start from (first
        incomplete level). Returns None if the prior run is already
        complete.

        Args:
            state_path: Path to the existing orchestration.md.
            manifest_path: Path to the existing dag-manifest.yaml.

        Returns:
            Level index to resume from, or None if already complete.

        Raises:
            FileNotFoundError: If state doc or manifest is missing.
            ValueError: If story count or level structure differs.
        """
        # Load prior state
        state = DagStateDoc.load(state_path)
        completed_count = len(state.completed_nodes)

        # Load prior manifest for comparison
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(
                f"Manifest not found at {manifest_path} — "
                f"cannot resume without a prior DAG manifest"
            )

        with open(manifest_path) as f:
            prior_manifest = yaml.safe_load(f)

        prior_node_count = len(
            prior_manifest.get("nodes", {})
        ) if isinstance(prior_manifest, dict) else 0
        prior_level_count = len(
            prior_manifest.get("dag", {}).get("levels", [])
        ) if isinstance(prior_manifest, dict) else 0

        current_node_count = len(self.graph.nodes) if self.graph else 0
        current_level_count = len(self.graph.levels) if self.graph else 0

        # Consistency check
        if prior_node_count != current_node_count:
            raise ValueError(
                f"Story count mismatch: prior run had {prior_node_count} nodes, "
                f"current run has {current_node_count}. Cannot resume."
            )
        if prior_level_count != current_level_count:
            raise ValueError(
                f"Level structure changed: prior run had {prior_level_count} levels, "
                f"current has {current_level_count}. Cannot resume."
            )

        # Determine resume point
        if completed_count >= current_node_count:
            return None  # Already complete

        # Resume from the first level that has any incomplete nodes
        prior_levels = prior_manifest.get("dag", {}).get("levels", [])
        for level_info in prior_levels:
            level_idx = level_info.get("index", 0)
            level_nodes = level_info.get("nodes", [])
            all_completed = all(
                any(
                    cn.get("id") == nid and cn.get("status") == "completed"
                    for cn in state.completed_nodes
                )
                for nid in level_nodes
            )
            if not all_completed:
                return level_idx

        return None  # All levels complete

    def run_dag(self, architecture_context: str = "",
                llm_edges_path: Optional[str] = None,
                agent_tool: str = "claude-code",
                agent_model: str = "sonnet") -> dict:
        """Full DAG pipeline: induct → execute levels → finalize.

        Returns a run summary dict.
        """
        # Phase 1: Induct
        induction_result = self.induct(architecture_context, llm_edges_path)
        if induction_result.get("status") == "error":
            return induction_result

        # Save manifest
        os.makedirs(self.output_dir, exist_ok=True)
        manifest_path = os.path.join(self.output_dir, "dag-manifest.yaml")
        with open(manifest_path, "w") as f:
            f.write(self.graph.to_yaml())

        # Init components
        self.pool = AgentPool(
            project_root=self.project_root,
            max_concurrent=self.max_concurrent,
            dry_run=self.dry_run,
        )
        self.bridge = ArtifactBridge(
            project_root=self.project_root,
            dry_run=self.dry_run,
        )
        self.state = DagStateDoc.from_manifest(
            self.graph.to_dict(), output_dir=self.output_dir
        )
        self.state.save(os.path.join(self.output_dir, "orchestration.md"))

        # Phase 2: Execute levels
        print(f"\n  🔄 Phase 2: Level-by-level execution", flush=True)
        run_start = datetime.now()

        # Build agent config map (shared across all nodes for now)
        default_config = AgentConfig(
            tool=AgentTool(agent_tool),
            model=agent_model,
        )

        # Resume detection — skip already-completed levels
        if self.resume:
            state_path = os.path.join(self.output_dir, "orchestration.md")
            manifest_path = os.path.join(self.output_dir, "dag-manifest.yaml")
            resume_level = self._find_resume_point(state_path, manifest_path)
            if resume_level is not None:
                self._resume_from_level = resume_level
                print(f"     ⏯️  Resuming from Level {resume_level}", flush=True)
                # Reload prior state doc to extend it
                self.state = DagStateDoc.load(state_path)
                self.state.mark_resumed(resume_level, "resume via --resume flag")
                self.state.save(os.path.join(self.output_dir, "orchestration.md"))
            else:
                print(f"     ✅ Prior run already complete — nothing to do", flush=True)
                return {"status": "complete", "message": "Prior run already complete"}

        # Initialize git
        if not self.dry_run:
            try:
                self.bridge.init_run()
            except RuntimeError as e:
                print(f"     ❌ Git init failed: {e}")
                return {"status": "error", "error": str(e)}

        failed_nodes_per_level: list[tuple[int, str, str]] = []

        for level_idx, level in enumerate(self.graph.levels):
            # Skip levels that were already completed in a prior resume run
            if self._resume_from_level is not None and level_idx < self._resume_from_level:
                print(f"     ⏭️  Level {level_idx}: skipped (completed in prior run)")
                continue

            print(f"  📐 Level {level_idx}: {level.width} node(s)")
            level_nodes = [self.graph.nodes[nid] for nid in level.node_ids]

            # Prepare git branch for this level
            level_branch = self.bridge.create_level_branch(level_idx)
            upstream = level_branch.branch_name

            # Build node data for agent pool
            node_data = []
            for node in level_nodes:
                spec_dir = os.path.join(self.project_root, "project-docs",
                                        "implementation-artifacts")
                spec_path = os.path.join(spec_dir, f"{node.id}.md")
                node_data.append({
                    "id": node.id,
                    "title": node.title,
                    "specPath": spec_path,
                    "spec": spec_path,
                })

            # Spawn and wait
            results = self.pool.wait_level(
                nodes=node_data,
                config_map={n.id: default_config for n in level_nodes},
                level_index=level_idx,
                upstream_branch=upstream,
                poll_interval=10,
                timeout_minutes=30,
            )

            # Process results
            level_results = []
            for r in results:
                entry = {
                    "id": r.node_id,
                    "status": r.status.value,
                    "session_id": r.session_id,
                    "duration_s": r.duration_seconds,
                    "error": r.error,
                }
                level_results.append(entry)

                if r.status == AgentStatus.COMPLETED:
                    # Record commit on level branch
                    sha = self.bridge.record_node_commit(r.node_id, level_idx)
                    entry["commit_sha"] = sha
                elif r.status == AgentStatus.FAILED:
                    failed_nodes_per_level.append((level_idx, r.node_id, r.error or "unknown"))

            self._level_results[level_idx] = level_results

            # DAG-aware failure handling
            if failed_nodes_per_level:
                # Check if any failed node has downstream dependents
                for level_idx_f, node_id, error in failed_nodes_per_level:
                    node = self.graph.nodes.get(node_id)
                    if node:
                        # Find what depends on this node
                        downstream = []
                        for nid, n in self.graph.nodes.items():
                            if node_id in n.all_deps:
                                downstream.append(nid)
                        if downstream:
                            print(f"     ⚠️  {node_id} failed — downstream blocked: {downstream}")
                        else:
                            print(f"     ⚠️  {node_id} failed — leaf node, no downstream impact")
                    fixed_failures = [(l, n, e) for l, n, e in failed_nodes_per_level
                                      if not (l == level_idx_f and n == node_id)]
                    failed_nodes_per_level = fixed_failures

            # Merge level
            merge_ok = self.bridge.merge_level(level_idx)
            if not merge_ok:
                print(f"     ❌ Merge failed for level {level_idx}")
                self.state.mark_paused(f"Merge conflict at level {level_idx}")
                self.state.save(os.path.join(self.output_dir, "orchestration.md"))
                return {
                    "status": "paused",
                    "reason": f"Merge conflict at level {level_idx}",
                    "level": level_idx,
                }

            # Update state doc
            self.state.record_level_complete(level_idx, level_results)
            self.state.dag_pool_size = self.pool.compute_pool_size(level.width)
            self.state.save(os.path.join(self.output_dir, "orchestration.md"))

        # Phase 3: Finalize
        run_duration = (datetime.now() - run_start).total_seconds()
        final_branch = self.bridge.finalize_run()

        self.state.mark_complete()
        self.state.save(os.path.join(self.output_dir, "orchestration.md"))

        # Summary
        total_completed = sum(
            1 for lr in self._level_results.values()
            for r in lr if r["status"] == "completed"
        )
        total_failed = sum(
            1 for lr in self._level_results.values()
            for r in lr if r["status"] == "failed"
        )

        summary = {
            "status": "complete",
            "duration_seconds": run_duration,
            "total_nodes": len(self.graph.nodes),
            "total_levels": len(self.graph.levels),
            "completed_nodes": total_completed,
            "failed_nodes": total_failed,
            "final_branch": final_branch,
            "level_results": self._level_results,
            "pool_summary": self.bridge.summary if self.bridge else {},
        }

        self._print_summary(summary)
        return summary

    def _print_summary(self, summary: dict) -> None:
        """Print a human-readable run summary."""
        print(f"\n  ✅ DAG RUN COMPLETE")
        print(f"     Duration: {summary['duration_seconds']:.0f}s")
        print(f"     Nodes: {summary['total_nodes']} ({summary['completed_nodes']} completed, "
              f"{summary['failed_nodes']} failed)")
        print(f"     Levels: {summary['total_levels']}")
        print(f"     Final branch: {summary['final_branch']}")
        print()

        for level_idx, results in sorted(summary.get("level_results", {}).items()):
            completed = sum(1 for r in results if r["status"] == "completed")
            failed = sum(1 for r in results if r["status"] == "failed")
            node_list = ", ".join(f"{r['id']}({'✅' if r['status']=='completed' else '❌'})"
                                  for r in results)
            print(f"     Level {level_idx}: {completed}/{len(results)} — {node_list}")
