"""DAG Validator — consistency checks between DAG manifest, state doc, and graph.

Provides structured validation of a prior DAG run's artifacts, detecting:
  - Mismatches between state doc and manifest
  - Orphaned nodes from aborted runs
  - Missing node references in the graph
  - Broken level boundaries (downstream without upstream)
"""

from __future__ import annotations

import os
from typing import Any, Optional

import yaml

from state_doc import DagStateDoc


class DagValidator:
    """Validates consistency between DAG artifacts.

    Each ``validate_*`` method returns a check result dict:
      check: str
      status: "pass" | "fail" | "warn"
      details: list[str]
      errors: list[str]
    """

    def __init__(self) -> None:
        pass

    def validate_manifest_vs_state(
        self, manifest_path: str, state_path: str
    ) -> dict[str, Any]:
        """Check that the state doc's completed nodes match the manifest.

        Verifies total node counts match. Individual node presence is
        checked by ``validate_orphaned_nodes`` and ``validate_node_existence``.
        """
        result: dict[str, Any] = {
            "check": "Manifest vs State Doc",
            "status": "pass",
            "details": [],
            "errors": [],
        }

        # --- Load manifest ---
        manifest = self._load_manifest(manifest_path)
        if manifest is None:
            result["status"] = "fail"
            result["errors"].append("Cannot load DAG manifest")
            return result

        manifest_nodes = manifest.get("nodes", {})
        manifest_levels = manifest.get("dag", {}).get("levels", [])
        manifest_node_count = len(manifest_nodes)
        manifest_level_count = len(manifest_levels)

        result["details"].append(
            f"Manifest: {manifest_node_count} nodes, "
            f"{manifest_level_count} levels"
        )

        # --- Load state doc ---
        try:
            state = DagStateDoc.load(state_path)
        except (FileNotFoundError, ValueError) as e:
            result["status"] = "fail"
            result["errors"].append(f"Cannot load state doc: {e}")
            return result

        completed_count = len(state.completed_nodes)
        result["details"].append(
            f"State doc: {completed_count} completed nodes, "
            f"{state.dag_total_levels} total levels"
        )

        # --- Compare ---
        if manifest_level_count != state.dag_total_levels:
            result["status"] = "fail"
            result["errors"].append(
                f"Level count mismatch: manifest has {manifest_level_count}, "
                f"state doc has {state.dag_total_levels}"
            )

        if completed_count > manifest_node_count:
            result["status"] = "fail"
            result["errors"].append(
                f"State doc reports {completed_count} completed nodes, "
                f"but manifest only defines {manifest_node_count} nodes "
                f"— possible orphaned or duplicate entries"
            )

        if result["status"] == "pass":
            result["details"].append(
                f"Node count consistent: "
                f"{manifest_node_count} in manifest, "
                f"{completed_count} completed"
            )

        return result

    def validate_orphaned_nodes(
        self, manifest_path: str, state_path: str
    ) -> dict[str, Any]:
        """Detect completed nodes in the state doc not present in the manifest."""
        result: dict[str, Any] = {
            "check": "Orphaned Nodes",
            "status": "pass",
            "details": [],
            "errors": [],
        }

        manifest = self._load_manifest(manifest_path)
        if manifest is None:
            result["status"] = "warn"
            result["details"].append("Cannot check orphans without manifest")
            return result

        manifest_ids = set(manifest.get("nodes", {}).keys())

        try:
            state = DagStateDoc.load(state_path)
        except (FileNotFoundError, ValueError) as e:
            result["status"] = "warn"
            result["details"].append(f"Cannot check orphans: {e}")
            return result

        orphans = [
            cn.get("id", "?")
            for cn in state.completed_nodes
            if cn.get("id") not in manifest_ids
        ]

        if orphans:
            result["status"] = "fail"
            result["errors"].append(
                f"Orphaned node(s) not in manifest: {', '.join(orphans)}"
            )
        else:
            result["details"].append(
                f"All {len(state.completed_nodes)} completed nodes "
                f"exist in manifest"
            )

        return result

    def validate_node_existence(
        self, manifest_path: str
    ) -> dict[str, Any]:
        """Verify all node IDs referenced in manifest levels exist as keys.

        Checks that every node listed in a level's ``nodes`` array has
        a corresponding entry in the manifest's ``nodes`` dict.
        """
        result: dict[str, Any] = {
            "check": "Node Existence",
            "status": "pass",
            "details": [],
            "errors": [],
        }

        manifest = self._load_manifest(manifest_path)
        if manifest is None:
            result["status"] = "fail"
            result["errors"].append("Cannot load DAG manifest")
            return result

        manifest_ids = set(manifest.get("nodes", {}).keys())
        levels = manifest.get("dag", {}).get("levels", [])

        missing: list[str] = []
        for level in levels:
            for nid in level.get("nodes", []):
                if nid not in manifest_ids:
                    missing.append(nid)

        if missing:
            result["status"] = "fail"
            result["errors"].append(
                f"Node(s) missing from manifest data: {', '.join(sorted(set(missing)))}"
            )
        else:
            all_ids = sorted(manifest_ids)
            result["details"].append(
                f"All {len(all_ids)} node(s) resolved: {', '.join(all_ids)}"
            )

        return result

    def validate_level_boundaries(
        self, manifest_path: str, state_path: str
    ) -> dict[str, Any]:
        """Check that all upstream levels are fully completed.

        For each level with any completed node, verify that every level
        with a lower index has ALL its nodes completed.
        """
        result: dict[str, Any] = {
            "check": "Level Boundaries",
            "status": "pass",
            "details": [],
            "errors": [],
        }

        manifest = self._load_manifest(manifest_path)
        if manifest is None:
            result["status"] = "fail"
            result["errors"].append("Cannot load DAG manifest")
            return result

        levels = manifest.get("dag", {}).get("levels", [])
        if not levels:
            result["details"].append("No levels to validate")
            return result

        try:
            state = DagStateDoc.load(state_path)
        except (FileNotFoundError, ValueError) as e:
            result["status"] = "fail"
            result["errors"].append(f"Cannot load state doc: {e}")
            return result

        completed_ids = {
            cn.get("id")
            for cn in state.completed_nodes
        }

        for level_info in levels:
            level_idx = level_info.get("index", 0)
            level_nodes = level_info.get("nodes", [])
            all_completed = all(nid in completed_ids for nid in level_nodes)
            completed_in_level = sum(1 for nid in level_nodes if nid in completed_ids)

            if all_completed:
                result["details"].append(
                    f"Level {level_idx}: {completed_in_level}/{len(level_nodes)} ✅"
                )
            elif completed_in_level > 0:
                # Partial completion — check upstream
                missing = [nid for nid in level_nodes if nid not in completed_ids]
                result["status"] = "fail"
                result["errors"].append(
                    f"Level {level_idx}: {completed_in_level}/{len(level_nodes)} "
                    f"completed — missing: {', '.join(missing)}"
                )
            else:
                result["details"].append(
                    f"Level {level_idx}: 0/{len(level_nodes)} (not started)"
                )

        return result

    def validate_all(
        self, manifest_path: str, state_path: str
    ) -> dict[str, Any]:
        """Run all consistency checks and produce a structured report.

        Args:
            manifest_path: Path to dag-manifest.yaml.
            state_path: Path to orchestration.md state doc.

        Returns:
            Report dict with ``verdict``, ``checks`` list, and ``summary``.
        """
        checks = [
            self.validate_manifest_vs_state(manifest_path, state_path),
            self.validate_orphaned_nodes(manifest_path, state_path),
            self.validate_node_existence(manifest_path),
            self.validate_level_boundaries(manifest_path, state_path),
        ]

        fail_count = sum(1 for c in checks if c["status"] == "fail")
        warn_count = sum(1 for c in checks if c["status"] == "warn")

        if fail_count > 0:
            verdict = "FAIL"
        elif warn_count > 0:
            verdict = "WARN"
        else:
            verdict = "PASS"

        # Build summary
        pass_count = sum(1 for c in checks if c["status"] == "pass")
        summary_parts = [f"{pass_count} passed"]
        if fail_count:
            summary_parts.append(f"{fail_count} failed")
        if warn_count:
            summary_parts.append(f"{warn_count} warnings")

        report = {
            "verdict": verdict,
            "exit_code": 0 if verdict == "PASS" else (2 if verdict == "WARN" else 1),
            "checks": checks,
            "summary": f"{verdict} — {', '.join(summary_parts)}",
        }

        return report

    @staticmethod
    def _load_manifest(manifest_path: str) -> Optional[dict]:
        """Load a DAG manifest YAML file. Returns None on failure."""
        if not os.path.exists(manifest_path):
            return None
        try:
            with open(manifest_path) as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError):
            return None

    @staticmethod
    def print_report(report: dict[str, Any]) -> None:
        """Print a structured validation report to stdout."""
        verdict = report["verdict"]
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(verdict, "❓")

        print(f"\n  {icon} DAG Validation: {verdict}")
        print(f"  {'─' * 50}")
        print(f"  {report['summary']}")
        print()

        for check in report["checks"]:
            status_icon = {
                "pass": "✅", "fail": "❌", "warn": "⚠️"
            }.get(check["status"], "❓")
            print(f"  {status_icon} {check['check']}")

            for detail in check["details"]:
                print(f"     · {detail}")

            for error in check["errors"]:
                print(f"     ❗ {error}")

            print()

        print(f"  Exit code: {report['exit_code']}")
