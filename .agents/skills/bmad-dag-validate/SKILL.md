---
name: bmad-dag-validate
description: "Validate DAG consistency and story YAML. Use when the user says 'validate dag', 'check dag consistency', or 'verify story yaml'."
---

# BMAD DAG Validate

## Overview

Validates DAG artifacts for consistency — checks that the state doc matches the DAG manifest, detects orphaned nodes, verifies level boundaries, and validates story YAML.

## Usage

```bash
cd {project-root}

# Validate story YAML (dangling refs, cycles)
python dag_scheduler.py validate examples/auth-system.yaml

# Validate DAG consistency from a prior run
python dag_scheduler.py validate-dag --project {project-root}

# Inspect full DAG internal state
python dag_scheduler.py inspect examples/auth-system.yaml
```

## Report Format

```
  ✅ DAG Validation: PASS
  ──────────────────────────────────────────────────
  PASS — 4 passed

  ✅ Manifest vs State Doc    · 8 nodes, 4 levels
  ✅ Orphaned Nodes           · All 8 completed nodes exist in manifest
  ✅ Node Existence           · All 8 node(s) resolved
  ✅ Level Boundaries         · Level 0: 2/2 ✅  Level 1: 2/2 ✅
```

Exit codes: 0 = PASS, 1 = FAIL, 2 = WARN.
