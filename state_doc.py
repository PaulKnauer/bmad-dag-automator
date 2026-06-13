"""
State Document — extends the automator's markdown state doc format with DAG state.

The state doc serves as both machine-readable (YAML frontmatter) and
human-readable (markdown sections) control plane. Matches the existing
automator convention at _bmad-output/story-automator/orchestration.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DagRunStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXECUTION_COMPLETE = "EXECUTION_COMPLETE"
    COMPLETE = "COMPLETE"
    ABORTED = "ABORTED"


@dataclass
class DagStateDoc:
    """Represents the full state document for a DAG orchestrator run."""

    # Frontmatter fields
    epic: str = ""
    epic_name: str = ""
    status: DagRunStatus = DagRunStatus.INITIALIZING
    generated_at: str = ""
    last_updated: str = ""

    # DAG-specific frontmatter
    dag_enabled: bool = True
    dag_manifest_path: str = ""
    dag_current_level: int = 0
    dag_total_levels: int = 0
    dag_max_width: int = 0
    dag_pool_size: int = 0
    dag_status: str = "init"
    dag_critical_path: list[str] = field(default_factory=list)
    dag_mode: str = "automatic"

    # Execution tracking
    current_node: str = ""
    current_level: int = 0
    steps_completed: list[str] = field(default_factory=list)
    completed_nodes: list[dict] = field(default_factory=list)
    failed_nodes: list[dict] = field(default_factory=list)
    active_sessions: list[str] = field(default_factory=list)

    # Paths
    output_dir: str = ""

    # Agent config snapshot
    agent_config: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().isoformat()
        if not self.last_updated:
            self.last_updated = self.generated_at

    def update_timestamp(self) -> None:
        self.last_updated = datetime.now().isoformat()

    def to_frontmatter(self) -> dict:
        """Serialise frontmatter fields as a YAML-compatible dict."""
        return {
            "epic": self.epic,
            "epicName": self.epic_name,
            "status": self.status.value,
            "generatedAt": self.generated_at,
            "lastUpdated": self.last_updated,

            # DAG fields
            "dagEnabled": self.dag_enabled,
            "dagManifestPath": self.dag_manifest_path,
            "dagCurrentLevel": self.dag_current_level,
            "dagTotalLevels": self.dag_total_levels,
            "dagMaxWidth": self.dag_max_width,
            "dagPoolSize": self.dag_pool_size,
            "dagStatus": self.dag_status,
            "dagCriticalPath": self.dag_critical_path,
            "dagMode": self.dag_mode,

            # Execution tracking
            "currentNode": self.current_node,
            "currentLevel": self.current_level,
            "stepsCompleted": self.steps_completed,
            "completedNodes": self.completed_nodes,
            "failedNodes": self.failed_nodes,
            "activeSessions": self.active_sessions,

            # Paths
            "outputDir": self.output_dir,

            # Config snapshot
            "agentConfig": self.agent_config,
        }

    def to_markdown(self) -> str:
        """Render the full state document as markdown.

        Format matches automator convention:
          YAML frontmatter (machine-readable)
          Markdown body (human-readable)
        """
        self.update_timestamp()

        frontmatter = self.to_frontmatter()
        import yaml
        fm_yaml = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        # Build markdown body
        completed_ids = [n.get("id", "?") for n in self.completed_nodes]
        failed_ids = [n.get("id", "?") for n in self.failed_nodes]

        body = f"""# DAG Orchestration State

## Configuration
- **Mode:** {self.dag_mode}
- **Levels:** {self.dag_current_level + 1}/{self.dag_total_levels}
- **Max width:** {self.dag_max_width}
- **Pool size:** {self.dag_pool_size}
- **Status:** {self.status.value}
- **Critical path:** {' → '.join(self.dag_critical_path) if self.dag_critical_path else 'N/A'}

## Story Progress
- **Completed:** {len(self.completed_nodes)} — {', '.join(completed_ids) if completed_ids else 'none'}
- **Failed:** {len(self.failed_nodes)} — {', '.join(failed_ids) if failed_ids else 'none'}
- **Active sessions:** {len(self.active_sessions)}

## Recent Activity

| Timestamp | Level | Node | Action |
|-----------|-------|------|--------|
"""

        # Add last few steps
        for step in self.steps_completed[-20:]:
            body += f"| {step} |\n"

        body += f"""
## Next
- Level {self.dag_current_level}/{self.dag_total_levels - 1}
- Pending nodes: {len(self._pending_count())} stories remaining
"""

        return f"---\n{fm_yaml}---\n\n{body}"

    def _pending_count(self) -> list:
        return []

    def save(self, filepath: str) -> str:
        """Write the state document to disk.

        Args:
            filepath: Path to write to (directory or full path)
        Returns:
            Path that was written
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        content = self.to_markdown()
        with open(filepath, "w") as f:
            f.write(content)
        return filepath

    @staticmethod
    def from_manifest(manifest: dict, output_dir: str = "") -> "DagStateDoc":
        """Create a state document from a DAG manifest dict."""
        dag = manifest.get("dag", {})

        doc = DagStateDoc(
            status=DagRunStatus.READY,
            dag_enabled=True,
            dag_manifest_path=os.path.join(output_dir, "dag-manifest.yaml"),
            dag_current_level=0,
            dag_total_levels=dag.get("total_levels", 0),
            dag_max_width=dag.get("max_width", 0),
            dag_pool_size=dag.get("max_width", 0),
            dag_status="ready",
            dag_critical_path=dag.get("critical_path", []),
            dag_mode=dag.get("mode", "automatic"),
            output_dir=output_dir,
            generated_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
        )
        return doc

    def record_level_complete(self, level_index: int, results: list[dict]) -> None:
        """Record that a level completed."""
        self.current_level = level_index + 1
        self.steps_completed.append(
            f"{datetime.now().isoformat()} | Level {level_index} | — | Level completed"
        )
        for r in results:
            if r.get("status") == "completed":
                self.completed_nodes.append(r)
            elif r.get("status") == "failed":
                self.failed_nodes.append(r)

    def mark_aborted(self, reason: str) -> None:
        """Mark the run as aborted."""
        self.status = DagRunStatus.ABORTED
        self.dag_status = "aborted"
        self.steps_completed.append(
            f"{datetime.now().isoformat()} | — | — | ABORTED: {reason}"
        )

    def mark_complete(self) -> None:
        """Mark the run as complete."""
        self.status = DagRunStatus.COMPLETE
        self.dag_status = "complete"
        self.steps_completed.append(
            f"{datetime.now().isoformat()} | — | — | Run complete"
        )

    def mark_paused(self, reason: str) -> None:
        """Pause the run (e.g., for escalation)."""
        self.status = DagRunStatus.PAUSED
        self.dag_status = "paused"
        self.steps_completed.append(
            f"{datetime.now().isoformat()} | — | — | PAUSED: {reason}"
        )
