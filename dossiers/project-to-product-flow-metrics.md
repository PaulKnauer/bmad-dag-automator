# Project to Product & Flow Metrics: Comprehensive Research Report


**Prepared for:** Paul Knauer, Software Engineering Manager, BVNK
**Date:** June 13, 2026
**Context:** Converged framework -- Team Topologies + BMAD + DAG-based autonomous orchestration

---

## Part 1: Mik Kersten's Project to Product (IT Revolution Press, 2018)

### 1.1 The Core Thesis

Kersten's central argument: The Project mindset is the enemy of value delivery in software.

**Project Mindset:** Success = On time, on budget, to scope. Fixed end date, then disband. Governance via milestones and gates. Handoffs between silos. Measures output (lines of code, story points). Cost center thinking.

**Product Mindset:** Success = Continuous value delivery. Ongoing evolution, persistent team. Governance via flow metrics and outcomes. End-to-end ownership. Measures outcome (customer value, business impact). Value stream thinking.

The Iron Triangle lie: Traditional project management measures against time, cost, scope. In software, scope is the variable that should flex. Measuring on-time/on-budget creates perverse incentives: teams ship buggy code to hit dates, accumulate debt to stay on budget, optimize for sign-off rather than user value.

Kersten's critique of ITIL/COBIT governance: these frameworks treat software like manufacturing. They measure utilization (are people busy?) rather than flow (is value moving?). Result: high utilization, zero throughput because everyone context-switches on multiple projects.

The Faster, Faster trap: when an organization optimizes solely for speed without balancing quality and risk, it slows down. Mirrors the Theory of Constraints applied to software value streams.

> *If you measure a product team like a project, you get project behavior. And project behavior is the opposite of what you need for continuous delivery.* -- Mik Kersten

### 1.2 The Flow Framework

Five types of flow items -- discrete units of work flowing through a value stream:

1. **Features** -- New functionality delivering value. Measured by: Feature acceptance rate, throughput per sprint.
2. **Defects** -- Things broken. Measured by: Defect arrival/closure/escape rates.
3. **Debts** -- Things needed to maintain future velocity (tech debt, process debt, architecture debt). Measured by: Debt count, aging, Debt-to-Feature ratio.
4. **Risks** -- Things that could cause future problems (security vulns, compliance gaps, SPOFs). Measured by: Risk count, aging, Mean time to remediate.
5. **Other** -- Catch-all: meetings, research spikes, ops tasks.

Each flow item tracked through the value stream with timestamps for Arrival, Start, Completion, and Blocked time.

### 1.3 The Four Flow Metrics

**Flow Velocity:** Number of flow items completed per unit time. Formula: Count / Time period. Measures raw throughput. Must track per item type. Kersten warns: velocity without distribution is dangerous.

**Flow Efficiency:** Ratio of active work time to total elapsed time. Formula: Active time / Elapsed time x 100%. Measures waste in the system. Benchmark: Most enterprises 5-15%, elite teams 40-60%.

**Flow Time (aka Cycle Time):** Total elapsed time from work start to completion. Formula: Completion - Start. Measures how fast items move through the system. Begins at work start, not arrival (different from Lead Time).

**Flow Distribution:** Proportion of each flow item type as % of total completed. Formula: Features completed / Total x 100% (repeat for Defects, Debts, Risks). Measures health and balance of the work portfolio.

### 1.4 Flow Distribution -- Why It Matters

Kersten's key insight: **The ratio of flow items is the single most important leading indicator of value stream health.**

Ideal targets: Features 40-50%, Defects 20-30%, Debts 15-25%, Risks 10-20%.

Warning signs: Defects > Features (firefighting death spiral). Debts < 10% (accruing unseen debt). Risks < 5% (ignoring security/compliance). If Defects + Debts + Risks > Features, more than half capacity is non-value-adding.

Red Light: Features 20%, Defects 50%, Debts 20%, Risks 10%. Green Light: Features 45%, Defects 20%, Debts 20%, Risks 15%.

For BVNK: Flow Distribution as capacity allocation signal. If DAG orchestrator spends 60% of cycles on agent-introduced defects, improve agent quality before adding features.

### 1.5 Connection to DORA Metrics

Flow Framework and DORA are complementary, not competing.
- DORA: Technical delivery performance. Deployment Frequency, Lead Time, MTTR, CFR. Level: Team/org capability. Focus: Speed + stability.
- Flow Framework: Value stream health and balance. Flow items by type. Level: Value stream/product. Focus: Balance + sustainability.

Overlap: Deployment Frequency ~ Flow Velocity. Lead Time for Changes ~ Flow Time. Change Failure Rate maps to Defect Flow Distribution. Time to Restore Service maps to Defect Flow Time.

Key difference: DORA measures the delivery pipeline (code to deploy). Flow Framework measures the entire value stream (idea to outcome), including discovery, design, risk management, debt -- things DORA doesn't capture.

Combined: DORA + Flow Framework = Complete picture. DORA tells you how fast. Flow tells you what you're delivering and whether it's sustainable.

### 1.6 The Faster, Faster Trap

When an organization optimizes solely for speed (Flow Velocity) without balancing Flow Distribution, it: (1) accelerates features at quality's expense, (2) accumulates debt, (3) loses sight of risk/compliance, (4) hits a wall where velocity collapses.

Mechanism: Go faster -> Skip testing -> More defects -> Defect distribution spikes -> Team context-switches to fix -> Feature velocity drops -> Go even faster -> System collapses -> Velocity = 0.

Solution is not to slow down. It's to balance the flow: allocate explicit capacity to debt/risk, measure Flow Distribution, use WIP limits.

### 1.7 Real Enterprise Examples

**CA Technologies (flagship case study):** 12-month release cycles, project-based measurement, massive debt. Transformation: mapped value streams (70% of flow items were Defects/Debt), set target distribution (50/25/15/10), reorganized into product teams. Results: throughput up 2-3x, defects down 50%, releases weekly.

**SAP:** Identified 60% of portfolio in maintenance mode. Rebalanced toward features and risk reduction.

**Large European bank:** 80% of flow items were compliance/risk related. Appropriate for context, but revealed true cost of compliance on innovation.

**Healthcare software:** Used Flow Distribution to justify debt reduction. Showed board 3-month investment would pay back in 6 months via regained feature velocity.

### 1.8 The Product-Centric Transformation Model

**Horizon 1 -- Visibility (0-6 months):** Instrument value streams, create CFDs, identify bottlenecks, calculate baseline Flow Distribution.

**Horizon 2 -- Alignment (6-18 months):** Reorganize into product teams, set Flow Distribution targets, implement WIP limits, connect to OKRs.

**Horizon 3 -- Autonomy (18+ months):** Self-managing teams own their flow within guardrails. Leadership focuses on strategic Flow Distribution. Psychological safety ensures problems are surfaced.

## Part 2: Beyond Kersten -- Modern Flow Metrics

### 2.1 DORA + Flow Framework Combined Measurement

The industry has converged on a hybrid model. Unified stack:

1. **Business Impact** (OKR attainment, Revenue per feature, NPS) -- Business -- Executives
2. **Value Stream Health** (Flow Distribution, Flow Efficiency) -- Flow Framework -- PMs/EMs
3. **Delivery Performance** (DORA: Deploy Freq, Lead Time, MTTR, CFR) -- DORA -- EMs/Tech Leads
4. **Operational** (P50/P95 latency, Error budget, Uptime) -- SRE -- Platform Team
5. **Team Health** (eNPS, Developer satisfaction, SPACE) -- HR/SPACE -- EMs

**North Star:** Sustainable Feature Velocity = Flow Velocity(Features) x (1 - Change Failure Rate)

### 2.2 Cycle Time vs Lead Time

**Lead Time:** Total time from request to delivery. Starts at ticket creation. Ends at production. Measures total customer wait time.

**Cycle Time:** Time from started to finished. Starts at work begins. Ends at production. Measures how fast the system processes work.

Why the confusion: Kanban/Lean originally defined Cycle Time as order-to-delivery (same as Lead Time). DORA uses 'Lead Time for Changes' which is closer to Cycle Time (commit to production). Flow Framework's Flow Time = Cycle Time.

Both matter: Cycle Time tells you if engineering is healthy. Lead Time tells you if prioritization/review is healthy. If Lead Time >> Cycle Time, the bottleneck is backlog management, not engineering.

### 2.3 Cumulative Flow Diagrams (CFDs)

A stacked area chart showing cumulative count of flow items by state (Backlog, In Progress, Review, Done) over time.

Reading a CFD:
- Vertical gap between bands = WIP
- Horizontal distance between bands = Cycle Time
- Widening gap = WIP growing faster than throughput (overloaded)
- Flat Done line = no deliveries (bad)
- Steep Backlog line = more arriving than completing

Starting WIP limit: 2-3 items per person.

### 2.4 Little's Law Applied to Software Delivery

Formula: Lead Time (or Cycle Time) = WIP / Throughput

Implications: (1) To reduce cycle time, reduce WIP or increase throughput. (2) Adding work to a full system doesn't increase throughput -- it increases WIP and slows everything. (3) WIP = Inventory. Partially-done features not deployed are waste.

Worked example: WIP=20, Throughput=10/week, Cycle Time=2 weeks. After WIP limit of 10: WIP=10, Throughput=10/week, Cycle Time=1 week. Halved by finishing before starting new work.

For agents: WIP = concurrent DAG nodes. Throughput = completed nodes per period. Increasing agent WIP without increasing capacity increases Cycle Time per node.

### 2.5 Queueing Theory for Engineering Teams

Core insight: Variability kills throughput.

Kingman's formula: Wait time ~ (Utilization / (1 - Utilization)) x Variability
- 0-50% utilization: low wait time
- 50-80%: climbing
- 80-90%: sharply rising
- 90%+: approaches infinity

The Utilization Trap: Keeping people at high utilization creates exponential wait times. Most productive team often looks underutilized because they have slack for variability.

For BVNK: Set WIP limits per DAG stage (max 3 agents parallel per value stream). Monitor queue depth. If wait times spike, reduce parallelism.

### 2.6 The SPACE Framework Connection

SPACE (Forsgren et al., 2021) adds the human dimension:
- **S**atisfaction & Wellbeing: eNPS, burnout risk. High Flow + low satisfaction = unsustainable.
- **P**erformance: System performance, availability.
- **A**ctivity: PRs, commits, deployments (Flow Velocity).
- **C**ommunication & Collaboration: Review time, dependencies (Flow Efficiency).
- **E**fficiency & Flow: Flow metrics themselves.

Insight: You can have excellent Flow/DORA metrics but terrible SPACE scores (burnout). Monthly developer satisfaction pulse + weekly flow metrics = complete picture.

## Part 3: Flow Metrics in an Agent-Augmented World

### 3.1 AI Agent Throughput

Does 10x agent code production make Flow Velocity meaningless?

1. Velocity is still meaningful as intra-system comparison (this week vs last week).
2. Agent-accelerated velocity masks debt accumulation. Agents generate Features but ignore Debt -- Flow Distribution skews toward Features+Defects.
3. Velocity must be quality-filtered: Net Feature Velocity = Gross Feature Velocity x (1 - Agent Error Rate).
4. Proposed correction: Standardized Flow Velocity = Flow Items Completed / Agent-Hour Equivalent.

### 3.2 Agent Flow Distribution

Two separate Flow Distributions required:

**Agent Flow Distribution (typical):** Features 50-70%, Defects 15-30%, Debts 5-10%, Risks 2-5%. Agents skew toward Features + Defects, underinvesting in Debt + Risk. Faster, Faster amplified 10x.

**Human Flow Distribution (agent-augmented):** Features 20-30%, Defects 25-35%, Debts 20-30%, Risks 15-25%. Humans shift from producing Features to curating the system -- reviewing agent output, managing debt and risk.

Target combined distribution should still match Kersten's ideal. It just changes who does what.

### 3.3 Agent Error Rates and Flow Distribution

Agent error 5%: acceptable, humans catch in review.
Agent error 15%: humans spend 30% of time fixing agent defects.
Agent error 30%: humans spend 60% fixing -> Defect Distribution dominates -> no capacity for Features/Debt/Risk -> rapid degradation.

Agent error rates compound non-linearly. Two 10%-defective agents can produce 25-30% interaction failures.

Health indicators:
- Agent Defects > 30% of total Flow Items: prompts/guardrails need improvement
- Agent Debt < 5%: agents not doing maintenance (bad)
- Human Debt + Risk < 30% of human time: humans doing too much Feature work

### 3.4 Measuring Agent Flow vs Human Flow Separately

Track each dimension for both:
- Flow Velocity: Items by humans / by agents / total
- Flow Time: Human start to completion / Agent launch to completion
- Flow Efficiency: Active human time vs elapsed / Agent compute vs wall clock
- Flow Distribution: Human items / Agent items / Overall
- Error Rate: Human defect rate / Agent defect rate / System CFR

Implementation: Tag each DAG node with executor_type (human/agent/hybrid), agent_model, agent_prompt_hash, human_review_required. Slice metrics by any dimension.

### 3.5 DAG Orchestrator Flow Metrics

- **DAG Flow Velocity:** Completed DAG nodes per hour. Measures orchestrator throughput.
- **DAG Flow Efficiency:** (Total compute across all agents) / (Wall clock x Parallelism limit).
- **DAG Flow Time:** DAG completion - DAG launch.
- **DAG Flow Distribution:** Proportion of DAG nodes by type.

Additional DAG metrics: Node Success Rate, Retry Rate, Human Handoff Rate, DAG Completion Rate, Agent Queue Depth, Agent Utilization.

**DAG North Star:** DAG Effectiveness = Feature Nodes Completed x (1 - Human Handoff Rate) / Agent-Hours Consumed

## Part 4: Measuring Success in Paul's Framework

### 4.1 Success at Each Layer

OKR -> PRD -> Architecture -> Team Assignment -> DAG Execution -> CI/CD -> Production Readiness

- **OKR:** Business outcomes achieved. Metric: OKR attainment (0-1.0). Quarterly review.
- **PRD:** Clear, testable, prioritized requirements. Metric: PRD quality score (1-5 rubric).
- **Architecture:** Design decisions enabling flow. Metric: Architecture fitness functions passing.
- **Team Assignment:** Right team for right work. Metric: Team-value stream alignment %. Team Topologies mapping.
- **DAG Execution:** Agents producing quality output efficiently. Metric: DAG Effectiveness, Node Success Rate, Human Handoff Rate.
- **CI/CD:** Fast, reliable, safe pipeline. Metric: DORA (Deploy Frequency, Lead Time, MTTR, CFR).
- **Production Readiness:** Stable, secure, observable. Metric: Error budget, SLO attainment, security scan pass rate.

Each layer's metric feeds the next. OKR attainment should correlate with Flow Distribution. Architecture fitness functions should predict CI/CD stability.

### 4.2 Bridging Business and Technical Metrics

Track X-Y correlations over time:
- Flow Velocity (Features) vs Revenue growth / feature adoption (positive lagging, 2-3 quarters)
- Flow Distribution (Defects %) vs Customer support tickets / NPS (negative correlation)
- Flow Time vs Time-to-market (direct correlation)
- Agent Error Rate vs Human review time / Defect escape rate (direct correlation)

For BVNK specifically:
- Feature Velocity -> New stablecoin protocol integrations per quarter
- Defect Flow Distribution -> Settlement errors per month (critical)
- Risk Flow Distribution -> Compliance audit findings, regulatory response time
- Debt Flow Distribution -> Time to add new supported currencies

### 4.3 Metrics as Coaching Tool, Not Weapon

Three principles:
1. Metrics are for learning, not evaluating. Flow Distribution is not a performance review tool.
2. The person doing the work sees the metric first. Team sees it before exec.
3. Pair a problem metric with a coaching question: 'Agent defect rate is 25% -- what's one thing we could change about prompts to reduce that?'

Do: Share with team before management. Ask what the metric tells us. Celebrate improvement trends. Let teams set targets.
Don't: Present as surprise. Ask who caused this. Compare teams publicly. Use as secret management tool.

### 4.4 Dashboard Recommendations

**Executive Dashboard (Monthly)** -- CTO, CPO, VP Eng: OKR attainment, Flow Distribution pie chart, Flow Velocity trend (12mo), DORA summary, DAG Completion Rate, Cost Efficiency.

**Engineering Management Dashboard (Weekly)** -- EMs, Tech Leads, PMs: Flow Distribution per value stream, Flow Time P50/P85/P95, Flow Efficiency, DORA all four, Agent Flow Distribution, Agent Error Rate, WIP by stage, top blocking dependencies.

**Team Dashboard (Daily)** -- Individual teams: Live CFD, WIP vs WIP limit (traffic light), Flow Time for in-progress items, blocked items count+age, agent tasks in queue, human handoff items with age.

**Agent System Dashboard (Ops)** -- Platform Engineering: DAG Completion Rate (24h), Node Success Rate, Retry Rate, Human Handoff Rate, Agent Queue Depth, Agent Utilization, Avg Node Flow Time, Agent Cost per Node, Flow Distribution by Model, Error Rate by Prompt Template.

## References

### Books
1. Kersten, Mik. *Project to Product*. IT Revolution Press, 2018.
2. Forsgren, Nicole, et al. *Accelerate*. IT Revolution Press, 2018.
3. Reinertsen, Donald G. *The Principles of Product Development Flow*. Celeritas Publishing, 2009.
4. Goldratt, Eliyahu M. *The Goal*. North River Press, 1984.

### Papers
5. Forsgren, N., et al. 'Elevating the Debate on Developer Productivity.' (SPACE Framework), ACM Queue, 2021.
6. DORA (Google Cloud). 'State of DevOps Report.' 2014-2024 editions.
7. Little, J.D.C. 'A Proof for the Queuing Formula: L = W.' Operations Research, 1961.
8. Kingman, J.F.C. 'On the Algebra of Queues.' Journal of Applied Probability, 1966.

### Tools
9. LinearB -- Flow metrics tooling (flowvelocity.dev)
10. Swarmia -- Engineering analytics platform (DORA + Flow)
11. Code Climate Velocity -- Engineering management platform
12. Allstacks -- Value stream intelligence

## Summary of Key Recommendations for Paul's Framework

1. **Track Flow Distribution as the primary health metric.** Both human and agent. If agent-heavy distribution skews toward Features+Defects and away from Debt+Risk, intervene.

2. **Use DORA for delivery pipeline, Flow Framework for value stream balance.** Deploy them together.

3. **Separate Agent Flow from Human Flow in all metrics.** Tag every DAG node by executor type.

4. **Apply Little's Law to agent compute.** Set WIP limits on parallel agent execution.

5. **Build coach-not-weapon culture.** Team-facing dashboards first. Ask 'what can we learn?' not 'who is responsible?'

6. **Bridge layers with correlation analysis.** Track OKR attainment alongside Flow Distribution.

7. **The DAG orchestrator's North Star:** DAG Effectiveness = Feature Nodes Completed x (1 - Human Handoff Rate) / Agent-Hours Consumed
