# BMAD DAG Automator — Operations Guide

> **Audience:** Developers who know BMAD but are new to the DAG Automator.  
> **Example story set:** `examples/auth-system.yaml` — building a user authentication system across 8 stories.  
> **Project root:** [bmad-dag-automator](https://github.com/nousresearch/bmad-dag-automator)

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Story File Format](#story-file-format)
4. [CLI Reference](#cli-reference)
   - [validate](#validate--validate-story-yaml)
   - [schedule](#schedule--build-dag-and-schedule)
   - [inspect](#inspect--show-full-dag-internal-state)
   - [apply-llm](#apply-llm--apply-llm-edge-suggestions)
   - [orchestrate](#orchestrate--run-full-dag-orchestrator)
   - [validate-dag](#validate-dag--validate-dag-consistency)
5. [Running a DAG Orchestration](#running-a-dag-orchestration)
6. [Resuming After Interruption](#resuming-after-interruption)
7. [Validating Consistency](#validating-consistency)
8. [Interpreting Reports](#interpreting-reports)
9. [Handling Failures](#handling-failures)
10. [Edge Cases](#edge-cases)
11. [Benchmarking](#benchmarking)
12. [Architecture Overview](#architecture-overview)

---

## Overview

The BMAD DAG Automator extends BMAD with **topological dependency scheduling**, **elastic agent scaling**, and **production-hardened run management**. Instead of executing stories sequentially (one at a time, in arbitrary order), it:

1. **Parses** a story set into a DAG (Directed Acyclic Graph)
2. **Infers** implicit dependencies via interface analysis or LLM assistance
3. **Schedules** stories into parallelisable levels using Kahn's algorithm
4. **Executes** level-by-level, spawning one tmux agent session per story per level
5. **Merges** artifacts via git branch-per-level isolation
6. **Resumes** from the last incomplete level on interrupt

Three **induction modes** control how dependencies are discovered:

| Mode | LLM Pass | Deps Applied | Use Case |
|------|----------|--------------|----------|
| `minimal` | Skipped | Explicit only | Fast, deterministic, no LLM cost |
| `assisted` | Generated | Flagged for review | Human-in-the-loop validation |
| `automatic` | Generated | Applied directly | Fully autonomous, trust LLM |

---

## Installation

### Prerequisites

- Python 3.10+
- `tmux` (for live agent orchestration)
- `git` (for artifact branching)
- [BMAD](https://github.com/nousresearch/bmad) installed and configured
- An LLM provider (for `assisted`/`automatic` modes — Hermes, Claude, etc.)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/nousresearch/bmad-dag-automator.git
cd bmad-dag-automator

# 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install pyyaml

# 4. Verify it works
python dag_scheduler.py validate examples/auth-system.yaml
```

Expected output:
```
  ✅ 8 stories loaded
  ✅ No dangling references
  ✅ No cycles detected
  🔗 4 explicit dependency edges

  ✅ Stories file is valid
```

> **Note:** No `pip install` of the package itself — the CLI is run directly via `python dag_scheduler.py`. The project is designed as a single-module BMAD skill, not a PyPI package.

---

## Story File Format

Story definitions live in YAML files. Each story is a node in the DAG. Here is `examples/auth-system.yaml`:

```yaml
# Example: Building a User Authentication System

stories:
  - id: "epic-1.1"
    title: "User model with email and password_hash"
    explicit_deps: []
    file_scope: ["src/models/user.py"]
    interfaces_provides: ["User", "UserCreate", "UserResponse"]

  - id: "epic-1.2"
    title: "Password hashing and validation utility"
    explicit_deps: []
    file_scope: ["src/auth/hash.py", "src/auth/validation.py"]
    interfaces_provides: ["PasswordHasher", "PasswordValidator"]

  - id: "epic-1.3"
    title: "User registration API endpoint"
    explicit_deps: ["epic-1.1", "epic-1.2"]
    file_scope: ["src/api/register.py", "src/api/schemas.py"]
    consumes_interfaces: ["User", "UserCreate", "PasswordHasher"]
    interfaces_provides: ["RegisterHandler"]

  - id: "epic-1.4"
    title: "Login endpoint with JWT token generation"
    explicit_deps: ["epic-1.1"]
    file_scope: ["src/api/login.py", "src/auth/jwt.py"]
    consumes_interfaces: ["User", "UserResponse"]
    interfaces_provides: ["LoginHandler", "TokenService"]

  - id: "epic-1.5"
    title: "Session management and token refresh"
    explicit_deps: ["epic-1.4"]
    file_scope: ["src/auth/session.py"]
    consumes_interfaces: ["TokenService", "User"]
    interfaces_provides: ["SessionManager"]

  - id: "epic-2.1"
    title: "User profile read endpoint"
    explicit_deps: ["epic-1.1", "epic-1.4"]
    file_scope: ["src/api/profile.py"]
    consumes_interfaces: ["User", "UserResponse", "TokenService"]
    interfaces_provides: ["ProfileHandler"]

  - id: "epic-2.2"
    title: "Admin user management UI"
    explicit_deps: ["epic-2.1", "epic-1.3"]
    file_scope: ["src/admin/users.py", "src/admin/templates/users.html"]
    consumes_interfaces: ["User", "UserResponse", "ProfileHandler"]

  - id: "epic-2.3"
    title: "Email verification flow"
    explicit_deps: ["epic-1.3"]
    file_scope: ["src/api/verify.py", "src/auth/email.py"]
    consumes_interfaces: ["User", "RegisterHandler"]
    interfaces_provides: ["EmailVerifier", "VerificationHandler"]
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique story identifier (e.g., `epic-1.1`) |
| `title` | ✅ | Human-readable description |
| `explicit_deps` | ✅ | Array of story IDs this depends on (can be empty `[]`) |
| `file_scope` | Optional | Files this story owns/creates |
| `interfaces_provides` | Optional | Types, classes, or APIs this story exports |
| `consumes_interfaces` | Optional | Types, classes, or APIs this story imports |

The top-level key can be `stories:` (a list) or just a flat list. Both are accepted.

---

## CLI Reference

All commands are invoked via `dag_scheduler.py`. The global `--mode` flag sets induction mode (default: `automatic`).

### `validate` — Validate story YAML

Checks the story file for common structural issues without scheduling.

```bash
# Basic validation
python dag_scheduler.py validate examples/auth-system.yaml
```

**Example output:**
```
  ✅ 8 stories loaded
  ✅ No dangling references
  ✅ No cycles detected
  🔗 4 explicit dependency edges

  ✅ Stories file is valid
```

**Checks performed:**
- ✅ Stories parseable — valid YAML with required fields
- ✅ No dangling refs — all `explicit_deps` IDs exist as story IDs
- ✅ No cycles — Kahn's algorithm can topologically sort the graph

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | Valid — no errors |
| 1 | Invalid — cycles, dangling refs, or parsing errors |

**Bad input example:**
```yaml
# auth-system-bad.yaml — dangling ref to nonexistent story
stories:
  - id: "epic-1.1"
    title: "User model"
    explicit_deps: ["epic-9.9"]   # <-- epic-9.9 does not exist
```

Running validate:
```
  ✅ 1 stories loaded
  ⚠️  Dangling references: ['epic-9.9']
  ✅ No cycles detected
  🔗 1 explicit dependency edges
```

> **Key point:** Dangling refs warn but do not fail. Cycles fail hard. Use `--mode minimal` implicitly — validate always runs in minimal mode (no LLM inference).

---

### `schedule` — Build DAG and schedule

Builds the DAG from stories, computes levels via Kahn's algorithm, identifies the critical path, and writes a `dag-manifest.yaml`.

```bash
# Minimal mode — explicit deps only, no LLM
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Automatic mode — LLM infers implicit deps (requires LLM output)
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml --llm-output edges.json

# Assisted mode — LLM flags suggestions, human reviews
python dag_scheduler.py --mode assisted schedule examples/auth-system.yaml --llm-output edges.json

# Write manifest to custom path
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml -o custom-manifest.yaml
```

**Example output (minimal mode):**
```
  📋 Loaded 8 stories from examples/auth-system.yaml
  ⚙️  Mode: minimal
  🔗 Explicit edges: 4

  📊 DAG Schedule:
     Nodes: 8
     Levels: 5
     Max width: 2
     Critical path: epic-1.1 → epic-1.4 → epic-1.5 → epic-2.1 → epic-2.2

  📐 Level Breakdown:
     Level 0: ▓▓▓░░░░░  (2 agents)  [epic-1.1, epic-1.2]
     Level 1: ▓▓▓░░░░░  (2 agents)  [epic-1.3, epic-1.4]
     Level 2: ▓░░░░░░░  (1 agents)  [epic-1.5, epic-2.3]
     Level 3: ▓░░░░░░░  (1 agents)  [epic-2.1]
     Level 4: ▓░░░░░░░  (1 agents)  [epic-2.2]

  ✅ Manifest written to: dag-manifest.yaml
```

**What the DAG levels mean for the auth system:**

```
Level 0 (parallel — 2 agents):
  epic-1.1: User model           (no deps)
  epic-1.2: Password hashing     (no deps)

Level 1 (parallel — 2 agents):
  epic-1.3: Registration         (depends on epic-1.1 + epic-1.2)
  epic-1.4: Login + JWT          (depends on epic-1.1)

Level 2 (parallel — 2 agents):
  epic-1.5: Session mgmt         (depends on epic-1.4)
  epic-2.3: Email verification   (depends on epic-1.3)

Level 3 (serial — 1 agent):
  epic-2.1: Profile endpoint     (depends on epic-1.1 + epic-1.4)

Level 4 (serial — 1 agent):
  epic-2.2: Admin UI             (depends on epic-2.1 + epic-1.3)
```

**Critical path:** `epic-1.1 → epic-1.4 → epic-1.5 → epic-2.1 → epic-2.2` — the longest chain of dependencies. This path determines the minimum execution time regardless of parallelism.

**If LLM output is required but not provided:**
```
  🤖 LLM inference required for implicit dependencies.
  Mode: automatic

  --- LLM PROMPT ---
  Analyze these stories for structural dependencies.
  ... (LLM context with all story details) ...
  --- END PROMPT ---

  Run: python dag_scheduler.py apply-llm examples/auth-system.yaml < llm_output.json
  Or:  python dag_scheduler.py schedule examples/auth-system.yaml --llm-output <file>
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | Scheduled successfully |
| 1 | Error (cycle, dangling refs, etc.) |
| 2 | LLM output required but not provided |

---

### `inspect` — Show full DAG internal state

Dumps the complete DAG as YAML — every node, edge, level assignment, and status — without writing a file or running any execution.

```bash
python dag_scheduler.py inspect examples/auth-system.yaml
```

**Example output (truncated):**
```yaml
dag:
  mode: automatic
  status: validated
  levels:
  - index: 0
    width: 2
    nodes:
    - epic-1.1
    - epic-1.2
  # ... more levels ...
  max_width: 2
  total_nodes: 8
  total_levels: 5
  critical_path:
  - epic-1.1
  - epic-1.4
  - epic-1.5
  - epic-2.1
  - epic-2.2
  has_cycle: false
  error: null

nodes:
  epic-1.1:
    id: epic-1.1
    title: User model with email and password_hash
    explicit_deps: []
    implicit_deps: []
    level: 0
    status: pending
  # ... other nodes ...
```

Use this to debug scheduling decisions, verify node assignments, and trace dependency chains.

---

### `apply-llm` — Apply LLM edge suggestions

Feeds LLM-inferred dependency edges (from stdin) into the DAG. Two-step workflow for `assisted` or `automatic` modes.

```bash
# Step 1: Generate LLM prompt (via schedule, which prints it)
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml

# Step 2: Feed the LLM response back
cat llm_edges.json | python dag_scheduler.py apply-llm examples/auth-system.yaml
```

**Expected LLM input format:**
```json
{
  "edges": [
    {"from": "epic-1.3", "to": "epic-1.1", "reasoning": "registration needs User model", "confidence": "high"},
    {"from": "epic-1.3", "to": "epic-1.2", "reasoning": "registration needs password hashing", "confidence": "high"},
    {"from": "epic-2.3", "to": "epic-1.3", "reasoning": "email verification needs registration", "confidence": "medium"}
  ]
}
```

**Output:**
```
  LLM edges applied:
    Added (automatic): 2
    Flagged (assisted): 1

  📊 DAG Schedule:
     Levels: 5, Max width: 2
     Level 0: [epic-1.1, epic-1.2]
     Level 1: [epic-1.3, epic-1.4]
     Level 2: [epic-1.5, epic-2.3]
     Level 3: [epic-2.1]
     Level 4: [epic-2.2]

  ✅ Manifest written to: dag-manifest.yaml
```

**Edge application rules:**
- `from` depends on `to` (i.e., `from` runs AFTER `to` completes)
- Edges already present in `explicit_deps` are silently skipped
- Unknown node IDs are skipped with a warning
- In `automatic` mode: edges are added as `implicit_deps`
- In `assisted` mode: edges are added as `suggested_deps` (flagged for human review)
- Confidence `high/medium/low` is advisory only — all edges are applied equally within a mode

---

### `orchestrate` — Run full DAG orchestrator

The flagship command. Runs the complete pipeline: induction → agent spawning → level execution → artifact merging → finalization.

```bash
# Dry run (no tmux, no git) — validates the pipeline path
python dag_scheduler.py orchestrate examples/auth-system.yaml --dry-run

# Live run with claude-code (default agent)
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/your/project \
    --mode automatic \
    --agent claude-code \
    --model sonnet \
    --max-concurrent 4

# Live run with codex
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/your/project \
    --mode minimal \
    --agent codex \
    --max-concurrent 2

# With architecture context file
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . \
    --architecture project-context.md \
    --dry-run

# With pre-computed LLM edges
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . \
    --llm-output edges.json \
    --dry-run

# Resume from last incomplete level
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . --resume

# Resume with specific agent
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . --resume --agent opencode --model gpt-4
```

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `stories_file` | (required) | Path to YAML/JSON story file |
| `--project, -p` | `.` | Project root directory |
| `--architecture, -a` | None | Architecture context file (read for LLM prompts) |
| `--llm-output` | None | Pre-computed LLM edges JSON file |
| `--max-concurrent` | `4` | Maximum parallel agent sessions |
| `--agent` | `claude-code` | Agent tool: `claude-code`, `codex`, or `opencode` |
| `--model` | `sonnet` | Model identifier for the agent |
| `--dry-run` | False | Simulate without tmux or git operations |
| `--resume` | False | Resume from last incomplete level |
| `--mode` | `automatic` | Induction mode: `minimal`, `assisted`, `automatic` |

**Dry-run output:**
```
  🔄 Phase 1: DAG Induction (mode=minimal)
     8 stories, 4 explicit edges
     Skipping LLM pass (minimal mode)
     ✅ 5 levels, max width 2, critical path: epic-1.1 → epic-1.4 → epic-1.5 → epic-2.1 → epic-2.2

  🔄 Phase 2: Level-by-level execution
  📐 Level 0: 2 node(s)
    ⏳ Level 0: spawned 2 agents (pool=2/4, waiting up to 30m)
    ✅ epic-1.1 completed (dry-run)
    ✅ epic-1.2 completed (dry-run)
  📐 Level 1: 2 node(s)
    ⏳ Level 1: spawned 2 agents (pool=2/4, waiting up to 30m)
    ✅ epic-1.3 completed (dry-run)
    ✅ epic-1.4 completed (dry-run)
  ...

  ✅ DAG RUN COMPLETE
     Duration: 0s
     Nodes: 8 (8 completed, 0 failed)
     Levels: 5
     Final branch: dag/complete
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | Run completed successfully |
| 1 | Error (induction failure, git init failure, etc.) |
| 2 | Paused (interrupted, merge conflict — can resume) |

---

### `validate-dag` — Validate DAG consistency

Post-run validation. Checks that the artifacts from a prior orchestration are consistent — manifest matches state doc, no orphaned nodes, all references resolve, level boundaries are sound.

```bash
# Validate artifacts in default project location
python dag_scheduler.py validate-dag --project /path/to/project

# Validate from current directory
python dag_scheduler.py validate-dag
```

**Artifact layout expected:**
```
/path/to/project/
  _bmad-output/
    dag-automator/
      dag-manifest.yaml       # Produced by schedule/orchestrate
      orchestration.md        # State document (produced by orchestrator)
```

**Example output:**
```
  ✅ DAG Validation: PASS
  ──────────────────────────────────────────────────
  PASS — 4 passed

  ✅ Manifest vs State Doc
     · Manifest: 8 nodes, 5 levels
     · State doc: 8 completed nodes, 5 total levels
     · Node count consistent: 8 in manifest, 8 completed

  ✅ Orphaned Nodes
     · All 8 completed nodes exist in manifest

  ✅ Node Existence
     · All 8 node(s) resolved: epic-1.1, epic-1.2, epic-1.3, epic-1.4, epic-1.5, epic-2.1, epic-2.2, epic-2.3

  ✅ Level Boundaries
     · Level 0: 2/2 ✅
     · Level 1: 2/2 ✅
     · Level 2: 2/2 ✅
     · Level 3: 1/1 ✅
     · Level 4: 1/1 ✅

  Exit code: 0
```

**Four validation checks performed:**

| Check | What It Detects |
|-------|----------------|
| **Manifest vs State Doc** | Node and level count mismatches between `dag-manifest.yaml` and `orchestration.md` |
| **Orphaned Nodes** | Completed nodes in the state doc missing from the manifest (possible corruption) |
| **Node Existence** | Every node ID in manifest levels resolves to a key in the nodes dict |
| **Level Boundaries** | No downstream level has completed nodes before all upstream levels completed |

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | PASS — all checks pass |
| 1 | FAIL — one or more checks fail |
| 2 | WARN — warnings only (e.g., missing files) |

---

## Running a DAG Orchestration

### Step-by-Step: Auth System Sprint

Here is the full workflow from zero to completed run.

**1. Validate the story set**
```bash
python dag_scheduler.py validate examples/auth-system.yaml
# → 8 stories, no cycles, 4 explicit edges
```

**2. (Optional) Schedule and inspect**
```bash
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml
# Review the level breakdown and critical path

python dag_scheduler.py inspect examples/auth-system.yaml
# Deep-dive into node-level details
```

**3. Dry run the orchestrator**
```bash
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /tmp/auth-system-demo \
    --mode minimal \
    --dry-run
```

**4. Live orchestration**

Before running live, ensure your project directory is a git repository with a `main` branch:

```bash
cd /path/to/your/project
git init
git checkout -b main
git add .
git commit -m "initial state"
```

Then run:

```bash
python /path/to/dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/your/project \
    --mode minimal \
    --agent claude-code \
    --model sonnet \
    --max-concurrent 4
```

**What happens during a live run:**

1. **Phase 1 — Induction:** Stories are loaded, DAG is built, levels are computed.
2. **Manifest written** to `_bmad-output/dag-automator/dag-manifest.yaml`.
3. **State doc initialized** at `_bmad-output/dag-automator/orchestration.md`.
4. **Git init:** Branches from `main`, cleans up any stale `dag/level-*` branches.
5. **Level loop:**
   - Level 0: `create_level_branch(dag/level-0)` from `main`
   - Spawn **2 tmux sessions** (epic-1.1, epic-1.2) — parallel agents
   - Poll every 10 seconds until both complete or 30-min timeout
   - Record node commits, merge level into branch
   - Level 1: Branch from `dag/level-0`, spawn epic-1.3 + epic-1.4
   - ... continues through all 5 levels ...
6. **Finalize:** Create `dag/complete` branch, switch back to `main`.
7. **Summary printed.**

### Agent Configuration Per Node

The default `AgentConfig` used for every node:

| Field | Default | Notes |
|-------|---------|-------|
| `tool` | `claude-code` | Also supported: `codex`, `opencode` |
| `model` | `sonnet` | Passed as model alias to the agent tool |
| `max_retries` | `2` | Number of retry attempts before fallback |
| `fallback_tool` | `None` | Alternative tool if primary fails repeatedly |
| `fallback_model` | `None` | Alternative model for fallback |
| `timeout_minutes` | `30` | Max wall-clock time per node |

---

## Resuming After Interruption

### The Problem

DAG orchestration can take hours. If the process is interrupted (Ctrl+C, network failure, system crash), you want to pick up where you left off — not rebuild from level 0.

### How Resume Works

1. **On interrupt** (SIGINT), the orchestrator:
   - Captures the signal via a `SIGINT` handler
   - Saves the state doc with `PAUSED` status
   - Prints the resume command to stdout
   - Exits with code 130

2. **On resume** (`--resume` flag), the orchestrator:
   - Loads the prior `orchestration.md` state doc
   - Loads the prior `dag-manifest.yaml`
   - **Validates consistency** — same number of nodes, same number of levels
   - Skips completed levels
   - Starts execution at the first incomplete level

### Resume Workflow

```bash
# Start a run
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . --mode minimal

# ... run completes Level 0 and Level 1 ...
# User presses Ctrl+C during Level 2

Output:
  ⏹️  Interrupted (SIGINT). Saving state...
  💾 State saved to ./_bmad-output/dag-automator/orchestration.md
  ℹ️  Resume later with: --resume

# Later, resume:
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project . --mode minimal --resume

Output:
  ⏯️  Resuming from Level 2
  ⏭️  Level 0: skipped (completed in prior run)
  ⏭️  Level 1: skipped (completed in prior run)
  📐 Level 2: 2 node(s)
  ...
```

### Resume Detection Logic

The method `_find_resume_point()` in `dag_orchestrator.py`:

1. **Loads state doc** — if missing: `FileNotFoundError` → starts fresh with warning
2. **Loads prior manifest** — if missing: `FileNotFoundError` → cannot resume
3. **Compares node counts** — mismatch: `ValueError("Story count mismatch...")` → starts fresh
4. **Compares level counts** — mismatch: `ValueError("Level structure changed...")` → starts fresh
5. **Scans levels in order** — first level where NOT ALL nodes are completed = resume point
6. **All levels complete** → returns `None` → "Prior run already complete — nothing to do"

### Resume Safety Guardrails

| Condition | Behaviour |
|-----------|-----------|
| State doc missing | Warning + fresh start from level 0 |
| Manifest missing | Warning + fresh start from level 0 |
| More/fewer nodes than prior run | Error message + fresh start |
| Different level structure | Error message + fresh start |
| Run was already complete | Graceful message, exit 0 |
| Prior run status is PAUSED | Normal resume from first incomplete level |

---

## Validating Consistency

### When to Validate

- **After a completed run** — confirm all artifacts are consistent
- **Before resume** — optional, but the resume logic does an implicit check
- **After manual intervention** — if you edited `orchestration.md` or `dag-manifest.yaml`
- **As a CI gate** — validate artifacts before deployment

### Manual Validation

```bash
python dag_scheduler.py validate-dag --project /path/to/project
```

### What Each Check Does

#### 1. Manifest vs State Doc
Loads both files, compares total node count and level count. Fails if:
- State doc reports more completed nodes than the manifest defines
- Level counts differ

#### 2. Orphaned Nodes
Scans the state doc's `completedNodes` list. If any completed node ID does not exist in the manifest's `nodes` dict, it's flagged as an orphan. This catches:
- Corruption from aborted writes
- Manual editing errors
- Version mismatches

#### 3. Node Existence
For every node ID listed in a manifest level's `nodes` array, confirms there is a corresponding key in the manifest's `nodes` dict. This is a structural integrity check — a valid manifest should always pass this.

#### 4. Level Boundaries
For each level, checks if all its nodes are completed. If a level has partial completion (some nodes done, some not), it fails — this means the run was interrupted mid-level and DAG integrity was violated. All upstream levels must be fully complete before any downstream node runs.

### Programmatic Validation Reports

The `DagValidator` class returns structured reports:

```python
from dag_validator import DagValidator

v = DagValidator()
report = v.validate_all("dag-manifest.yaml", "orchestration.md")
# report = {
#     "verdict": "PASS" | "FAIL" | "WARN",
#     "exit_code": 0 | 1 | 2,
#     "checks": [
#         {"check": "Manifest vs State Doc", "status": "pass", "details": [...], "errors": [...]},
#         ...
#     ],
#     "summary": "PASS — 4 passed",
# }
```

---

## Interpreting Reports

### Orchestration Run Summary

At the end of a run, the orchestrator prints:

```
  ✅ DAG RUN COMPLETE
     Duration: 1247s
     Nodes: 8 (8 completed, 0 failed)
     Levels: 5
     Final branch: dag/complete

     Level 0: 2/2 — epic-1.1(✅), epic-1.2(✅)
     Level 1: 2/2 — epic-1.3(✅), epic-1.4(✅)
     Level 2: 2/2 — epic-1.5(✅), epic-2.3(✅)
     Level 3: 1/1 — epic-2.1(✅)
     Level 4: 1/1 — epic-2.2(✅)
```

**Reading the summary:**
- **Duration** — real wall-clock time for the full run
- **Nodes completed/failed** — at-a-glance health
- **Level-by-level** — which nodes passed (✅) or failed (❌) each level
- **Final branch** — `dag/complete` contains the merged output of all levels

### State Document (`orchestration.md`)

The state doc serves as the **source of truth** for the run. It's both machine-readable (YAML frontmatter) and human-readable (Markdown body).

**Frontmatter (machine):**
```yaml
epic: bmad-dag-automator
epicName: "Auth System Sprint"
status: COMPLETE
generatedAt: "2026-06-23T20:00:00Z"
lastUpdated: "2026-06-23T20:21:00Z"
dagEnabled: true
dagManifestPath: _bmad-output/dag-automator/dag-manifest.yaml
dagCurrentLevel: 5
dagTotalLevels: 5
dagMaxWidth: 2
dagPoolSize: 2
dagStatus: complete
dagCriticalPath: ["epic-1.1", "epic-1.4", "epic-1.5", "epic-2.1", "epic-2.2"]
dagMode: minimal
completedNodes:
  - id: epic-1.1
    status: completed
    ...
failedNodes: []
```

**Body (human):**
```markdown
## Configuration
- Mode: minimal
- Levels: 5/5
- Max width: 2
- Status: COMPLETE
- Critical path: epic-1.1 → epic-1.4 → epic-1.5 → epic-2.1 → epic-2.2

## Story Progress
- Completed: 8 — epic-1.1, epic-1.2, epic-1.3, epic-1.4, ...
- Failed: 0 — none

## Recent Activity
| Timestamp | Level | Node | Action |
...
```

### Manifest (`dag-manifest.yaml`)

Contains the full DAG definition: node metadata, level assignments, critical path. This is the **blueprint** that drove the run. Comparing it to the state doc validates consistency.

### Reading Failure Reports

When nodes fail:

```
  ✅ DAG RUN COMPLETE
     Duration: 893s
     Nodes: 8 (7 completed, 1 failed)
     Levels: 5
     Final branch: dag/complete

     Level 0: 2/2 — epic-1.1(✅), epic-1.2(✅)
     Level 1: 2/2 — epic-1.3(✅), epic-1.4(✅)
     Level 2: 1/2 — epic-1.5(✅), epic-2.3(❌)
     Level 3: 1/1 — epic-2.1(✅)
     Level 4: 1/1 — epic-2.2(✅)

     ⚠️  epic-2.3 failed — leaf node, no downstream impact
```

The orchestrator logs downstream impact for every failure:
- "leaf node, no downstream impact" — safe to continue
- "downstream blocked: [epic-3.1, epic-3.2]" — downstream stories are affected

---

## Handling Failures

### Failure Types and Responses

| Failure | Detection | Response |
|---------|-----------|----------|
| **Story YAML parse error** | `validate` | Exit code 1 with descriptive error |
| **Dangling dependency ref** | `validate` / `schedule` | Warning (validate) or error (schedule) |
| **Cycle in graph** | `schedule` | Error with cycle path listed |
| **tmux not found** | `orchestrate` live run | Agent returns `FAILED` with "tmux not found" |
| **Node timeout** | AgentPool poll loop | Agent marked FAILED after 30m, session killed |
| **Node failure** | AgentPool `wait_level` | Recorded in state doc, downstream flagged |
| **Merge conflict** | ArtifactBridge merge | State doc paused, can resume after resolution |
| **Git not a repository** | Orchestrator init | RuntimeError, run aborted |
| **SIGINT (Ctrl+C)** | Signal handler | State saved as PAUSED, resume command printed |
| **Level structure changed on resume** | `_find_resume_point` | Warning + fresh start |
| **Story count changed on resume** | `_find_resume_point` | Warning + fresh start |

### Failure Propagation in the DAG

```
epic-1.1 ──→ epic-1.3 ──→ epic-2.2
  │            │
  │            └──→ epic-2.3
  │
  └──→ epic-1.4 ──→ epic-1.5
       │
       └──→ epic-2.1 ──→ epic-2.2
```

If `epic-1.4` (Login + JWT) fails:
- Direct downstream: `epic-1.5`, `epic-2.1` (blocked)
- Indirect downstream: `epic-2.2` (blocked via epic-2.1)
- Not affected: `epic-2.3` (depends on epic-1.3, not epic-1.4)

The orchestrator prints: `⚠️  epic-1.4 failed — downstream blocked: epic-1.5, epic-2.1`

### Failure Recovery Strategies

1. **Retry the level:** Fix the issue (missing import, config error) and resume:
   ```bash
   python dag_scheduler.py orchestrate examples/auth-system.yaml --project . --resume
   ```

2. **Manual fix + resume:** Apply a hotfix directly, then resume. The resume logic skips completed levels and re-attempts the failed level.

3. **Abort and restart:** Clean up stale branches and start fresh:
   ```bash
   git branch -D dag/level-*
   python dag_scheduler.py orchestrate examples/auth-system.yaml --project . --mode minimal
   ```

4. **Skip the failed node:** If the failed node is a leaf (no downstream dependents), the orchestrator already logs this and continues. No manual action needed for downstream integrity.

### SIGINT Handling

When you press Ctrl+C during a live run:

```
  ⏹️  Interrupted (SIGINT). Saving state...
  💾 State saved to ./_bmad-output/dag-automator/orchestration.md
  ℹ️  Resume later with: --resume
```

The state doc is saved with status `PAUSED`. Any running tmux sessions are left running — they are NOT killed. This allows you to:
- Inspect what the agents were doing
- Let them finish externally
- Then resume with confidence

---

## Edge Cases

### Empty Story List

```yaml
stories: []
```

```
  📋 Loaded 0 stories from empty.yaml
  ⚙️  Mode: minimal
     ⚠️  No stories to process — nothing to do
```

Returned as "complete" immediately. No files written, no git operations.

### Single-Story Sprint

```yaml
stories:
  - id: "S1"
    title: "Fix login bug"
    explicit_deps: []
```

```
  📊 DAG Schedule:
     Nodes: 1
     Levels: 1
     Max width: 1
     Critical path: S1
```

One level, one node, no overhead. The orchestrator skips parallel pooling and runs a single agent.

### Deep DAG (50+ Levels)

A serial chain of 52 nodes produces 52 levels, each with width 1. Kahn's algorithm handles this without recursion depth issues. The critical path spans all 52 nodes.

**Benchmark:** Scheduling a 52-node serial chain completes in ~0.1ms.

### Self-Referencing Dependency

```yaml
stories:
  - id: "loop"
    title: "Depends on itself"
    explicit_deps: ["loop"]
```

`schedule` output:
```
  ❌ Cycle detected at nodes: ['loop']
```

Kahn's algorithm catches this correctly — the node never reaches in-degree 0.

### tmux Not Installed

```
  ❌ epic-1.1 failed
     Error: tmux not found — is tmux installed?
```

The `spawn_node` method catches `FileNotFoundError` and returns `AgentResult(status=FAILED, error="tmux not found — is tmux installed?")`.

### Git Worktree Conflicts

The `artifact_bridge.py` module handles this through branch isolation:
- Each level gets its own branch (`dag/level-N`)
- Multiple nodes within a level commit independently to the same branch
- If two nodes modify the same file, the merge step detects conflicts and pauses the run
- Resolution: fix conflicts manually, then resume

### Graceful Shutdown on Interrupt

The `SIGINT` handler in `run_dag()`:
1. Saves state doc with `PAUSED` status
2. Does NOT kill active tmux sessions (allows external management)
3. Prints the resume command
4. Exits with code 130

---

## Benchmarking

### Running Benchmarks

```bash
cd /path/to/bmad-dag-automator
python benchmarks/bench_dag.py
```

### Benchmark Shapes

Four DAG topologies measure different scheduling characteristics:

| Shape | Nodes | Levels | Width | Description |
|-------|-------|--------|-------|-------------|
| **Serial Chain** | 10 | 10 | 1 | N0 → N1 → ... → N9 — worst case for parallelisation |
| **Full Parallel** | 10 | 1 | 10 | All independent — best case for parallelisation |
| **Fan-out/fan-in** | 7 | 3 | 5 | Root → 5 children → merge leaf |
| **Mixed** | 8 | 5 | 2 | Varying widths, representative of real projects |

### Sample Output

```
  DAG Scheduling Benchmarks
  ========================================================================

  Shape                Nodes  Lvls  Width  Sched   Serial  Par  Speed  Util
  ──────────────────── ───── ──── ─────── ─────── ─────── ──── ────── ─────
  Serial Chain            10   10      1   0.10ms    10     1  10.0x  100%
  Full Parallel           10    1     10   0.04ms    10    10   1.0x  100%
  Fan-out/fan-in           7    3      5   0.05ms     7     5   1.4x  100%
  Mixed                    8    5      2   0.05ms     8     2   4.0x  100%

  ────────────────────────────────────────────────────────────────────────
  Scheduling overhead: 0.24ms total (35 nodes across 4 shapes)
```

### Interpreting Benchmark Results

| Metric | What It Measures |
|--------|-----------------|
| **Sched** | Time to run Kahn's algorithm + critical path (pure overhead) |
| **Serial** | Abstract serial work units (nodes) |
| **Par** | Abstract parallel work units (max width = min completion time) |
| **Speed** | Theoretical speedup: serial / parallel (higher = more benefit from parallelisation) |
| **Util** | Agent utilisation: percentage of agent slots that are occupied each level |

**Key insights:**
- Scheduling overhead is sub-millisecond even for complex DAGs
- Serial chains get the most benefit from DAG scheduling (10x speedup for 10 nodes) because they expose the dependency structure
- Full parallel DAGs show 1.0x speedup because they cannot be parallelised further
- The **Mixed** shape (4x speedup) is most representative of real projects

### Running Benchmark Tests

```bash
python tests/test_benchmarks.py
```

This runs 6 benchmark harness tests that verify:
- All 4 shapes produce correct level counts
- Critical path lengths are accurate
- Serial/parallel unit calculations are correct

---

## Architecture Overview

```
dag_scheduler.py          ← CLI entry point (argparse)
       │
       ├── dag_core.py    ← DagGraph, DagNode, DagLevel, Kahn's algorithm
       │                       NodeStatus, GraphStatus, InductionMode enums
       │
       ├── dag_induction.py  ← DagInductor — LLM inference for implicit deps
       │
       ├── dag_orchestrator.py  ← DagOrchestrator — main execution loop
       │       │
       │       ├── agent_pool.py    ← AgentPool — tmux session management
       │       ├── artifact_bridge.py ← ArtifactBridge — git branch-per-level
       │       └── state_doc.py     ← DagStateDoc — markdown state document
       │
       ├── dag_validator.py  ← DagValidator — post-run consistency checks
       │
       └── benchmarks/
              └── bench_dag.py  ← Performance measurement harness
```

### File Layout

```
_bmad-output/dag-automator/
├── dag-manifest.yaml        # DAG blueprint (nodes, levels, critical path)
└── orchestration.md         # State document (YAML frontmatter + markdown body)
```

### Git Branch Scheme

```
main                    ── root (input state)
  └── dag/level-0       ── from main, Level 0 nodes commit here
       └── dag/level-1  ── from dag/level-0, Level 1 nodes commit here
            └── ...     ── chain continues
                 └── dag/level-N
                      └── dag/complete  ── final merged output
```

### Lifecycle

1. **Induct:** Stories → DagGraph → Kahn's algorithm → levels + critical path
2. **Execute:** Level loop → branch creation → parallel agent spawning → polling → merge
3. **Finalize:** Create `dag/complete` branch, print summary
4. **Validate (post-run):** Check manifest vs state doc consistency

### Test Suite

Run all tests to verify your installation:

```bash
for t in tests/test_*.py; do python "$t"; done
```

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_dag_core.py` | 17 | Core algorithms (Kahn's, cycles, critical path) |
| `test_resume.py` | 8 | Resume from any level, mismatch detection, state doc round-trip |
| `test_validator.py` | 9 | All 4 validation checks + edge cases |
| `test_failure_modes.py` | 12 | Failure injection, retry, downstream blocking, edge cases |
| `test_benchmarks.py` | 6 | Benchmark harness correctness |
| `test_dry_run.py` | — | Dry-run orchestrator path |

---

## Quick Reference Card

```bash
# Validate
python dag_scheduler.py validate examples/auth-system.yaml

# Schedule (minimal — no LLM)
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Schedule (automatic — needs LLM output)
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml --llm-output edges.json

# Inspect DAG
python dag_scheduler.py inspect examples/auth-system.yaml

# Apply LLM edges
cat edges.json | python dag_scheduler.py apply-llm examples/auth-system.yaml

# Dry-run orchestrate
python dag_scheduler.py orchestrate examples/auth-system.yaml --dry-run

# Live orchestrate
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project --mode minimal --agent claude-code

# Resume after interrupt
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project --resume

# Validate post-run artifacts
python dag_scheduler.py validate-dag --project /path/to/project

# Run benchmarks
python benchmarks/bench_dag.py

# Run all tests
for t in tests/test_*.py; do python "$t"; done
```
