# Reference Dossiers — Converged Framework

Topics researched for the Team Topologies × BMAD × DAG Automator convergence project.

---

## Completed Dossiers

| # | Topic | File | Size | Source |
|---|-------|------|------|--------|
| 1 | **DORA + Enterprise Implementation + AI** | `dora-enterprise-ai.md` | 41KB | Research report |
| 2 | **Story Mapping (Patton) + Mike Cohn** | `story-mapping-work-breakdown.md` | 48KB | Research report |
| 3 | **Project to Product (Kersten) + Flow Metrics** | `project-to-product-flow-metrics.md` | 19KB | Research report |
| 4 | **Business Process Modelling (BPMN/DMN/CMMN)** | `bpm-converged-framework.md` | 25KB | Research report |

| 5 | **OOP + SOLID + GoF Design Patterns** | `oop-solid-gof-patterns.md` | 42KB | Research report |
| 6 | **BFF + UI Component Design + UX + Micro Frontends** | `bff-ui-ux-microfrontends.md` | 32KB | Research report |

## Pre-existing Reference Material (in repo)

| Topic | Location |
|-------|----------|
| **BMAD Method** | `~/github/bmad-dag-automator/` (scheduler + orchestrator code) |
| **BMAD DAG Automator** | `~/github/bmad-dag-automator/dag_*.py` (full implementation) |
| **Team Topologies** | `~/.hermes/skills/software-development/team-topologies/SKILL.md` |
| **Architecture doc** | `~/.hermes/plans/bmad-dag-automator-architecture.md` |

## Potential Gaps (not yet researched)

These topics were implied by your pipeline but don't have dedicated dossiers yet:

| Topic | Why it matters for the framework |
|-------|----------------------------------|
| **OKRs** | You mentioned OKRs as the starting point (strategic → initiative). OKR theory, cascading, and OKR-to-story-map conversion would formalise the top of the pipeline. |
| **API Contract-First Design** | The `API Contract Agent` is a named step. OpenAPI/AsyncAPI, consumer-driven contracts, contract testing patterns. |
| **Cognitive Load Measurement** | Central to Team Topologies but deserves its own deep dive — the Team Cognitive Load Assessment tool, bus-factor analysis, complexity scoring. |
| **Value Stream Mapping** | The bridge between Team Topologies (Step 1: identify value streams) and DORA (measure flow efficiency). |
| **Acceptance Test-Driven Development / Spec by Example** | BMAD stories use Given/When/Then (Gherkin). ATDD patterns, living documentation, specification by example. |
| **GA / Production Readiness** | The final gate in your pipeline. Service maturity models, launch checklists, phased rollouts, feature flag graduation. |
| **AI Agent Observability** | How to trace, log, and monitor agent behaviour specifically — separate from application observability. |

---

## Quick Reference — Key Concepts Per Dossier

### DORA (dossier 1)
- 4 metrics: Deploy Frequency, Lead Time for Changes, MTTR, Change Failure Rate
- Elite = on-demand deploys, <1hr lead time, <1hr MTTR, <5% failure rate
- DORA + AI: bottleneck shifts from coding to review → new metric: Review Lead Time
- DAG-level DORA: DAG Completion Frequency, DAG Lead Time, DAG Rerun Latency, DAG Validation Failure Rate
- SPACE framework as human counterbalance to DORA

### Story Mapping (dossier 2)
- Backbone → walking skeleton → detailed stories (Patton's 2D map vs 1D backlog)
- INVEST + 3Cs (Cohn's foundations)
- 12 story splitting patterns
- Agent-ready vs human-ready stories (8-dimension comparison)
- Rich Gherkin: AC format with Agent, FileScope, DependsOn, Provides, Contract metadata

### Project to Product (dossier 3)
- 5 flow items: Features, Defects, Debts, Risks, Other
- 4 flow metrics: Flow Velocity, Flow Efficiency, Flow Time, Flow Distribution
- Ideal distribution: Features 40-50%, Defects 20-30%, Debt 15-25%, Risk 10-20%
- DAG North Star: DAG Effectiveness = Feature Nodes Completed × (1 - Handoff Rate) / Agent-Hours
- "Faster, Faster" trap

### BPMN (dossier 4)
- BPMN 2.0 elements mapped to the framework pipeline
- DMN decision tables for Definition of Ready, dependency confidence, topological ordering
- CMMN for exploratory phases (DAG induction, architecture design)
- Camunda/Zeebe as orchestration engine pattern
- DORA metrics derived from BPMN event instrumentation
