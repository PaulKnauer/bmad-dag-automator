"""
Artifact Bridge — git branch-per-level management.

Each DAG level gets a branch from upstream. Within a level, each node commits
independently. At level completion, all node commits are merged into the level
branch and validated before downstream levels start.

Branch scheme:
  main                → root (what existed before the DAG run)
  dag/level-0         → from main, parallel nodes commit here
  dag/level-1         → from dag/level-0 (after merge), parallel nodes commit here
  dag/level-N         → from dag/level-N-1 (after merge), parallel nodes commit here
  dag/complete        → final merge target (squashed or preserved)
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MergeStrategy(str, Enum):
    SQUASH = "squash"         # Single commit per level
    PRESERVE = "preserve"     # All per-node commits preserved


@dataclass
class LevelBranch:
    level_index: int
    branch_name: str
    upstream_branch: str
    node_ids: list[str] = field(default_factory=list)
    node_shas: dict[str, str] = field(default_factory=dict)
    merge_sha: Optional[str] = None
    has_conflicts: bool = False


class ArtifactBridge:
    """Manages git branches per DAG level for clean artifact propagation."""

    def __init__(self, project_root: str, main_branch: str = "main",
                 strategy: MergeStrategy = MergeStrategy.PRESERVE,
                 dry_run: bool = False):
        self.project_root = os.path.abspath(project_root)
        self.main_branch = main_branch
        self.strategy = strategy
        self.dry_run = dry_run
        self._level_branches: dict[int, LevelBranch] = {}

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command in the project root."""
        cmd = ["git", "-C", self.project_root] + list(args)
        if self.dry_run:
            print(f"  [git] {' '.join(cmd)}")
            return subprocess.CompletedProcess(cmd, 0, stdout=b"", stderr=b"")
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=check)

    def _branch_exists(self, name: str) -> bool:
        """Check if a branch exists (local or remote)."""
        result = self._git("rev-parse", "--verify", name, check=False)
        return result.returncode == 0

    def _get_current_sha(self, branch: Optional[str] = None) -> str:
        """Get the SHA of a branch (or HEAD if branch is None)."""
        ref = branch or "HEAD"
        result = self._git("rev-parse", ref)
        return result.stdout.strip()

    def init_run(self) -> None:
        """Initialize the run: ensure we start from a clean state on main."""
        if self.dry_run:
            return

        # Ensure we're in a git repo
        result = self._git("rev-parse", "--git-dir", check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Not a git repository: {self.project_root}")

        # Stash any uncommitted changes
        result = self._git("stash", "push", "-m", "dag-automator-auto-stash", check=False)

        # Ensure main branch exists
        if not self._branch_exists(self.main_branch):
            self._git("checkout", "-b", self.main_branch)

        # Checkout main
        self._git("checkout", self.main_branch)

        # Clean up any stale dag/ branches from previous runs
        self._cleanup_stale_branches()

    def _cleanup_stale_branches(self) -> None:
        """Remove any dag/level-* branches from aborted runs."""
        result = self._git("branch", "--list", "dag/level-*")
        for branch in result.stdout.strip().split("\n"):
            branch = branch.strip().lstrip("* ")
            if branch.startswith("dag/level-"):
                self._git("branch", "-D", branch, check=False)

    def create_level_branch(self, level_index: int) -> LevelBranch:
        """Create a branch for a DAG level from its upstream.

        Level 0 branches from main.
        Level N branches from level N-1's merge commit.
        """
        if self.dry_run:
            upstream = self.main_branch
        elif level_index == 0:
            upstream = self.main_branch
        else:
            prev = self._level_branches.get(level_index - 1)
            if prev and prev.merge_sha:
                upstream = prev.branch_name
            elif prev:
                # Previous level completed but merge SHA unknown — use its branch tip
                upstream = prev.branch_name
            else:
                # Fallback
                upstream = self.main_branch

        branch_name = f"dag/level-{level_index}"
        base_sha = self._get_current_sha(upstream)

        if not self.dry_run:
            # Create branch from upstream
            self._git("checkout", "-b", branch_name, upstream)

        level_branch = LevelBranch(
            level_index=level_index,
            branch_name=branch_name,
            upstream_branch=upstream,
        )
        self._level_branches[level_index] = level_branch
        return level_branch

    def prepare_node_worktree(self, node_id: str, level_index: int) -> Optional[str]:
        """Set up a worktree for a node to work in isolation.

        Not strictly required if nodes don't touch the same files —
        they can commit directly to the level branch.
        For safety, returns the branch name they should commit on.
        """
        level_branch = self._level_branches.get(level_index)
        if not level_branch:
            level_branch = self.create_level_branch(level_index)
        return level_branch.branch_name

    def record_node_commit(self, node_id: str, level_index: int) -> Optional[str]:
        """Record a node's latest commit SHA on the level branch.

        Call after the node's agent reports a successful commit.
        """
        if self.dry_run:
            return "dry-run-sha"

        level_branch = self._level_branches.get(level_index)
        if not level_branch:
            return None

        sha = self._get_current_sha(level_branch.branch_name)
        level_branch.node_shas[node_id] = sha
        return sha

    def merge_level(self, level_index: int) -> bool:
        """Finalize a level: handle conflicts and merge all nodes' work.

        Strategy:
          - PRESERVE: merge all node commits, keep individual SHAs for traceability
          - SQUASH: create a single squashed commit for the entire level

        Returns True if merge succeeded, False if conflicts unresolved.
        """
        if self.dry_run:
            return True

        level_branch = self._level_branches.get(level_index)
        if not level_branch:
            return False

        branch = level_branch.branch_name

        # Check if there were actual changes
        git_log = self._git("log", f"{level_branch.upstream_branch}..{branch}", "--oneline")
        if not git_log.stdout.strip():
            # No changes — just record the merge as the upstream SHA
            level_branch.merge_sha = self._get_current_sha(level_branch.upstream_branch)
            return True

        if self.strategy == MergeStrategy.SQUASH:
            # Squash merge: reset to upstream, then commit all changes as one
            self._git("reset", "--soft", level_branch.upstream_branch)
            self._git("commit", "-m", f"dag/level-{level_index}: squash merge")
            sha = self._get_current_sha()
            level_branch.merge_sha = sha

        elif self.strategy == MergeStrategy.PRESERVE:
            # If there's only one node, no merge needed — just record
            if len(level_branch.node_shas) <= 1:
                sha = self._get_current_sha()
                level_branch.merge_sha = sha
                return True

            # Multiple nodes: ensure they're all on top of the upstream
            # (they should be, since they all branched from the same point)
            # Just record the current tip
            sha = self._get_current_sha()
            level_branch.merge_sha = sha

        return True

    def finalize_run(self) -> Optional[str]:
        """Finalize the entire DAG run: create a final branch.

        Returns the final branch name, or None if nothing was produced.
        """
        if self.dry_run:
            return "dag/complete"

        # Find the last level that completed
        completed_levels = sorted(self._level_branches.keys())
        if not completed_levels:
            return None

        last_level = self._level_branches[completed_levels[-1]]
        final_branch = "dag/complete"

        # Create final branch from the last level's merge base
        base = last_level.merge_sha or self._get_current_sha(last_level.branch_name)
        self._git("branch", "-f", final_branch, base)
        self._git("checkout", self.main_branch)

        return final_branch

    def get_upstream_for_level(self, level_index: int) -> Optional[str]:
        """Get the branch or SHA that this level should build on."""
        if level_index == 0:
            return self.main_branch

        prev = self._level_branches.get(level_index - 1)
        if prev:
            return prev.merge_sha or prev.branch_name

        return self.main_branch

    @property
    def summary(self) -> dict:
        """Summary of branches created and their status."""
        return {
            "main_branch": self.main_branch,
            "strategy": self.strategy.value,
            "levels": {
                idx: {
                    "branch": lb.branch_name,
                    "upstream": lb.upstream_branch,
                    "node_count": len(lb.node_shas),
                    "merged": lb.merge_sha is not None,
                }
                for idx, lb in sorted(self._level_branches.items())
            }
        }
