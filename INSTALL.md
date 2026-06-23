# BMAD DAG Automator — Installation Guide

> **Audience:** Developers setting up the BMAD DAG Automator for the first time.  
> **Last updated:** 2026-06-23  
> **Project:** [bmad-dag-automator](https://github.com/nousresearch/bmad-dag-automator)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
   - [Python](#python)
   - [System Tools](#system-tools)
   - [Platform-Specific Notes](#platform-specific-notes)
2. [Quick Install](#quick-install)
3. [Dependency Installation](#dependency-installation)
4. [Verifying the Installation](#verifying-the-installation)
5. [BMAD Skill Registration](#bmad-skill-registration)
   - [Registering with BMAD](#registering-with-bmad)
   - [Skill Descriptions](#skill-descriptions)
6. [Hermes Agent Integration](#hermes-agent-integration)
7. [Claude Code Integration](#claude-code-integration)
8. [LLM Provider Setup](#llm-provider-setup)
9. [Docker Setup](#docker-setup)
   - [Dockerfile](#dockerfile)
   - [Docker Compose (Optional)](#docker-compose-optional)
10. [Post-Installation Checklist](#post-installation-checklist)
11. [Troubleshooting](#troubleshooting)
12. [Next Steps](#next-steps)

---

## Prerequisites

### Python

| Requirement | Minimum Version |
|---|---|
| **Python** | 3.10+ |
| **pip** | 21.x+ (bundled with Python 3.10+) |

Check your version:

```bash
python --version   # Must be 3.10+
pip --version      # Should bundle with Python
```

> **Note:** The project uses `pyyaml` as its only pip dependency. Everything else is Python 3 stdlib. No `setup.py`, `pyproject.toml`, or build system is required.

### System Tools

These are required for **full orchestration** (live runs). For `validate`, `schedule`, and `--dry-run` operations, only Python is needed.

| Tool | Required For | Install Command |
|---|---|---|
| **git** | Artifact branch-per-level management (orchestrate mode) | See platform notes below |
| **tmux** | Live agent session spawning and monitoring | See platform notes below |

Optional agent tools (one of these must be installed for live orchestration):

| Tool | Source | Notes |
|---|---|---|
| `claude-code` | [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | Default agent |
| `codex` | [OpenAI Codex CLI](https://github.com/openai/codex) | Alternative |
| `opencode` | [OpenCode CLI](https://github.com/sst/opencode) | Alternative |

### Platform-Specific Notes

#### Linux (Ubuntu / Debian)

```bash
# Python (if not already installed)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git tmux

# Verify
python3 --version  # Should be 3.10+
tmux -V             # Should report a version
git --version
```

#### Linux (Fedora / RHEL)

```bash
# Python
sudo dnf install -y python3 python3-pip python3-virtualenv git tmux

# Verify
python3 --version
tmux -V
git --version
```

#### Linux (Arch)

```bash
sudo pacman -S python python-pip git tmux
```

#### macOS

```bash
# Using Homebrew (recommended)
brew install python git tmux

# Verify
python3 --version
tmux -V
git --version
```

> **macOS note:** macOS ships with Python 3.x as of recent versions, but it's recommended to use Homebrew's Python to avoid permission issues. If `python` points to Python 2, always use `python3` explicitly.

#### Windows

Windows is **not natively supported** for full orchestration (tmux is Unix-only). However, the following approaches work:

- **WSL2 (Windows Subsystem for Linux):** Install Ubuntu on WSL2, then follow the Linux instructions above. All features work within WSL.
- **Minimal mode only:** `validate`, `schedule`, and `inspect` commands work on any platform with Python 3.10+.
- **Docker:** See the [Docker Setup](#docker-setup) section for a containerized approach.

---

## Quick Install

```bash
# 1. Clone the repository
git clone https://github.com/nousresearch/bmad-dag-automator.git
cd bmad-dag-automator

# 2. (Recommended) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install the single dependency
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

---

## Dependency Installation

### Python Dependencies

The project has a single pip dependency:

```bash
pip install pyyaml
```

All other modules (`argparse`, `json`, `os`, `sys`, `subprocess`, `signal`, `asyncio`, `datetime`, `typing`, `dataclasses`, `enum`, `collections`) are Python 3 stdlib — no additional packages needed.

### Version Pinning (Optional)

If you prefer a pinned environment, create a `requirements.txt`:

```txt
PyYAML==6.0.2
```

Then:

```bash
pip install -r requirements.txt
```

> **Note:** There is no `setup.py` or `pyproject.toml` — the project is designed as a collection of standalone Python modules run directly via `python dag_scheduler.py`. It is not a PyPI package.

---

## Verifying the Installation

Run all available checks to confirm everything is working:

```bash
# 1. Validate a story file
python dag_scheduler.py validate examples/auth-system.yaml

# 2. Schedule in minimal mode (no LLM needed)
python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# 3. Dry-run the orchestrator
python dag_scheduler.py --mode minimal orchestrate examples/auth-system.yaml --dry-run

# 4. Run the test suite
for t in tests/test_*.py; do echo "Running $t..."; python "$t"; done

# 5. Run benchmarks
python benchmarks/bench_dag.py
```

All tests should report a passing status (52 tests total across 5 files). The benchmark harness prints scheduling performance for 4 DAG shapes.

---

## BMAD Skill Registration

The DAG Automator ships with two BMAD skills that register the tool into the BMAD ecosystem. These are already defined in `.agents/skills/` and `.claude/skills/`.

### Skill Manifest Registration

If you have BMAD installed and want the DAG Automator to appear in BMAD's skill index:

**Option A — Add to BMAD skill manifest (`_bmad/_config/skill-manifest.csv`):**

The following entries should already exist in your copy of `skill-manifest.csv`. If not, add them:

```csv
"bmad-dag-schedule","bmad-dag-schedule","Run DAG scheduling on story YAML — produces topological schedule with levels and critical path. Use when the user says 'run dag schedule', 'schedule stories', or 'build dag manifest'.","bmm",".agents/skills/bmad-dag-schedule/SKILL.md"
"bmad-dag-validate","bmad-dag-validate","Validate DAG consistency and story YAML — checks manifest vs state doc, orphaned nodes, level boundaries. Use when the user says 'validate dag', 'check dag consistency', or 'verify story yaml'.","bmm",".agents/skills/bmad-dag-validate/SKILL.md"
```

The `path` column uses a relative path from the project root to the `SKILL.md` file.

**Option B — Run BMAD re-index:**

```bash
# If your BMAD setup supports auto-discovery
bmad index
```

### Skill Descriptions

#### bmad-dag-schedule

- **Triggers:** "run dag schedule", "schedule stories", "build dag manifest"
- **Commands:** `validate`, `schedule`, `inspect`, `apply-llm`, `orchestrate`
- **Location:** `.agents/skills/bmad-dag-schedule/SKILL.md`

#### bmad-dag-validate

- **Triggers:** "validate dag", "check dag consistency", "verify story yaml"
- **Commands:** `validate-dag`
- **Location:** `.agents/skills/bmad-dag-validate/SKILL.md`

---

## Hermes Agent Integration

The DAG Automator includes pre-configured skill definitions for Hermes Agent:

### Skill Locations

```
.agents/skills/
├── bmad-dag-schedule/
│   └── SKILL.md          # Scheduling + orchestration skill
└── bmad-dag-validate/
    └── SKILL.md          # DAG validation skill
```

### How It Works in Hermes

When Hermes Agent processes a user request that matches a skill trigger description, it loads the corresponding `SKILL.md` to understand how to invoke `dag_scheduler.py`. The skill descriptions are:

- **bmad-dag-schedule:** Triggered by requests to schedule stories, run DAG orchestration, or build a DAG manifest.
- **bmad-dag-validate:** Triggered by requests to validate DAG consistency or verify YAML story files.

### Usage Within Hermes

Once the skills are registered in Hermes's skill directory (which they already are at `.agents/skills/`), Hermes will automatically surface the DAG Automator when a user's intent matches one of the trigger patterns. No additional configuration is required.

### Customizing for Your Hermes Profile

If you use a non-default Hermes profile, copy the skill directories:

```bash
# Example: add skills to a profile named "my-profile"
cp -r .agents/skills/bmad-dag-schedule ~/.hermes/profiles/my-profile/skills/
cp -r .agents/skills/bmad-dag-validate ~/.hermes/profiles/my-profile/skills/
```

---

## Claude Code Integration

The DAG Automator also includes skill definitions for Claude Code (if you use Claude Code as your agent tool).

### Skill Locations

```
.claude/skills/
├── bmad-dag-schedule/
│   └── SKILL.md
└── bmad-dag-validate/
    └── SKILL.md
```

These follow the same format as the Hermes Agent skills. Claude Code will pick them up automatically from the project root's `.claude/skills/` directory.

---

## LLM Provider Setup

For `assisted` and `automatic` dependency induction modes, the DAG Automator requires an LLM provider to generate implicit dependency suggestions. This is a **two-step workflow**:

### Step 1: Generate the LLM Prompt

```bash
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml
```

This prints an LLM prompt with all story details and dependency patterns. Copy the prompt (everything between `--- LLM PROMPT ---` and `--- END PROMPT ---`).

### Step 2: Feed LLM Response Back

Send the prompt to your LLM provider (Hermes, Claude, GPT, etc.), save the response as JSON, then apply it:

```bash
python dag_scheduler.py apply-llm examples/auth-system.yaml < llm_edges.json
```

Or skip the separate step and provide the file directly:

```bash
python dag_scheduler.py --mode automatic schedule examples/auth-system.yaml --llm-output llm_edges.json
```

### LLM Output Format

The LLM response must follow this JSON structure:

```json
{
  "edges": [
    {
      "from": "epic-1.3",
      "to": "epic-1.1",
      "reasoning": "registration needs User model",
      "confidence": "high"
    }
  ]
}
```

### Supported LLM Providers

The DAG Automator is provider-agnostic — any LLM that can analyze structured YAML and output JSON works:

| Provider | Use Case | Notes |
|---|---|---|
| **Hermes** | Integration with Hermes Agent | Matches BMAD ecosystem |
| **Claude** | Integration with claude-code agent | Default agent tool |
| **OpenAI GPT** | Integration with codex agent | Good for JSON output |
| **Any local model** | Offline / air-gapped setups | Requires JSON instruction tuning |

---

## Docker Setup

> **Note:** The project does not ship with a pre-built Dockerfile. Below is a reference setup you can use to containerize the DAG Automator for reproducible environments.

### Dockerfile

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir pyyaml

# Verify the installation
RUN python dag_scheduler.py validate examples/auth-system.yaml

# Default command: print help
CMD ["python", "dag_scheduler.py", "--help"]
```

### Building and Running

```bash
# Build the image
docker build -t bmad-dag-automator .

# Run validation
docker run --rm bmad-dag-automator python dag_scheduler.py validate examples/auth-system.yaml

# Schedule in minimal mode
docker run --rm bmad-dag-automator python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml

# Interactive shell (for orchestration with mounted project)
docker run --rm -it \
    -v /path/to/your/project:/project \
    -v /var/run/docker.sock:/var/run/docker.sock \
    bmad-dag-automator bash
```

> **Docker + tmux note:** Live orchestration inside Docker requires the container to have tmux support and access to a project directory via volume mount. For full live runs, consider using docker with `--privileged` or mounting `/var/run/docker.sock` for docker-in-docker setups.

### Docker Compose (Optional)

Create `docker-compose.yml` in the project root:

```yaml
version: "3.9"
services:
  dag-automator:
    build: .
    image: bmad-dag-automator
    volumes:
      - ./examples:/app/examples
      - ./_bmad-output:/app/_bmad-output
    command: python dag_scheduler.py validate examples/auth-system.yaml
```

### Multi-Platform Build

```bash
# Build for both amd64 and arm64
docker buildx build --platform linux/amd64,linux/arm64 -t bmad-dag-automator .
```

---

## Post-Installation Checklist

After completing installation, verify each capability:

| # | Capability | Command | Expected |
|---|---|---|---|
| 1 | Python available | `python --version` | 3.10+ |
| 2 | Dependencies installed | `pip list \| grep PyYAML` | PyYAML present |
| 3 | Story validation | `python dag_scheduler.py validate examples/auth-system.yaml` | ✅ Valid |
| 4 | Minimal schedule | `python dag_scheduler.py --mode minimal schedule examples/auth-system.yaml` | Manifest written |
| 5 | Dry-run orchestrate | `python dag_scheduler.py --mode minimal orchestrate examples/auth-system.yaml --dry-run` | ✅ DAG RUN COMPLETE |
| 6 | git available | `git --version` | Version reported |
| 7 | tmux available | `tmux -V` | Version reported |
| 8 | All tests pass | `for t in tests/test_*.py; do python "$t"; done` | All pass |
| 9 | Benchmarks run | `python benchmarks/bench_dag.py` | Table printed |
| 10 | Skills registered | Check `.agents/skills/` exists | Both skills present |

---

## Troubleshooting

### Common Installation Issues

| Symptom | Likely Cause | Solution |
|---|---|---|
| `Python 3.9 or lower detected` | Python version too old | Install Python 3.10+ (see platform notes above). Check with `python3 --version`. |
| `ModuleNotFoundError: No module named 'yaml'` | PyYAML not installed | Run `pip install pyyaml` or `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'dag_core'` | Wrong working directory | Run commands from the project root (`bmad-dag-automator/`), not a subdirectory. |
| `FileNotFoundError: examples/auth-system.yaml` | Wrong working directory | Ensure you are in the project root (`cd /path/to/bmad-dag-automator`). |
| `yaml.scanner.ScannerError` or YAML parse error | Corrupt or malformed story YAML | Validate your YAML with `python -c "import yaml; yaml.safe_load(open('your-file.yaml'))"`. |
| `OSError: [Errno 2] No such file or directory: 'tmux'` | tmux not installed | Install tmux: `sudo apt install tmux` (Linux) or `brew install tmux` (macOS). Not needed for `--dry-run`. |
| `git: command not found` | git not installed | Install git: `sudo apt install git` (Linux) or `brew install git` (macOS). Not needed for `--dry-run`. |
| `SubprocessError: ... tmux-wrapper ...` | tmux session failure | Ensure tmux is installed and functional. Try `tmux new -d` to test. |
| `Permission denied` when creating virtual env | System Python restrictions | Use `python3 -m venv .venv` without sudo, or use a pyenv-managed Python. |
| `LLM output required but not provided` | Using `assisted`/`automatic` mode without LLM file | Use `--mode minimal` for local-only operation, or provide LLM output via `--llm-output`. |
| `Story count mismatch...` on resume | Stories changed between runs | Resume requires the same story set. Start fresh with `--dry-run` first, or remove `--resume`. |
| `⚠️  Dangling references` during validate | Story `explicit_deps` references nonexistent ID | Check the `explicit_deps` list in your YAML — every referenced ID must exist as a story `id`. |
| `❌ Cycle detected` during schedule | Circular dependency chain | Break the cycle by removing one of the circular edges. Use `python dag_scheduler.py inspect <file>` to see the full graph. |
| `Merge conflict` during orchestrate | Parallel node commits conflict | Manually resolve conflicts on the `dag/level-N` branch, then resume with `--resume`. |
| Hermes Agent doesn't trigger DAG skills | Skills not in Hermes profile | Copy `.agents/skills/bmad-dag-*` to your Hermes profile's `skills/` directory. |
| `bmad index` doesn't find DAG skills | skill-manifest.csv missing entries | Add the entries from [Skill Manifest Registration](#skill-manifest-registration) to `_bmad/_config/skill-manifest.csv`. |
| Docker build fails on `tmux` install | Base image mismatch | Use `python:3.12-slim` or `python:3.12` (full Debian). The slim image includes apt. |
| `ValueError: too many values to unpack` | Corrupt `dag-manifest.yaml` | Delete `_bmad-output/dag-automator/` and re-run. |

### CLI Exit Code Reference

| Exit Code | Meaning | Common Cause |
|---|---|---|
| 0 | Success | Everything worked |
| 1 | Error | Cycle detected, validation failure, git error |
| 2 | Paused / Needs input | Orchestrator paused (Ctrl+C), or LLM output needed |
| 130 | Interrupted | SIGINT (Ctrl+C) during orchestration |

### Debugging Tips

1. **Always start with `--dry-run`** before a live orchestration to validate the pipeline path without touching tmux or git.
2. **Use `--mode minimal`** to eliminate LLM-related issues — if it works in minimal mode, the problem is in the LLM integration, not the DAG engine.
3. **Use `inspect` to debug DAG structure:** `python dag_scheduler.py inspect examples/auth-system.yaml` dumps the complete graph as YAML.
4. **Check `_bmad-output/dag-automator/orchestration.md`** for detailed per-level state if a run fails mid-way.
5. **Run individual test files** to isolate failures: `python tests/test_dag_core.py` tests core scheduling in isolation.

---

## Next Steps

Once installed and verified:

1. **Read the [Operations Guide](OPERATIONS_GUIDE.md)** — full CLI reference, story format, and orchestration walkthrough.
2. **Explore the example story set** at `examples/auth-system.yaml` to understand the story format.
3. **Try `schedule` in different modes:** `minimal` (explicit only), `assisted` (LLM suggests), `automatic` (LLM applies).
4. **Run a full live orchestration** on a git-initialized project (see [Operations Guide: Running a DAG Orchestration](OPERATIONS_GUIDE.md#running-a-dag-orchestration)).
5. **Review the [Testing Guide](TESTING_GUIDE.md)** for test structure and contribution patterns.
