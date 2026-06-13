# Business Process Modelling for Software Delivery & Autonomous Agent Workflows

**Research for Paul Knauer Converged Framework (Team Topologies × BMAD × DAG Orchestration)**

---

## 1. BPMN 2.0 — The Standard

### 1.1 Core Elements Architecture

BPMN 2.0 (ISO/IEC 19510:2013) defines five basic element categories:

| Category | Elements | Purpose |
|----------|----------|---------|
| **Flow Objects** | Events, Activities, Gateways | The verbs of a process |
| **Data** | Data Objects, Inputs/Outputs, Data Stores | The nouns — artifacts |
| **Connecting Objects** | Sequence Flows, Message Flows, Associations | How things link |
| **Swimlanes** | Pools, Lanes | Who does what |
| **Artifacts** | Groups, Text Annotations | Documentation |

**Key subtypes for software delivery:**
- **Events**: Start (None, Message, Timer, Conditional, Signal), Intermediate (Message catch/throw, Timer, Link, Escalation, Error), End (None, Message, Terminate, Error, Escalation)
- **Activities**: Task (Service, User, Manual, Business Rule, Script, Send, Receive), Subprocess (collapsed, expanded, embedded, reusable, transaction, ad-hoc)
- **Gateways**: Exclusive (XOR), Inclusive (OR), Parallel (AND), Complex, Event-based

### 1.2 Modelling Roles, Decisions, and Handoffs

**Roles via Pools and Lanes:**
- **Pool** = a participant (a business entity, team, or external system). Pools communicate via **Message Flows** (dashed lines) — cross-team handoffs.
- **Lane** = a sub-partition within a pool, typically a role or department.
- **Rule**: Sequence flows NEVER cross pool boundaries. Only Message Flows cross pools.

**Decision Points via Gateways:**
- **XOR (Exclusive)** — Exactly one path. E.g., "Is story ready? Yes→proceed; No→refine"
- **OR (Inclusive)** — One or more paths. E.g., "Deploy to Staging + Production + Canary"
- **AND (Parallel)** — All paths concurrently. E.g., DAG level fan-out
- **Event-Based** — First event wins. E.g., approval OR timeout

**Handoff Patterns via Message Flows:**
1. **Sync Handoff**: Activity Pool A → Message Flow → Receive Task Pool B
2. **Async Handoff**: Activity Pool A → Message Flow → Intermediate Catch Event Pool B
3. **Error Escalation**: Error End Event → Boundary Error Event on subprocess

### 1.3 Process Modelling Levels

BPMN has three distinct levels:

| Level | Also Called | Audience | Detail | Tooling |
|-------|-------------|----------|--------|---------|
| **Descriptive** (Level 1) | Business Process Diagram | Executives, Stakeholders | High-level flow, ~10-15 elements | draw.io, Miro, Lucidchart |
| **Analytical** (Level 2) | Detailed Process Model | Process Analysts, Ops Leads | Full gateway logic, data objects, swimlanes, exception paths | Signavio, Bizagi Modeler |
| **Executable** (Level 3) | Technical Process Definition | Developers, Automation Engineers | Full BPMN XML, service task implementations, DMN references, form definitions | Camunda Modeler, bpmn-js |

**For Pauls framework**: Model OKR→GA pipeline at **Level 2 (Analytical)** for human decision-makers, with Level 3 extensions for agentic parts.

### 1.4 Real Tools

| Tool | Strength | Best For |
|------|----------|----------|
| **Camunda (Modeler + Platform)** | Full executable lifecycle. BPMN 2.0, DMN 1.3, CMMN 1.1. Zeebe engine cloud-native. REST API for agent integration. | Primary runtime choice — Zeebe orchestration maps directly to agent invocations. |
| **Signavio** | Enterprise modelling, process mining | Design-time modelling and simulation |
| **Bizagi Modeler** | Free desktop modeller, analytical diagrams | Rapid prototyping |
| **draw.io / bpmn-js** | Free, web-based. bpmn-js is reference BPMN renderer | Embedding diagrams in web dashboards |

### 1.5 BPMN → Executable Workflow Mapping

1. **BPMN XML** ( file) — full process definition
2. **Camunda Modeler** adds implementation details: service task topic names, form keys, expressions
3. **Deploy to Engine**:
   - **Camunda Platform 7** (Java, embedded/hybrid) — traditional BPM engine
   - **Zeebe / Camunda Platform 8** (gRPC, cloud-native) — microservice orchestration, horizontal scaling, exact-fit for agent systems
4. **External Task Pattern** (most relevant for agents):
   - BPMN defines a **Service Task** with 
   - Agent subscribes to that topic
   - Engine gives agent a job (variables: , )
   - Agent processes and completes (sends back: )
   - Engine advances process state

**For agentic systems: External Task pattern is the correct mapping.** Agents are external workers subscribed to topics. The BPMN engine becomes the orchestrator state machine.

---
## 2. Activity Definition Patterns for Software Delivery

### 2.1 Standard SDLC Activities as BPMN Tasks

| SDLC Phase | BPMN Activity Type | Input | Output | Std Duration |
|------------|-------------------|-------|--------|-------------|
| **Requirements** | User Task (PM) | OKR, Research | PRD, Stories | 1-2 sprints |
| **Design** | User Task (Architect) | PRD | ADR, System Design | 1 sprint |
| **Implementation** | Service Task (Coding Agent) or User Task (Dev) | Story, Spec | Code, PR | Hours-days |
| **Testing** | User Task (QA) or Service Task (Test Agent) | Code + Tests | Test Report, Bugs | Hours-days |
| **Deployment** | Service Task (CI/CD) | Release Artifact | Deployed Env | Minutes |
| **Operations** | User Task (SRE) + Service Task (Monitoring) | System | SLO Metrics | Continuous |

### 2.2 Formal Activity Definition Template

Each activity should define:
- **Activity name and type** (Service Task / User Task / Business Rule Task)
- **Lane** (which role or agent)
- **Inputs** (Data Objects from prior activities)
- **Outputs** (Data Objects produced)
- **Roles** (RACI: R=the lane, A=pool owner, C=message flows in, I=message flows out)
- **Duration** (estimated, with agent vs human variance)
- **Acceptance Criteria** (DMN table reference for pass/fail)
- **Handoff Condition** (message event that gates next activity)
- **Exception Path** (what happens on rejection or failure)

Example:


### 2.3 RACI → BPMN Lane Mapping

| RACI Role | BPMN Mapping | Example |
|-----------|-------------|---------|
| **R — Responsible** | Lane whose activity performs the work | Coding Agent lane implements feature |
| **A — Accountable** | Lane that owns pool or final decision gateway | Senior Engineer lane approves code review |
| **C — Consulted** | Lane/pool that receives message flows for input before activity | Security Expert pool receives Threat Model consult |
| **I — Informed** | End-event notification or message throw. Non-blocking. | Team Channel pool gets Slack notification |

**Nested mapping**: Pool = Accountable entity. Lanes within = Responsible roles. Consulted/Informed = Message Flows.

### 2.4 AI Agent vs Human Activities

| Dimension | Human (User Task) | Agent (Service Task) |
|-----------|------------------|---------------------|
| **Duration** | Variable, hour-days | Predictable, sec-min |
| **State** | Can pause, defer, context-switch | Atomic — runs to completion or fails |
| **Approval** | May need synchronous approval | Auto-approval with confidence threshold, escalate if low |
| **Exception** | Can improvise ad-hoc | Needs explicit path (DMN, retries, escalation) |
| **Retry** | Self-corrects | Defined policy (n times, then escalate) |
| **Handoff** | Meeting, ticket, notification | API call, message queue, webhook |

**Whats the same**: Both need input/output contracts, acceptance criteria, SLAs, escalation paths.



## 3. Decision Modelling (DMN)

### 3.1 How DMN Complements BPMN

DMN 1.3 (OMG standard, ISO/IEC 24707) provides a formal language for business decisions separate from process flow. Key insight: **BPMN handles the flow (when/where decisions happen), DMN handles the logic (how decisions are made).**

- A BPMN **Business Rule Task** references a DMN decision table
- The DMN table encapsulates all decision logic
- Changes to business rules don't require process model changes — just redeploy the DMN

### 3.2 When to Use DMN vs BPMN Gateway

| Scenario | BPMN Gateway | DMN Table |
|----------|-------------|-----------|
| DAG ordering | Two-path XOR: "A then B vs B then A" | Multi-criteria: depth, confidence, resource constraints |
| Definition of Ready | Single Boolean: "All AC met?" | Weighted: clarity, testability, feasibility, cost-of-delay |
| Agent confidence | Threshold: "> 0.8? Yes/No" | Tiered: > 0.9 auto-execute, > 0.7 flag, < 0.7 escalate |
| Production readiness | Single compliance pass/fail | Multi-factor: security, perf, CAB, rollback plan |

**Rule of thumb**: Single if/else → gateway. Multi-factorial or frequent rule changes → DMN.

### 3.3 Software Delivery Decision Tables

**Example 1: Definition of Ready** (Hit Policy: FIRST)

Inputs: StoryClarity, HasAC, DependenciesResolved, CostOfDelay, PreferredBy
- Clear+Yes+Resolved+any+any → READY
- Clear+Yes+Unresolved+Critical+Architect → READY_CAUTION
- Unclear+any+any+any+any → NOT_READY
- any+No+any+any+any → NEEDS_AC
- any+any+Unresolved+Low+any → BLOCKED

**Example 2: BMAD Dependency Classification** (Hit Policy: COLLECT)

Inputs: SimilarityScore, SourceReliability, DependencyDepth
- > 0.9 + High + any → CONFIRMED + HIGH confidence
- 0.7-0.9 + High + any → LIKELY + MEDIUM
- 0.7-0.9 + Medium + < 3 → POSSIBLE + MEDIUM
- 0.5-0.7 + any + any → UNCERTAIN + LOW
- < 0.5 + any + any → UNKNOWN + LOW
- any + any + > 5 → SUGGEST_SPLIT + LOW

**Example 3: DAG Ordering Strategy** (Hit Policy: FIRST)

Inputs: CrossLevelDeps, ParallelismAvailable, AvgConfidence
- Yes + any + any → TOPOLOGICAL_SORT
- No + > 3 workers + > 0.8 → BATCH_PARALLEL
- No + > 3 workers + < 0.8 → PAIRWISE_VERIFY
- No + <= 3 workers + any → SEQUENTIAL

### 3.4 DMN for BMAD Induction Decisions

DMN formalizes four key induction decisions:

1. **Dependency Classification Confidence** (table above): replaces hardcoded thresholds with transparent rules.
2. **Topological Ordering Choice**: decides execution strategy per DAG level.
3. **DAG Split/Merge**: When depth > 5 levels, should the DAG split? DMN encodes criteria.
4. **Task-Executor Assignment**: Which agent type (coder, reviewer, architect) handles each node.

Execution flow: BPMN Business Rule Task → DMN table → Response flows back as process variables → Gateway routes based on variables.

---
## 4. Role Definition Standards

### 4.1 BPMN Semantics

- **Pool** = A participant in a collaboration. Independent lifecycle. Contains a process (or black box with only message flows visible).
- **Lane** = Sub-partition within a pool. Groups activities by role, department, or capability.
- **Lane Set** = Hierarchical grouping (e.g., Engineering > Backend, Frontend, QA)

**Critical rule**: Sequence flows stay within a pool. Only Message Flows cross pools.

### 4.2 Team Topologies → BPMN Mapping

| Team Topology | BPMN Mapping | Rationale |
|--------------|-------------|-----------|
| **Stream-Aligned Team** | **Pool** — owns end-to-end process slice | Autonomous lifecycle, owns business capability |
| **Enabling Team** | **Pool** — consultation via Message Flows | Accelerates stream team, does NOT do the work |
| **Complicated-Subsystem** | **Pool** — black-box subprocess | Only interfaces visible via Message Flows |
| **Platform Team** | **Pool** — self-service via Message Flows + Data Stores | Produces APIs, infra, tooling consumed by stream teams |

Within a stream-aligned pool:
```
Pool: Payments Stream Team
  Lane: Product Manager (human)
  Lane: Senior Engineer (human)
  Lane: AI Coding Agent System
    Lane: Orchestrator Agent
    Lane: Code Generation Agent
    Lane: Code Review Agent
    Lane: Test Generation Agent
  Lane: QA Engineer (human)
  Lane: DevOps Engineer (human)
```

### 4.3 Agent-Specific Lanes

| Agent | BPMN Task | Topic | Notes |
|-------|----------|-------|-------|
| **Orchestrator** | Service Task | orchestrator | DAG orchestrator, Zeebe workflow engine |
| **PRD Agent** | Service Task | prd-generation | Input: OKR, Context. Output: PRD. Human review gate. |
| **Architecture Agent** | Service Task | architecture-design | May be CMMN (exploratory) |
| **UX Agent** | Service Task | ux-design | Visual artifacts as Data Objects |
| **API Contract Agent** | Service Task | api-contract | OpenAPI/Spec-first contracts |
| **Coding Agent** | Service Task | code-generation | Story+Spec → Code+Tests |
| **Review Agent** | Service Task | code-review | PR → Review+Approval |

Naming: `topic={domain}-{agent-type}` routes jobs to correct worker pool.

### 4.4 Human ↔ Agent Handoff Rules

| Scenario | BPMN Pattern | Implementation |
|----------|-------------|----------------|
| **Agent needs approval** | User Task after Service Task | XOR: confidence >= 0.9 auto-advance, else User Task |
| **Human delegates to agent** | Service Task assigned via form | User Task form: "assign to agent" button triggers subprocess |
| **Agent exception** | Boundary Error Event on Service Task | Error code → escalation path (Manual Task) |
| **Human overrides** | Terminate End Event on agent subprocess | Signal Event: human sends, agent subprocess terminates |
| **Collaborative design** | Ad-Hoc Subprocess (CMMN) | User Tasks + Service Tasks in any order until milestone |

**Design principle**: Agents = autonomous external workers (Zeebe external task pattern). Engine queues jobs even if agent is down.



## 5. Applying BPM to Pauls Converged Framework

### 5.1 Full Pipeline Model

The OKR → GA pipeline as a BPMN collaboration between Pools:

Pool: "Executive / Strategy"
  Start → [Define OKRs] → Message Flow →
Pool: "Agent System"
  → Receive OKR → [PRD Agent] → [Architecture Agent] → [UX Agent] → [API Contract Agent]
  → Message Flow (Artifacts: PRD + ADR + UI Specs + API Specs) →
Pool: "Stream-Aligned Team"
  → Receive Package → [Team Assignment] → [DAG Orchestrator] →
Pool: "Platform Team (CI/CD)"
  → [CI Pipeline] → [CD Pipeline] →
Pool: "Production Readiness Board"
  → [Production Readiness Review] → End (GA Release)

### 5.2 BPMN Element Mapping

| Stage | BPMN Element | Rationale |
|-------|-------------|-----------|
| OKR Definition | Start Event (Timer quarterly) + User Task | Periodic business cycle, human decision |
| PRD Generation | Service Task (topic: agent-prd) + Boundary Timer | Agent generates, timer prevents infinite runs |
| PRD Review | User Task (PM) + XOR Gateway | Approve/Revise/Reject |
| Architecture Design | Business Rule Task (DMN) + CMMN Case | Structured tech choices + unstructured exploration |
| UX Design | Service Task (agent-ux) + User Task review | Agent generates, human approves |
| API Contract | Service Task (agent-api-contract) | Spec-first, atomic output |
| Team Assignment | Business Rule Task (DMN) | Automated routing based on system affinity |
| DAG Orchestrator | Ad-Hoc Subprocess + Parallel Gateways | Each DAG level = parallel fan-out, sequenced by level |
| CI Pipeline | Send Task (webhook) + Catch Event (callback) | Async: fire CI, wait for result |
| CD Pipeline | Transaction Subprocess | Atomic deployment with rollback compensation |
| Production Readiness | Business Rule Task (DMN) + User Task (Go/No-Go) | Automated checks + human final signature |
| GA Release | End Event (Message) | Notify stakeholders + systems |

### 5.3 DAG Orchestrator → BPMN Subprocess

The BMAD DAG level-by-level execution maps to nested Parallel Gateways:

```
Ad-Hoc Subprocess: "Execute DAG"
  |
  [Initialize DAG]
  |
  Parallel Gateway (AND) ----------------------------
  |              |              |                    |
  [Node A L1]   [Node B L1]   [Node C L1]   [Node D L1]
  |              |              |                    |
  Parallel Gateway (AND) <----------------------------
  |
  Parallel Gateway (AND) ----------------------------
  |              |              |
  [Node E L2]   [Node F L2]   [Node G L2]
  |              |              |
  Parallel Gateway (AND) <----------------------------
  |
  ... (repeat for each DAG level)
  |
  [Collate Results] → End
```

**Key insight**: Each DAG level = Parallel Gateway fan-out. The DAG induction agent determines level structure dynamically. BPMN uses a loop counter (current_level) incrementing after each level completes.

**Dynamic DAG Execution** (Camunda Multi-Instance pattern):

Subprocess: "Execute DAG Level" (Multi-Instance, Sequential)
- Input: dag_levels (collection of level node arrays)
- Body: Parallel Gateway → Service Tasks (topic: dag-executor) → Parallel Gateway fan-in
- After level complete: increment counter, loop if more levels

### 5.4 CMMN for Unstructured Phases

CMMN (Case Management Model and Notation) is designed for unpredictable, knowledge-intensive work:

| Phase | BPMN Limitation | CMMN Solution |
|-------|----------------|---------------|
| DAG Induction | Hard to sequence — deps emerge during discovery | Case: "Discover Dependencies" with discretionary tasks: Analyze Codebase, Review PR History, Trace System Calls |
| Architecture Design | Fixed sequence cant capture iteration | Case: "Design Architecture" entry: PRD Approved. Tasks in any order: Draft ADR, Run POC, Review NFRs, Document Trade-offs |
| Discovery/Spikes | Rigid sequence flow | Milestone-driven: "Architecture Validated" fires when POC Complete AND ADR Approved AND Trade-offs Done |
| Incident Response | BPMN for runbook, CMMN for diagnosis | CMMN: "Investigate Incident" — tasks appear based on initial diagnosis |

**CMMN Key Concepts:**
1. **Case Plan Model**: Overall case (e.g., "Feature Architecture Discovery")
2. **Stages**: Required (must complete) vs Discretionary (optional)
3. **Plan Items**: Tasks (human/agent), Milestones, Events
4. **Entry/Exit Criteria**: Conditions that activate/deactivate stages
5. **Sentry**: Conditions controlling task activation — "If POC Complete AND Confidence > 0.7, activate Finalize ADR"

**Hybrid Design**: CMMN wraps exploratory phases; BPMN wraps deterministic pipeline. Handoff: CMMN milestone "Design Complete" triggers BPMN Start for "API Contract Generation".

---
## 6. Process Architecture for Agentic Systems

### 6.1 Service Tasks → Agent Invocations

External Task Pattern = canonical pattern for agent integration:

```
BPMN: Service Task | Type: external | Topic: code-generation
  Variables In: story, spec | Out: code, tests | Retries: 3 | Timeout: 120s

Agent: Worker subscribes to topic "code-generation"
  On job: 1. Parse variables → 2. Invoke LLM → 3. Validate output → 4. Complete/fail

Zeebe: Job Queue with topics (prd-generation, architecture-design, code-generation, code-review...)
  Workers subscribe via gRPC
```

**Benefits for agents:**
- **Decoupled**: Any language, any deployment
- **Resilient**: Jobs queue if agent is down; engine retries on timeout
- **Scalable**: Multiple agent instances subscribe to same topic (competing consumers)
- **Observable**: Engine tracks job state (created, locked, completed, failed)
- **Long-running**: Engine supports long-polling with heartbeats

### 6.2 Monitoring (Business Activity Monitoring)

| BAM Capability | Source | Agent System Implementation |
|---------------|--------|---------------------------|
| Process Status | Process lifecycle | Dashboard: active pipelines, current DAG level, time per level |
| Task Status | Job status per Service Task | Per-agent queue depth: pending, in-progress, completed, failed |
| Cycle Time | Event timestamps | Lead time OKR→GA; per-level DAG execution time |
| Bottlenecks | Wait times between activities | Stall detection (usually: human review gates, low-confidence agents) |
| Error Rate | Error events, escalation paths | Agent failure rate, retry frequency, escalation count |
| SLO Compliance | Timer events, deadlines | % pipelines completing within target time |

**Camunda + Prometheus/Grafana**: Camunda exposes metrics via Micrometer:
- `camunda_job_executor_{topic}_jobs` — queue depth per agent topic
- `camunda_process_instance_duration_seconds` — pipeline duration histogram
- `camunda_incidents_total` — unresolved escalations

### 6.3 Process KPIs → DORA & Flow Metrics

| Metric | BPMN KPI | Measurement |
|--------|----------|-------------|
| **Deployment Frequency** | Process Instance Count / Time | Instances reaching "Deploy to Production" End per day/week |
| **Lead Time for Change** | Total Duration | Timestamp delta Start→GA Release End |
| **Change Failure Rate** | % with Error paths | Instances with Error End/Escalation within 24h of release |
| **MTTR** | CMMN Case Duration | Time from "Incident Detected" to "Service Restored" milestones |
| **Flow Velocity** | Tasks Completed / Time | Service Tasks completing per hour (all pipelines) |
| **Flow Efficiency** | Active Work / Total Cycle | Sum(Service Task durations) / total duration (excludes wait time) |
| **Flow Distribution** | % by feature type | Instances per variable: new feature, bug fix, tech debt, experiment |
| **Flow Load** | Active Instances | Current running instances (= WIP) |

**Operationalize**: Deploy BPMN with timestamps on all Start/End events. Export to warehouse. Compute DORA metrics via SQL.

### 6.4 BPMN ∩ CI/CD

**Can BPMN model a CI/CD pipeline? Yes — up to a point.**

| Aspect | BPMN | CI/CD Config |
|--------|------|-------------|
| Pipeline stages | Subprocess of stages | YAML (GitHub Actions, GitLab CI) |
| Decision gates | XOR gateways | if: conditions, when: clauses |
| Human approval | User Task w/ escalation | environment: prod w/ manual gate |
| Env config | NOT modeled | Env vars, secrets, matrix |
| Build commands | NOT modeled — BPMN says what, not how | run: npm build, Dockerfile |
| Artifact storage | Data Object reference | Registry config (ECR, Docker Hub) |
| Test execution | Service Task + DMN pass/fail | Test runner config |
| Rollback | Transaction + Compensation | Blue-green, canary |
| Infra provisioning | NOT modeled — Terraform | IaC step |

**The boundary rule:**
> BPMN models the WHAT and WHEN (flow, decisions, roles, handoffs). CI/CD configs implement the HOW (commands, environments, tooling).

**BPMN stops at:** build commands, test runner flags, container registries, env-specific vars, IaC, package managers.

**CI/CD stops at:** cross-team handoff logic, business rule changes, multi-pipeline deps, compliance audit trail, agent allocation decisions.

**Hybrid pattern:**
```
BPMN:
  Generate PRD → Service Task (PRD Agent)
  Code Gen → Service Task (Coding Agent)  
  Code Review → Service Task (Review Agent) + User Task (Senior Eng)
  CI Pipeline → Send Task (webhook trigger) + Catch Event (callback)
  Prod Release → DMN readiness + User Task (Release Mgr)
  GA Release → Send Task (Slack, Jira)

CI/CD (GitHub Actions):
  Trigger: webhook from BPMN
  Steps: Checkout → Install → Lint → Test → Build → Push → Callback webhook
```

---
## Summary: Architecture Principles

1. **BPMN as orchestration backbone** — Zeebe/Camunda 8 as process engine managing state, routing, and task assignment across agents and humans.

2. **DMN for multi-factor decisions** — Definition of Ready, Production Readiness, DAG ordering strategy, Agent Confidence thresholds. Decouples business logic from flow.

3. **CMMN for exploration phases** — DAG induction, architecture design, any phase where sequence isnt predetermined. CMMN milestones gate handoff to BPMN.

4. **Agents as external workers** — Service Tasks with External Task pattern. One Zeebe topic per agent capability. Human tasks as User Tasks with same interface contracts.

5. **RACI → Pool/Lane mapping** — Stream-Aligned Team = Pool (Accountable). Lanes = Responsible. Consulted/Informed = Message Flows. Agent lanes with escalation paths to human lanes.

6. **DAG → Parallel Gateway fan-out** — Each DAG level = multi-instance subprocess with parallel gateway. DAG induction agent outputs level structure as collection. Engine iterates levels sequentially, nodes within each level in parallel.

7. **CI/CD is a black box** — BPMN triggers CI via webhook, waits for callback. CI config handles all implementation details.

8. **DORA metrics from BPMN instrumentation** — Timestamps on every event. Warehouse export for Lead Time, Deploy Frequency, Change Failure Rate, MTTR. Flow Metrics from queue depths and task durations.

---
## References

- BPMN 2.0 Spec: OMG (2011), "Business Process Model and Notation Version 2.0"
- DMN 1.3 Spec: OMG (2019), "Decision Model and Notation Version 1.3"
- CMMN 1.1 Spec: OMG (2016), "Case Management Model and Notation Version 1.1"
- Silver, B. (2011), "BPMN Method and Style"
- Skelton, M. & Pais, M. (2019), "Team Topologies"
- Forsgren, N., Humble, J., Kim, G. (2018), "Accelerate" — DORA metrics
- Kersten, M. (2018), "Project to Product" — Flow Metrics
- Camunda Docs: https://docs.camunda.io
- Bizagi Modeler: https://www.bizagi.com/en/platform/modeler
- bpmn-js: https://bpmn.io
