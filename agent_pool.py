"""
Elastic Agent Pool — spawns and manages tmux child sessions per DAG node.

Reuses bmad-story-automator's tmux-wrapper pattern:
  - tmux-wrapper spawn  → create a detached tmux session per node
  - tmux-wrapper monitor  → poll session output for progress
  - tmux-wrapper kill     → clean up on abort

Pool size scales dynamically per DAG level: min(max_concurrent, level_width).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AgentStatus(str, Enum):
    PENDING = "pending"
    SPAWNING = "spawning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERING = "recovering"


class AgentTool(str, Enum):
    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    OPENCODE = "opencode"


@dataclass
class AgentConfig:
    """Per-node agent configuration."""
    tool: AgentTool = AgentTool.CLAUDE_CODE
    model: str = "sonnet"               # model alias/name
    max_retries: int = 2                # retries before fallback
    fallback_tool: Optional[AgentTool] = None
    fallback_model: Optional[str] = None
    max_review_cycles: int = 5          # adversary review cycles
    timeout_minutes: int = 30           # max wall-clock per node

    def to_dict(self) -> dict:
        return {
            "tool": self.tool.value,
            "model": self.model,
            "max_retries": self.max_retries,
            "fallback_tool": self.fallback_tool.value if self.fallback_tool else None,
            "fallback_model": self.fallback_model,
            "max_review_cycles": self.max_review_cycles,
            "timeout_minutes": self.timeout_minutes,
        }


@dataclass
class AgentResult:
    """Result from a single node's execution."""
    node_id: str
    status: AgentStatus
    session_id: Optional[str] = None
    exit_code: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output: str = ""
    commit_sha: Optional[str] = None
    modified_files: list[str] = field(default_factory=list)
    error: Optional[str] = None
    retry_count: int = 0
    fallback_used: bool = False

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class AgentPool:
    """Manages elastic scaling of agent sessions per DAG level.

    Pool size = min(max_concurrent, level_width), re-evaluated per level.
    """

    def __init__(self, project_root: str, max_concurrent: int = 4, dry_run: bool = False):
        self.project_root = os.path.abspath(project_root)
        self.max_concurrent = max_concurrent
        self.dry_run = dry_run
        self._active_sessions: dict[str, dict] = {}  # session_id -> info

    def compute_pool_size(self, level_width: int) -> int:
        """Elastic pool size = min(max_concurrent, level_width)."""
        return min(self.max_concurrent, level_width)

    def build_child_command(self, node_id: str, story_path: str,
                            config: AgentConfig, level_index: int,
                            upstream_branch: Optional[str] = None) -> list[str]:
        """Build the CLI command for a child agent session.

        Matches bmad-story-automator's tmux-wrapper build-cmd pattern:
          claude -p "Implement story X" --dangerously-skip-permissions
          --allowedTools Read,Edit,Bash --max-turns 30

        Or via BMAD skills:
          claude -p "Use bmad-dev-story skill for story X"
        """
        project = self.project_root

        # Build the context for the child agent
        context_parts = [
            f"Project: {project}",
            f"Level: {level_index}",
            f"Story: {story_path}",
        ]
        if upstream_branch:
            context_parts.append(f"Upstream branch: {upstream_branch}")

        context = ". ".join(context_parts)

        if config.tool == AgentTool.CLAUDE_CODE:
            return [
                "claude", "-p",
                f"Implement the story at {story_path} in {project}. "
                f"Use BMAD skills: bmad-dev-story, bmad-code-review. "
                f"{context}",
                "--dangerously-skip-permissions",
                "--allowedTools", "Read,Edit,Bash",
                "--max-turns", "30",
                "--output-format", "json",
            ]
        elif config.tool == AgentTool.CODEX:
            return [
                "codex", "exec",
                f"Implement story at {story_path}. {context}",
                "--full-auto",
            ]
        elif config.tool == AgentTool.OPENCODE:
            return [
                "opencode", "run",
                f"Implement story at {story_path}. {context}",
            ]
        else:
            raise ValueError(f"Unknown tool: {config.tool}")

    def spawn_node(self, node_id: str, story_path: str,
                   config: AgentConfig, level_index: int,
                   upstream_branch: Optional[str] = None) -> AgentResult:
        """Spawn a child agent session for one DAG node.

        Uses tmux (matching the automator's pattern):
          1. Create tmux session
          2. Run the child command inside it
          3. Return session tracking info

        In dry_run mode, just records what would happen.
        """
        if self.dry_run:
            session_id = f"dag-node-{node_id}-dry"
            return AgentResult(
                node_id=node_id,
                status=AgentStatus.RUNNING,
                session_id=session_id,
                started_at=datetime.now(),
            )

        cmd = self.build_child_command(
            node_id, story_path, config, level_index, upstream_branch
        )
        session_name = self._sanitize_session_name(f"dag-{node_id}")
        cmd_str = " ".join(cmd)
        script_path = f"/tmp/sa-cmd-{session_name}.sh"

        # Write command script (matching automator pattern)
        os.makedirs("/tmp", exist_ok=True)
        with open(script_path, "w") as f:
            f.write("#!/bin/bash\n")
            f.write(f"cd {self.project_root}\n")
            f.write(f"{cmd_str}\n")
        os.chmod(script_path, 0o755)

        # Create tmux session
        try:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session_name,
                 "-x", "140", "-y", "40", script_path],
                capture_output=True, text=True, timeout=10
            )
        except subprocess.CalledProcessError as e:
            return AgentResult(
                node_id=node_id,
                status=AgentStatus.FAILED,
                error=f"tmux spawn failed: {e.stderr.strip()}",
            )

        session_id = session_name
        self._active_sessions[session_id] = {
            "node_id": node_id,
            "started_at": datetime.now(),
            "config": config,
        }

        return AgentResult(
            node_id=node_id,
            status=AgentStatus.RUNNING,
            session_id=session_id,
            started_at=datetime.now(),
        )

    def poll_node(self, session_id: str) -> tuple[AgentStatus, str]:
        """Poll a tmux session for current status and output.

        Returns (status, output).

        Status logic:
          - Session exists + running process → RUNNING
          - Session exists + no process → COMPLETED or FAILED (check exit code)
          - Session doesn't exist → FAILED (crashed)
        """
        if self.dry_run:
            return AgentStatus.COMPLETED, "[dry-run]"

        # Check if tmux session exists
        result = subprocess.run(
            ["tmux", "has-session", "-t", session_id],
            capture_output=True, timeout=5
        )
        if result.returncode != 0:
            # Session died → check if it was already completed
            info = self._active_sessions.pop(session_id, None)
            if info and info.get("completed"):
                return AgentStatus.COMPLETED, info.get("output", "")
            return AgentStatus.FAILED, "tmux session not found (crashed)"

        # Capture pane output
        capture = subprocess.run(
            ["tmux", "capture-pane", "-t", session_id, "-p", "-S", "-100"],
            capture_output=True, text=True, timeout=5
        )
        output = capture.stdout or ""

        # Check if process is still running
        pgrep = subprocess.run(
            ["tmux", "list-panes", "-t", session_id, "-F", "#{pane_pid}"],
            capture_output=True, text=True, timeout=5
        )
        pane_pids = pgrep.stdout.strip().split("\n")

        # Default: still running
        return AgentStatus.RUNNING, output

    def wait_level(self, nodes: list[dict], config_map: dict[str, AgentConfig],
                   level_index: int, upstream_branch: Optional[str] = None,
                   poll_interval: int = 10, timeout_minutes: int = 30) -> list[AgentResult]:
        """Spawn all nodes in a level and wait for all to complete.

        Args:
            nodes: List of node dicts with id, specPath
            config_map: Per-node agent config
            level_index: Current DAG level
            upstream_branch: Branch name for upstream artifacts
            poll_interval: Seconds between polls
            timeout_minutes: Max wall-clock time for the level

        Returns:
            List of AgentResult (one per node)
        """
        pool_size = self.compute_pool_size(len(nodes))
        max_time = time.time() + (timeout_minutes * 60)

        # Spawn all nodes (they run in parallel, tmux handles concurrency)
        results: dict[str, AgentResult] = {}
        for node in nodes:
            nid = node["id"]
            spec = node.get("specPath", node.get("spec", ""))
            config = config_map.get(nid, AgentConfig())
            story_path = os.path.join(self.project_root, spec) if spec else self.project_root

            result = self.spawn_node(nid, story_path, config, level_index, upstream_branch)
            results[nid] = result

        print(f"  ⏳ Level {level_index}: spawned {len(results)} agents "
              f"(pool={pool_size}/{self.max_concurrent}, waiting up to {timeout_minutes}m)")

        # In dry-run mode, skip polling — all results are immediately complete
        if self.dry_run:
            completed = []
            for nid, result in results.items():
                result.status = AgentStatus.COMPLETED
                result.completed_at = datetime.now()
                result.exit_code = 0
                completed.append(result)
                print(f"    ✅ {nid} completed (dry-run)")
            return completed

        # Wait for all to complete
        pending = set(results.keys())
        completed: list[AgentResult] = []

        while pending and time.time() < max_time:
            time.sleep(poll_interval)
            still_pending: set[str] = set()

            for nid in pending:
                result = results[nid]
                if not result.session_id:
                    still_pending.add(nid)
                    continue

                status, output = self.poll_node(result.session_id)
                result.output = output

                if status == AgentStatus.COMPLETED:
                    result.status = AgentStatus.COMPLETED
                    result.completed_at = datetime.now()
                    result.exit_code = 0
                    completed.append(result)
                    print(f"    ✅ {nid} completed ({result.duration_seconds:.0f}s)")
                elif status == AgentStatus.FAILED:
                    result.status = AgentStatus.FAILED
                    result.completed_at = datetime.now()
                    result.error = output[-500:] if len(output) > 500 else output
                    completed.append(result)
                    print(f"    ❌ {nid} failed")
                else:
                    still_pending.add(nid)

            pending = still_pending

        # Timeout handling
        for nid in pending:
            result = results[nid]
            result.status = AgentStatus.FAILED
            result.error = f"Timed out after {timeout_minutes}m"
            result.completed_at = datetime.now()
            completed.append(result)
            print(f"    ⏰ {nid} timed out")
            self.kill_node(result.session_id)

        return completed

    def kill_node(self, session_id: Optional[str]) -> None:
        """Kill a tmux session."""
        if not session_id or self.dry_run:
            return
        subprocess.run(
            ["tmux", "kill-session", "-t", session_id],
            capture_output=True, timeout=5
        )
        self._active_sessions.pop(session_id, None)

    def kill_all(self) -> None:
        """Kill all active sessions."""
        for sid in list(self._active_sessions.keys()):
            self.kill_node(sid)

    @staticmethod
    def _sanitize_session_name(name: str) -> str:
        """Sanitize session name for tmux (alphanumeric, hyphens, dots only)."""
        return "".join(c if c.isalnum() or c in "-." else "-" for c in name)

    @property
    def active_count(self) -> int:
        return len(self._active_sessions)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.kill_all()
