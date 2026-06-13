"""
Core DAG data structures and algorithms for the BMAD DAG Scheduler.

Provides:
  - DagNode, DagGraph, DagLevel
  - Kahn's algorithm for topological sort + level assignment
  - Critical path calculation (longest path)
  - Cycle detection
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GraphStatus(str, Enum):
    INIT = "init"
    VALIDATED = "validated"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    ABORTED = "aborted"


class InductionMode(str, Enum):
    MINIMAL = "minimal"
    ASSISTED = "assisted"
    AUTOMATIC = "automatic"


@dataclass
class DagNode:
    id: str
    title: str
    explicit_deps: list[str] = field(default_factory=list)
    implicit_deps: list[str] = field(default_factory=list)
    suggested_deps: list[str] = field(default_factory=list)  # assisted mode: flagged for review

    file_scope: list[str] = field(default_factory=list)
    interfaces_provides: list[str] = field(default_factory=list)
    consumes_interfaces: list[str] = field(default_factory=list)

    # Assigned by scheduler
    level: Optional[int] = None
    status: NodeStatus = NodeStatus.PENDING

    # Graph traversal (internal)
    _in_degree: int = 0
    _children: set[str] = field(default_factory=set)
    _distance: int = 0  # longest path distance from root

    @property
    def all_deps(self) -> list[str]:
        """All resolved dependencies (explicit + implicit, excluding suggestions)."""
        seen: set[str] = set()
        result: list[str] = []
        for dep in self.explicit_deps + self.implicit_deps:
            if dep not in seen:
                seen.add(dep)
                result.append(dep)
        return result

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "explicit_deps": self.explicit_deps,
            "implicit_deps": self.implicit_deps,
            "suggested_deps": self.suggested_deps if self.suggested_deps else None,
            "file_scope": self.file_scope or None,
            "interfaces_provides": self.interfaces_provides or None,
            "consumes_interfaces": self.consumes_interfaces or None,
            "level": self.level,
            "status": self.status.value,
        }


@dataclass
class DagLevel:
    index: int
    node_ids: list[str] = field(default_factory=list)

    @property
    def width(self) -> int:
        return len(self.node_ids)

    def to_dict(self) -> dict:
        return {"index": self.index, "width": self.width, "nodes": self.node_ids}


@dataclass
class DagGraph:
    mode: InductionMode = InductionMode.AUTOMATIC
    nodes: dict[str, DagNode] = field(default_factory=dict)
    levels: list[DagLevel] = field(default_factory=list)
    status: GraphStatus = GraphStatus.INIT
    critical_path: list[str] = field(default_factory=list)
    has_cycle: bool = False
    cycle_path: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def add_node(self, node: DagNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> DagNode:
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found in graph. Available: {list(self.nodes.keys())}")
        return self.nodes[node_id]

    def _build_adjacency(self) -> tuple[dict[str, set[str]], dict[str, int]]:
        """Build adjacency list and in-degree count from resolved edges."""
        adj: dict[str, set[str]] = {nid: set() for nid in self.nodes}
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}

        for node_id, node in self.nodes.items():
            for dep_id in node.all_deps:
                if dep_id in self.nodes:
                    adj[dep_id].add(node_id)   # dep -> dependent
                    in_degree[node_id] += 1
                # if dep_id not in graph, it's a dangling ref — skip and flag later

        return adj, in_degree

    def find_dangling_refs(self) -> list[str]:
        """Nodes referenced as deps but not in the graph."""
        all_refs = set()
        for node in self.nodes.values():
            all_refs.update(node.explicit_deps)
            all_refs.update(node.implicit_deps)
            all_refs.update(node.suggested_deps)
        return sorted(r for r in all_refs if r not in self.nodes)

    def detect_cycles(self) -> bool:
        """Kahn's algorithm — if not all nodes can be sorted, there's a cycle."""
        adj, in_degree = self._build_adjacency()

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        sorted_count = 0

        # For cycle path detection, track the order
        while queue:
            nid = queue.pop(0)
            sorted_count += 1
            for child in adj[nid]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if sorted_count < len(self.nodes):
            self.has_cycle = True
            # Nodes still with positive in_degree are in cycles
            remaining = [nid for nid, deg in in_degree.items() if deg > 0]
            self.cycle_path = remaining
            self.status = GraphStatus.ABORTED
            self.error = f"Cycle detected involving nodes: {remaining}"
            return True

        return False

    def topological_levels(self) -> list[DagLevel]:
        """Assign topological levels using Kahn's algorithm.
        Level 0 = root (no dependencies). Each pass = one level.
        """
        adj, in_degree = self._build_adjacency()

        levels: list[DagLevel] = []
        level_idx = 0

        # Track remaining in-degree per node (we'll mutate a copy)
        remaining_degree = dict(in_degree)

        # All roots = nodes with in_degree 0
        current_level = [nid for nid, deg in remaining_degree.items() if deg == 0]

        while current_level:
            dag_level = DagLevel(index=level_idx, node_ids=sorted(current_level))
            levels.append(dag_level)

            # Assign level to nodes
            for nid in current_level:
                self.nodes[nid].level = level_idx

            next_level: list[str] = []
            for nid in current_level:
                for child in adj[nid]:
                    remaining_degree[child] -= 1
                    if remaining_degree[child] == 0:
                        next_level.append(child)

            current_level = next_level
            level_idx += 1

        self.levels = levels
        self.status = GraphStatus.VALIDATED
        return levels

    def compute_critical_path(self) -> list[str]:
        """Longest path through the DAG (most levels, or widest if tie).
        Uses DP: distance of node = max(distance of all parents) + 1.
        """
        if not self.levels:
            self.topological_levels()

        # Topological order gives us a valid processing order
        # Process in topological order: for each node, update its children
        adj, _ = self._build_adjacency()

        # Get nodes in topological order (level 0 first)
        ordered = []
        for level in self.levels:
            for nid in level.node_ids:
                ordered.append(nid)

        dist: dict[str, int] = {nid: 0 for nid in ordered}
        parent: dict[str, Optional[str]] = {nid: None for nid in ordered}

        for nid in ordered:
            for child in adj[nid]:
                if dist[nid] + 1 > dist[child]:
                    dist[child] = dist[nid] + 1
                    parent[child] = nid

        # Find the node with the longest distance
        if not dist:
            self.critical_path = []
            return []

        farthest = max(dist, key=lambda k: dist[k])

        # Reconstruct path
        path: list[str] = []
        current: Optional[str] = farthest
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()

        self.critical_path = path
        return path

    def schedule(self) -> DagGraph:
        """Full scheduling pipeline: validate → levels → critical path."""
        # Step 1: Check for dangling refs
        dangling = self.find_dangling_refs()
        if dangling:
            self.error = f"Dangling dependency references: {dangling}"
            self.status = GraphStatus.ABORTED
            return self

        # Step 2: Cycle detection
        if self.detect_cycles():
            return self

        # Step 3: Topological levels
        self.topological_levels()

        # Step 4: Critical path
        self.compute_critical_path()

        return self

    def to_dict(self) -> dict:
        return {
            "dag": {
                "mode": self.mode.value,
                "status": self.status.value,
                "levels": [l.to_dict() for l in self.levels],
                "max_width": max((l.width for l in self.levels), default=0),
                "total_nodes": len(self.nodes),
                "total_levels": len(self.levels),
                "critical_path": self.critical_path or None,
                "has_cycle": self.has_cycle,
                "cycle_path": self.cycle_path or None,
                "error": self.error,
            },
            "nodes": {nid: n.to_dict() for nid, n in sorted(self.nodes.items())},
        }

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False, Dumper=yaml.SafeDumper)

    @staticmethod
    def from_story_list(stories: list[dict], mode: str = "automatic") -> DagGraph:
        """Build a DagGraph from a simple story list dict.
        
        Each story dict should have:
          - id: str
          - title: str
          - explicit_deps: list[str] (optional)
          - file_scope: list[str] (optional)
          - interfaces_provides: list[str] (optional)
          - consumes_interfaces: list[str] (optional)
        """
        graph = DagGraph(mode=InductionMode(mode))

        for story in stories:
            node = DagNode(
                id=story["id"],
                title=story.get("title", story["id"]),
                explicit_deps=story.get("explicit_deps", []),
                file_scope=story.get("file_scope", []),
                interfaces_provides=story.get("interfaces_provides", []),
                consumes_interfaces=story.get("consumes_interfaces", []),
            )
            graph.add_node(node)

        return graph
