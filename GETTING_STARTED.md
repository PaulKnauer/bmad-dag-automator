# Getting Started with the BMAD DAG Automator

> **Audience:** Developers who just cloned the repo and want to go from zero to their first scheduled DAG run in under 10 minutes.  
> **Example used throughout:** `examples/auth-system.yaml` — an 8-story sprint to build a user authentication system.  
> **Prerequisites:** Python 3.10+, `git`, and optionally `tmux` (for live agent orchestration).

---

## What the DAG Automator Does

The BMAD DAG Automator extends [BMAD](https://github.com/nousresearch/bmad) with **topological dependency scheduling**, **elastic agent scaling**, and **production-hardened run management**. Instead of executing stories one at a time in arbitrary order, it:

1. **Parses** your story set into a DAG (Directed Acyclic Graph) — each story is a node, and dependencies between stories are edges.  
2. **Infers** implicit dependencies via interface analysis or LLM assistance (three modes: `minimal`, `assisted`, `automatic`).  
3. **Schedules** stories into **parallelisable levels** using Kahn's algorithm — stories with no remaining dependencies run concurrently.  
4. **Executes** level-by-level, spawning one agent session per story per level, with git branch-per-level isolation.  
5. **Resumes** from the last incomplete level if interrupted (Ctrl+C won't lose progress).

The result: **shorter sprint cycle times** because independent work runs in parallel, **clear architectural dependency tracking** because every edge is explicit or LLM-inferred, and **deterministic replay** because the DAG schedule is reproducible.

---

## Installation

The DAG Automator is a CLI tool run directly from the repo — it's not published as a PyPI package. Detailed setup instructions are in [INSTALL.md](INSTALL.md), but here is the quick summary:

### Quick Install

```bash
# 1. Clone the repo (if you haven't already)
git clone https://github.com/nousresearch/bmad-dag-automator.git
cd bmad-dag-automator

# 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install minimal dependencies
pip install pyyaml

# 4. Verify everything works
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

> **Note:** No `pip install` of the package itself — the CLI is run directly as `python dag_scheduler.py <command>`. For live orchestration you'll also need `tmux` installed and a configured LLM provider (Hermes, Claude, etc.). See [INSTALL.md](INSTALL.md) for full details.

---

## Creating Your First Story YAML

A *story set* is a YAML file with a list of stories. Each story is a node in the DAG with optional dependency information. Here is the `examples/auth-system.yaml` that ships with the repo:

```yaml
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

### Story Fields Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique story identifier (e.g., `epic-1.1`) |
| `title` | ✅ | Human-readable description of the work |
| `explicit_deps` | ✅ | Array of story IDs this story depends on (empty `[]` if none) |
| `file_scope` | Optional | Files this story creates or owns |
| `interfaces_provides` | Optional | Types, classes, or APIs this story exports |
| `consumes_interfaces` | Optional | Types, classes, or APIs this story imports |

> **Key insight:** Stories with empty `explicit_deps` (like `epic-1.1` and `epic-1.2`) are *root nodes* — they have no prerequisites and run first, in parallel. Stories that list dependencies (like `epic-1.3` which depends on both `epic-1.1` and `epic-1.2`) will wait for their dependencies to complete before running.

### Try it: Create Your Own Mini Story Set

Create a file called `my-first-sprint.yaml`:

```yaml
stories:
  - id: "setup"
    title: "Project scaffolding and config"
    explicit_deps: []
    file_scope: ["setup.py", "config.yaml"]

  - id: "database"
    title: "Database models and migrations"
    explicit_deps: ["setup"]
    file_scope: ["src/db/models.py"]

  - id: "api"
    title: "API endpoints"
    explicit_deps: ["database"]
    file_scope: ["src/api/routes.py"]

  - id: "tests"
    title: "Integration tests"
    explicit_deps: ["api"]
    file_scope: ["tests/test_api.py"]
```

This defines a simple serial chain: `setup → database → api → tests`. All four stories run one at a time — no parallelism possible because each depends on the previous.

---

## Validating Your Story Set

Before scheduling, always validate your story YAML:

```bash
python dag_scheduler.py validate my-first-sprint.yaml
```

Expected output:

```
  ✅ 4 stories loaded
  ✅ No dangling references
  ✅ No cycles detected
  🔗 3 explicit dependency edges

  ✅ Stories file is valid
```

**What validate checks:**

| Check | What It Catches |
|-------|-----------------|
| ✅ Stories parseable | Valid YAML with required `id`, `title`, and `explicit_deps` fields |
| ✅ No dangling refs | All `explicit_deps` IDs actually exist as story IDs in the file |
| ✅ No cycles | The graph is acyclic (Kahn's algorithm can topologically sort it) |

**Exit codes:**
- **0** — Valid, no errors
- **1** — Invalid (cycles, dangling refs, or parse errors)

### Try breaking it on purpose

Dangling refs produce a warning (not failure):

```yaml
# bad-story.yaml
stories:
  - id: "task-1"
    title: "Something"
    explicit_deps: ["task-99"]   # <-- task-99 doesn't exist
```

```bash
python dag_scheduler.py validate bad-story.yaml
# → "⚠️ Dangling references: ['task-99']" — still exits 0
```

Cycles fail hard:

```yaml
stories:
  - id: "a"
    title: "A"
    explicit_deps: ["b"]
  - id: "b"
    title: "B"
    explicit_deps: ["a"]   # <-- cycle: a → b → a
```

```bash
python dag_scheduler.py validate cyclic.yaml
# → "❌ Cycle detected: a → b → a" — exits 1
```

---

## Running a Schedule

Once your story set is valid, build the DAG schedule:

```bash
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml
```

**Example output:**

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

### Understanding the Schedule

The schedule breaks your stories into **levels** — all stories at the same level can run in parallel because they share no unfulfilled dependencies:

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

**The critical path** (`epic-1.1 → epic-1.4 → epic-1.5 → epic-2.1 → epic-2.2`) is the longest dependency chain — it determines the *minimum* wall-clock time regardless of parallelism. You cannot run the admin UI (`epic-2.2`) until its entire dependency chain completes.

### Induction Modes

The `--mode` flag controls how dependencies are discovered:

| Mode | Cost | LLM Pass | Deps Applied | Use Case |
|------|------|----------|--------------|----------|
| `minimal` | Free | Skipped | Explicit only | Fast, deterministic, no LLM needed |
| `assisted` | LLM | Generated | Flagged for review | Human-in-the-loop validation |
| `automatic` | LLM | Generated | Applied directly | Fully autonomous, trust the LLM |

For your first run, always start with `--mode minimal`. It uses only the `explicit_deps` you wrote — no LLM calls, no surprises.

---

## Understanding the Output Files

Running `schedule` produces a **`dag-manifest.yaml`** — the blueprint for execution:

```yaml
dag:
  mode: minimal
  status: validated
  levels:
  - index: 0
    width: 2
    nodes: [epic-1.1, epic-1.2]
  - index: 1
    width: 2
    nodes: [epic-1.3, epic-1.4]
  # ... more levels ...
  max_width: 2
  total_nodes: 8
  total_levels: 5
  critical_path: [epic-1.1, epic-1.4, epic-1.5, epic-2.1, epic-2.2]
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

You can also explore the DAG interactively:

```bash
# Dump the complete DAG structure to the terminal
python dag_scheduler.py inspect examples/auth-system.yaml
```

Use `inspect` to debug scheduling decisions, verify level assignments, and trace dependency chains before committing to a run.

---

## Running a Dry-Run Orchestration

The `orchestrate` command is the flagship pipeline — it runs induction, level-by-level agent execution, and finalization. A **dry run** simulates the full pipeline without actually spawning tmux sessions or touching git:

```bash
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /tmp/auth-demo \
    --mode minimal \
    --dry-run
```

**Expected output:**

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
  📐 Level 2: 2 node(s)
    ⏳ Level 2: spawned 2 agents (pool=2/4, waiting up to 30m)
    ✅ epic-1.5 completed (dry-run)
    ✅ epic-2.3 completed (dry-run)
  📐 Level 3: 1 node(s)
    ⏳ Level 3: spawned 1 agents (pool=1/4, waiting up to 30m)
    ✅ epic-2.1 completed (dry-run)
  📐 Level 4: 1 node(s)
    ⏳ Level 4: spawned 1 agents (pool=1/4, waiting up to 30m)
    ✅ epic-2.2 completed (dry-run)

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
| 1 | Error (induction failure, etc.) |
| 2 | Paused (interrupted — can resume with `--resume`) |

> **Why dry-run first?** It validates the entire pipeline path without side effects — no tmux sessions, no git branches, no LLM costs. You'll see the exact level-by-level order the orchestrator will follow in a live run.

### What a Live Orchestration Looks Like

Once you're comfortable with the dry-run output, a live orchestration adds real agent spawning and git branching:

```bash
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/your/git/repo \
    --mode minimal \
    --agent claude-code \
    --model sonnet \
    --max-concurrent 4
```

During a live run the orchestrator:

1. Creates a `_bmad-output/dag-automator/` directory with the manifest and state document
2. Per-level: creates a branch (`dag/level-0`, `dag/level-1`, ...), spawns one agent per story, waits for all agents to complete
3. After each level: merges changes back via `artifact_bridge.py`
4. On completion: creates a final `dag/complete` branch with all artifacts

If you hit Ctrl+C mid-run, the state doc is saved with `PAUSED` status. Resume later with:

```bash
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/your/project --resume
```

---

## Next Steps

You've covered the getting-started loop: **validate → schedule → dry-run orchestrate**. Here's where to go next:

| Resource | What It Covers |
|----------|---------------|
| [README.md](README.md) | Quick Start recap + full CLI reference + test suite info |
| [OPERATIONS_GUIDE.md](OPERATIONS_GUIDE.md) | Deep dive: all commands, resume, failure handling, edge cases, architecture |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Running the 52-test suite, writing new tests, failure injection patterns |
| [INSTALL.md](INSTALL.md) | Prerequisites, environment setup, LLM provider config |
| `examples/auth-system.yaml` | The 8-story auth system used in this guide — modify it to experiment |
| `benchmarks/bench_dag.py` | Scheduling performance benchmarks (4 DAG shapes) |

### Quick Reference — All Commands

```bash
# Validate
python dag_scheduler.py validate examples/auth-system.yaml

# Schedule (minimal mode — explicit deps only)
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Inspect DAG state
python dag_scheduler.py inspect examples/auth-system.yaml

# Dry-run orchestrator
python dag_scheduler.py orchestrate examples/auth-system.yaml --project /tmp/demo --mode minimal --dry-run

# Live orchestration
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project \
    --mode minimal \
    --agent claude-code \
    --model sonnet \
    --max-concurrent 4

# Resume after interrupt
python dag_scheduler.py orchestrate examples/auth-system.yaml \
    --project /path/to/project --resume

# Post-run validation
python dag_scheduler.py validate-dag --project /path/to/project

# Apply LLM-generated edges (assisted/automatic modes)
cat llm_edges.json | python dag_scheduler.py apply-llm examples/auth-system.yaml

# Run benchmarks
python benchmarks/bench_dag.py

# Run all tests
for t in tests/test_*.py; do python "$t"; done
```

Happy scheduling!
