"""
DAG Induction — story parsing and LLM-based implicit dependency inference.

Flow for a given mode:
  minimal   → skip LLM pass entirely, use only explicit deps
  assisted  → LLM suggests edges, flagged with 'suggested: true'
  automatic → LLM adds edges immediately
"""

from __future__ import annotations

import json
from typing import Optional

from dag_core import DagGraph, InductionMode, DagNode


class DagInductor:
    """Induces a DAG from story data with configurable LLM assistance."""

    def __init__(self, graph: DagGraph):
        self.graph = graph
        self.mode = graph.mode

    def induct(self, stories: list[dict], architecture_context: str = "") -> DagGraph:
        """Full induction pipeline.

        1. Ingest stories into graph (already done if built via from_story_list)
        2. Run LLM pass for implicit deps (unless minimal)
        3. Apply edges according to mode
        4. Return graph ready for scheduling
        """
        if self.mode != InductionMode.MINIMAL:
            self._llm_inference_pass(stories, architecture_context)

        return self.graph

    def _llm_inference_pass(self, stories: list[dict], architecture_context: str) -> None:
        """Use an LLM to infer implicit dependencies between stories.

        This method is designed to be called either:
          A) By this agent (Hermes) — I perform the reasoning directly
          B) Via an external API — the format is a prompt + structured response

        The structured output for the LLM pass:

        ```json
        {
          "edges": [
            {"from": "epic-1.1", "to": "epic-1.3", "reasoning": "...", "confidence": "high|medium|low"},
            ...
          ]
        }
        ```
        """
        # Build the context for the reasoning step
        story_summaries = []
        for s in stories:
            provides = s.get("interfaces_provides", [])
            consumes = s.get("consumes_interfaces", [])
            files = s.get("file_scope", [])
            summary = (
                f"  - {s['id']}: \"{s.get('title', '')}\""
                + (f"  files: {files}" if files else "")
                + (f"  provides: {provides}" if provides else "")
                + (f"  consumes: {consumes}" if consumes else "")
            )
            story_summaries.append(summary)

        stories_text = chr(10).join(story_summaries)
        arch_text = ("Architecture context:\n" + architecture_context) if architecture_context else ""

        context = f"""Analyze these stories for structural dependencies.

Rules for identifying dependencies:
  - If story B consumes an interface type that story A provides → B depends on A
  - If story B modifies files in the same module as story A → likely sequential
  - If story A creates a data schema and story B reads/writes that schema → B depends on A
  - If stories touch completely independent modules with no shared types → no dependency
  - Architecture layers: core → domain → infrastructure → API → UI
    - A story in a downstream layer depends on upstream layers if it references them

Stories:
{stories_text}

{arch_text}

Output ONLY valid JSON:
{{
  "edges": [
    {{"from": "<story-id>", "to": "<story-id>", "reasoning": "why", "confidence": "high|medium|low"}}
  ]
}}

Rules:
  - from depends on to (from runs AFTER to completes)
  - Do NOT include edges that are already in the explicit dependencies
  - Be precise — only add edges when there's a genuine structural reason
  - confidence=high: same interface/file/variable dependency
  - confidence=medium: architectural layer dependency or shared module
  - confidence=low: speculative, e.g. "might need this later"
"""

        # Store the reasoning context for the orchestrator to use
        self._llm_context = context
        self._stories = stories
        self._architecture_context = architecture_context

    def get_llm_context(self) -> str:
        """Return the LLM prompt context for external processing."""
        return getattr(self, '_llm_context', "")

    def apply_llm_edges(self, llm_output: str) -> list[dict]:
        """Apply LLM-inferred edges according to the current mode.
        
        Args:
            llm_output: JSON string with edges array
            
        Returns:
            List of edge dicts applied (for reporting)
        """
        try:
            data = json.loads(llm_output)
        except json.JSONDecodeError as e:
            return [{"error": f"Failed to parse LLM output: {e}", "raw": llm_output[:500]}]

        edges = data.get("edges", [])
        applied = []

        for edge in edges:
            from_id = edge.get("from", "")
            to_id = edge.get("to", "")  # from depends on to
            reasoning = edge.get("reasoning", "")
            confidence = edge.get("confidence", "low")

            # Validate both nodes exist
            if from_id not in self.graph.nodes:
                applied.append({"from": from_id, "to": to_id, "status": "skipped", "reason": f"node '{from_id}' not in graph"})
                continue
            if to_id not in self.graph.nodes:
                applied.append({"from": from_id, "to": to_id, "status": "skipped", "reason": f"node '{to_id}' not in graph"})
                continue

            # Check it's not already an explicit dep
            if to_id in self.graph.nodes[from_id].explicit_deps:
                applied.append({"from": from_id, "to": to_id, "status": "skipped", "reason": "already explicit"})
                continue

            if self.mode == InductionMode.AUTOMATIC:
                # Add silently
                if to_id not in self.graph.nodes[from_id].implicit_deps:
                    self.graph.nodes[from_id].implicit_deps.append(to_id)
                applied.append({"from": from_id, "to": to_id, "status": "added", "confidence": confidence, "reasoning": reasoning})

            elif self.mode == InductionMode.ASSISTED:
                # Flag for review
                if to_id not in self.graph.nodes[from_id].suggested_deps:
                    self.graph.nodes[from_id].suggested_deps.append(to_id)
                applied.append({"from": from_id, "to": to_id, "status": "flagged", "confidence": confidence, "reasoning": reasoning})

        return applied

    def promote_suggested(self, node_id: str, dep_id: str) -> bool:
        """Promote a suggested dependency to an actual implicit dep (user approved)."""
        node = self.graph.nodes.get(node_id)
        if not node:
            return False
        if dep_id in node.suggested_deps:
            node.suggested_deps.remove(dep_id)
            if dep_id not in node.implicit_deps:
                node.implicit_deps.append(dep_id)
            return True
        return False

    def reject_suggested(self, node_id: str, dep_id: str) -> bool:
        """Reject a suggested dependency."""
        node = self.graph.nodes.get(node_id)
        if not node:
            return False
        if dep_id in node.suggested_deps:
            node.suggested_deps.remove(dep_id)
            return True
        return False
