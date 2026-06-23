# BMAD DAG Automator — Product Requirements Document

> **Version:** 1.0  
> **Status:** Draft  
> **Author:** Paul Knauer  
> **Date:** 2026-06-23  
> **Repository:** [github.com/PaulKnauer/bmad-dag-automator](https://github.com/PaulKnauer/bmad-dag-automator)

---

## 1. Elevator Pitch

A DAG-aware scheduling and execution layer that extends BMAD's story automator — replaces linear story processing with dependency-respecting, level-by-level execution where agent pools scale elastically with DAG topology.

---

## 2. Target User

**Primary:** BMAD power users with complex story sets (10-50+ stories) who need automated parallel execution with proper dependency ordering. Users on BMAD Method or Enterprise planning tracks.

**Secondary:** Any BMAD user whose story sets have implicit or explicit dependencies — opt-in with a flag, transparent upgrade from linear processing.

---

## 3. Problem Statement

BMAD's existing `bmad-story-automator` processes stories in flat list order. Three gaps:

| Gap | Today's behaviour | Required behaviour |
|-----|-------------------|--------------------|
| **No dependency resolution** | Stories run in arbitrary list order; user must manually sequence | DAG induction reads explicit deps + LLM discovers implicit edges |
| **No level-based scheduling** | `maxParallel` creates opportunistic overlap, not intentional parallelism | Topological sort assigns levels; all same-level nodes run concurrently |
| **Static parallelism** | Agent count is a fixed ceiling set at config time | Pool scales per level: `min(max_concurrent, level_width)` |

---

## 4. Success Metrics

| Metric | Target | How measured |
|--------|--------|-------------|
| DAG Completion Time | ≤ linear execution time for same story set | Wall-clock comparison with existing automator |
| Agent Utilisation | ≥80% of available agents active per level | Pool stats in state doc |
| False Positive Induction | ≤2 false edges per 10 stories | User-flagged edges / total induced |
| Cycle Detection | 100% — no undetected cycles | Kahn's algorithm verification |

---

## 5. Key Capabilities

### 5.1 DAG Induction

- Parse explicit dependencies from `sprint-status.yaml` (or story dict)
- LLM pass for implicit dependencies (interface, data, architectural)
- **3 modes:** `minimal` (explicit only), `assisted` (LLM suggests, user approves), `automatic` (LLM adds immediately)
- Cycle detection via Kahn's algorithm
- Critical path computation (longest path via DP)

### 5.2 Level-Based Scheduling

- Topological sort → ordered levels where Level 0 = root nodes
- All nodes in same level run concurrently
- Next level starts only when current level completes
- Handles serial chains, fan-out, fan-in, and mixed shapes

### 5.3 Elastic Agent Pool

- Pool size = `min(max_concurrent, level_width)` — recalculated per level
- Scales up naturally when DAG widens, back down when it narrows
- Per-node lifecycle: tmux spawn → run → monitor → collect
- Retry chains: primary (2 retries) → fallback (2 retries) → escalate

### 5.4 Artifact Bridge

- Branch-per-level git model
- Each level branches from upstream level's tip
- Level end → merge all node work → propagate to next level
- Interface contract tracking across DAG edges

### 5.5 State Management

- Markdown state document with DAG frontmatter
- Machine + human readable
- Resume from any level (not story index)
- Validate mode for DAG consistency checking

---

## 6. Non-Goals

- Not a replacement for `bmad-story-automator` — an opt-in layer on top
- Not a general-purpose job scheduler — DAG model is scoped to BMAD story execution
- Not responsible for agent output quality — inner node loop (create→dev→review→commit) is unchanged from automator
- Not an orchestrator for non-BMAD projects — interfaces are BMAD story artifacts

---

## 7. Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Induction mode | 3 modes, user-configurable | Supports conservative (minimal) to trusting (automatic) teams |
| Git model | Branch-per-level with merge | Best balance of isolation + propagation overhead |
| Language | Python | Matches automator's existing Python helper CLI |
| Node granularity | One story per node | Aligns with automator's per-story loop |
| Contribution model | BMAD community module (if proven) | Open-source, standard BMAD module structure |

---

## 8. Implementation Status

| Phase | Deliverable | Status |
|-------|-------------|--------|
| **1 — DAG Induction** | Core data model, induction pipeline, CLI | ✅ Built & tested (14 tests) |
| **2 — Level Scheduler** | Topological sort, level execution loop | ✅ Built |
| **3 — Artifact Bridge** | Branch-per-level git model, merge | ✅ Built |
| **4 — Elastic Agent Pool** | Dynamic pool, tmux lifecycle, retry chains | ✅ Built |
| **5 — Production Hardening** | Resume, validate, failure injection, benchmarks | 🔜 Planned |
| **6 — Community Contribution** | BMAD module packaging, PR to bmad-code-org | 🔜 Future |

---

## 9. Constraints

- Python 3 — stdlib + pyyaml only, zero external runtime dependencies
- Reuses BMAD automator's tmux-wrapper, agent config model, and skill invocation
- No CI/CD pipeline yet
- Public repo at `github.com/PaulKnauer/bmad-dag-automator`

---

## 10. Dossiers (Research Completed)

6 research dossiers inform the product architecture — available in `dossiers/`:

| Dossier | Relevance |
|---------|-----------|
| DORA + Enterprise + AI | DAG-level DORA metrics, agent observability patterns |
| Story Mapping + Mike Cohn | Agent-ready vs human-ready stories, Rich Gherkin format |
| Project to Product + Flow Metrics | DAG Effectiveness metric, flow distribution per agent |
| Business Process Modelling | BPMN pipeline mapping, DMN for dependency decisions |
| OOP + SOLID + GoF Patterns | SOLID gates per DAG level, pattern vocabulary |
| BFF + UI/UX + Micro Frontends | Micro frontend DAG composition, a11y as deploy gate |
