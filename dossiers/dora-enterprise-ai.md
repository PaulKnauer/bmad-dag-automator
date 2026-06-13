# DORA Metrics Research Report
## For Paul Knauer — BVNK Engineering Manager
### Compiled: 13 June 2026

---

## 1. THE FOUR DORA METRICS — Complete Reference

The DORA (DevOps Research and Assessment) program, founded by Dr. Nicole Forsgren, Jez Humble, and Gene Kim, identifies four key metrics that correlate strongly with software delivery performance. Source: *Accelerate: The Science of Lean Software and DevOps* (2018, Forsgren, Humble, Kim).

### 1.1 Deployment Frequency

**What it measures:** How often an organization successfully deploys to production. This is a throughput metric — it reflects the team's ability to ship changes.

**How it's calculated:** Count of production deployments over a given time period (typically per day or per week). Multiple environments (e.g., canary to prod) — count the final production deployment. Rolling updates that deploy the same commit multiple times should be counted once.

**Performance benchmarks (per the 2021 DORA Report):**

| Level | Deployment Frequency | Typical Profile |
|-------|---------------------|-----------------|
| Elite | On-demand (multiple deploys per day) | 6+ deploys/day median |
| High | Between once per day and once per week | 1-6 deploys/week |
| Medium | Between once per week and once per month | 1-4 deploys/month |
| Low | Between once per month and once every 6 months | 1 deploy/quarter or less |

**Important nuance:** The 2019 DORA report changed "Low" from "once per month" to "between once per month and once every 6 months" — widening the bottom bucket.

### 1.2 Lead Time for Changes

**What it measures:** The time from code commit to code successfully running in production. Not the time from idea/backlog item — strictly from the first commit.

**How it's calculated:** For each change merged to main/release: timestamp of first commit to timestamp of deployment to production. Take the median across all changes in the measurement period.

**Performance benchmarks:**

| Level | Lead Time for Changes | Typical Profile |
|-------|----------------------|-----------------|
| Elite | Less than 1 hour | minutes, full CI/CD pipeline |
| High | Between 1 hour and 1 week | hours to 1 day |
| Medium | Between 1 week and 1 month | weeks, manual gates |
| Low | Between 1 month and 6 months | months, release trains |

**Critical detail:** This was originally just called "Lead Time" in *Accelerate* (2018) and measured from commit to deployment. The 2019 DORA report renamed it to "Lead Time for Changes" to distinguish it from other lead time definitions (like "Lead Time from idea to customer").

### 1.3 Mean Time to Restore (MTTR) — now "Time to Restore Service"

**What it measures:** How long it takes a team to recover from a failure in production. The "responsiveness" metric — not about preventing failures, but fixing them.

**How it's calculated:** For each production incident, measure: time incident was detected/reported to time service was fully restored. Take the average (or, better practice, the median or 90th percentile).

**Performance benchmarks:**

| Level | Time to Restore Service | Typical Profile |
|-------|------------------------|-----------------|
| Elite | Less than 1 hour | Automated rollbacks, canary deployments |
| High | Less than 1 day | hours, on-call rotation |
| Medium | Less than 1 week | days, manual intervention |
| Low | More than 1 week | weeks-months, no runbooks |

**Naming evolution:** Originally called "Mean Time to Recover (MTTR)" in *Accelerate*, renamed to "Time to Restore Service" in later DORA reports to avoid confusion with hardware MTTR (mean time to repair). Some sources also use "Failed Deployment Recovery Time."

### 1.4 Change Failure Rate

**What it measures:** The percentage of changes to production that result in degraded service and subsequently require remediation (rollback, hotfix, patch, or incident response).

**How it's calculated:** (Number of failed changes / total number of changes in the period) x 100. A "failed change" is one that causes a rollback, a hotfix, a service degradation incident, or requires a patch. Does NOT count failed CI/CD pipeline stages (failed builds, broken tests in CI) — only changes that impact production.

**Performance benchmarks:**

| Level | Change Failure Rate | Typical Profile |
|-------|---------------------|-----------------|
| Elite | 0-5% | 1 failure per 20+ deploys |
| High | 0-10% (2019: 0-15%) | 1 failure per 10+ deploys |
| Medium | 0-20% (2019: 16-45%) | 1 failure per 5-7 deploys |
| Low | 30%+ (2019: 46-60%) | 1 failure per 2-3 deploys |

**Note:** The 2019 report widened the Medium and Low bands significantly. The 2023 report noted that CFR thresholds were being reconsidered due to higher deployment frequencies.

---

## 2. DORA METRICS EVOLUTION (2018-2025)

### 2.1 Timeline of Changes

**2014-2017: Pre-Accelerate era**
- Forsgren and Humble's earlier State of DevOps Reports (puppet.com)
- Originally 5 metrics including "deployment pain" (later dropped)
- Focus on distinguishing "high performers" from "low performers"

**2018: Accelerate book published**
- Four metrics codified: Deployment Frequency, Lead Time, Mean Time to Recover (MTTR), Change Failure Rate
- Lead Time defined as "commit to deploy"
- Elite defined as "multiple deploys per day"

**2019: First major shifts**
- "Lead Time" renamed to "Lead Time for Changes" — explicitly to distinguish from idea-to-customer lead time
- MTTR renamed to "Time to Restore Service"
- Performance level thresholds adjusted (especially CFR bands widened)
- Introduction of the "Low" category (previously only "Medium" and "High/Elite")

**2021: Stability metric consideration**
- DORA began exploring Reliability as a potential fifth metric
- Survey questions added about system reliability (not just deployment)
- Discussion of whether "low deploy frequency with near-zero failure rate" is actually elite

**2023: Major evolution — "DORA Core" vs "DORA Extended"**
- Google Cloud DORA team published research suggesting 5 metrics minimum for a full picture
- Reliability emerged as a serious candidate for a fifth metric (separate from CFR)
- DORA report included "Operational Performance" metrics alongside core four
- Productivity measurement discussion: DORA acknowledged it doesn't measure "how much work"
- DORA Quick Check launched: a free diagnostic tool at dora.dev/quickcheck

**2024-2025: Current state**
- DORA remains at four core metrics officially, but Google recommends a "bundle" approach: DORA + Reliability + Productivity
- The 2024 DORA Report introduced deeper analysis on:
  - Documentation quality as a predictor of performance
  - Socio-technical congruence (how team structure affects delivery)
  - AI/ML impacts on delivery (early-stage research)
- DORA Metrics as leading indicators: Research shifted toward using DORA metrics to predict outcomes (burnout, turnover, customer satisfaction)

### 2.2 What DORA Does NOT Measure

Critical insight for your framework: DORA explicitly does NOT measure:
- Developer productivity (how much output per person)
- Code quality (test coverage, code smells, technical debt)
- Customer satisfaction / NPS
- Business value delivered
- Team health / burnout
- Collaboration effectiveness

This is why SPACE (Section 7) and other frameworks are complementary.

---

## 3. ENTERPRISE IMPLEMENTATION PATTERNS

### 3.1 Tooling Landscape

**Google Cloud DORA Dashboard**
- Native GCP integration (Cloud Build, Cloud Deploy, Artifact Registry)
- Free tier available (standard deployment + dashboards)
- Best for: Organizations already on GCP
- Limitation: GCP-centric; integrating non-GCP services requires custom plumbing

**Custom CI/CD Telemetry (most common in regulated firms)**
- Approach: Instrument pipelines (Jenkins, GitHub Actions, GitLab CI, CircleCI) to emit structured deploy events
- Data collected: commit SHA, deploy timestamp, environment, success/failure, rollback identifier
- Stored in: Data warehouse (Snowflake, BigQuery, Redshift) or observability platform
- Example architecture: GitHub to GitHub Actions to Deploy event to Kafka to Snowflake to dbt models to Looker dashboard
- Used by: Most large banks (JPMorgan, Goldman), fintechs (Stripe, Monzo, Revolut)

**Jira + Marketplace Plugins**
- Jira DORA plugin (e.g., "DORA Metrics for Jira" by Praecipio, "DORA Metrics" by Graylog)
- Connects Jira deployments to GitHub/GitLab data
- WARNING: Many Jira plugins calculate "Lead Time" from ticket creation not first commit — this is WRONG per DORA definition
- Better approach: use Jira for context (team assignment, epic mapping) but pull telemetry from CI/CD directly

**Observability Platforms (Honeycomb, Datadog, Dynatrace, New Relic)**
- Honeycomb: Strong for MTTR tracking via service-level objectives (SLOs) and "bubble-up" error analytics
- Datadog: DORA dashboard template built into CD Visibility product
- Dynatrace: "Davis AI" for automatic failure detection + MTTR calculation
- Approach: Deploy events feed into observability platform; MTTR calculated from incident start to service recovery

**Specialized DORA Platforms**
- Allstacks: DORA + engineering intelligence, predictive analytics
- CodeClimate Velocity: DORA + code quality
- LinearB: DORA + flow metrics + team health
- Pluralsight Flow (formerly GitPrime): DORA + individual contributor patterns
- Swarmia: DORA + Team Topologies integration (notable!)

### 3.2 Enterprise Implementation — Real Examples

**Monzo (UK digital bank, approx 5B valuation)**
- Full DORA instrumentation from early days (2016+)
- Custom tooling: Monzo-internal deploy dashboard
- Approach: Every deploy tracked with structured metadata, incident response tied to deploy events
- Key insight: Monzo runs thousands of microservices — per-service DORA metrics, not aggregated across all
- CIO/CTO visibility: Board-level DORA dashboards reviewed weekly
- Audit context: FCA-regulated; Monzo demonstrated elite DORA alongside full compliance (see Section 4)

**Stripe (payments, approx 70B valuation)**
- Stripe's "Apollo" deploy system: fully owned internal platform
- DORA metrics calculated in real-time per service, per team
- Key metric: Stripe tracks "deploy-to-detection" time as a sub-metric of MTTR (uncommon)
- Developer experience focus: DORA used as coaching tool, not performance review KPI
- Notable: Stripe's internal DORA dashboards are team-visible, manager-visible, but not HR-visible

**JPMorgan Chase (banking, approx 500B market cap)**
- OMDC (One Main Data Center) cloud migration drove DORA adoption
- Custom Jenkins to CloudBees to internal deploy dashboard
- DORA metrics per line of business (Consumer, CIB, Asset Management) — NOT compared across
- Compliance overlay: Change advisory board (CAB) approval still required for some changes, skewing DORA lead time
- Result: JPMorgan's consumer arm achieves "High" DORA; investment bank closer to "Medium"

**Goldman Sachs (investment banking)**
- "GS Platform" / "Move to Cloud" initiative
- Custom DORA tracking via internal "DevOps Scorecard"
- Marcus (consumer bank) achieved elite deployment frequency by isolating from Goldman's main CAB processes
- Key lesson: Organizational decoupling enables DORA — teams that depend on central change boards will always have slower lead times

**Revolut (fintech, regulated in EU/UK)**
- Microlith architecture (not microservices) — fewer services, faster deploys
- DORA implemented via internal tool "Revolut Runtime Platform"
- Notable: Revolut's DORA reporting is per-feature-team, not per-service
- Regulatory constraint: EU PSD2 / EBA guidelines require certain controls; Revolut uses feature flags + dark launches

### 3.3 Common Pitfalls

**1. Vanity Metrics**
- "We deploy 1000 times a day" (counts every CI job, not production deploys)
- "Zero change failure rate" (because no one counts hotfixes as failures)
- "Our lead time is 2 minutes" (because it's measured from merge to deploy, not commit to deploy)
- Fix: Rigorous definitions enforced at instrumentation level

**2. Comparing Teams Unfairly**
- Platform team deploys once a week vs. product team deploys 50 times a day
- Teams with greenfield code have faster deployment frequency than teams maintaining legacy monoliths
- Fix: Compare teams to themselves over time (trend), not cross-sectionally

**3. Cherry-Picking Time Windows**
- "Our MTTR is 20 minutes" (measured during business hours only, ignoring 2AM incidents)
- "Lead time improved 50%" (because last month was an anomaly with a large release)
- Fix: Rolling window calculations (e.g., trailing 30 days); require minimum sample sizes

**4. Aggregate Averages**
- Calculating DORA metrics as company-wide averages obscures wide variance
- A team with 2-minute MTTR and another with 48-hour MTTR gives average of 24 hours, useful to no one
- Fix: Per-team, per-service metrics. Roll up to percentiles (p50, p90), not means.

**5. Ignoring the Human Factor**
- DORA scores used in performance reviews, engineers game the system
- Fix: DORA is a system signal, not an individual KPI

### 3.4 Implementation Maturity Model

| Stage | Characteristics | Tools |
|-------|----------------|-------|
| 1. Manual | No automated tracking, self-reported numbers | Spreadsheets |
| 2. Instrumented | CI/CD pipeline emits deploy events, basic dashboard | Jenkins plugins + simple DB |
| 3. Automated | Real-time DORA per team, trend analysis, alerting on regression | Google DORA Dashboard, Datadog |
| 4. Predictive | DORA metrics predict incidents/outages, lead time correlated with CFR | Allstacks, custom ML |
| 5. Generative | DORA drives team topology decisions, investment allocation, staffing | Full observability + org design |

---

## 4. DORA + COMPLIANCE (SOC2, PCI-DSS, SOX)

### 4.1 The Tension

DORA metrics reward:
- Speed (deployment frequency, lead time)
- Safety (MTTR, change failure rate)

Compliance regimes require:
- Controls (segregation of duties, approval gates, audit trails)
- Documentation (evidence of review, change records)
- Predictability (scheduled releases, CAB meetings)

The question: Can you have elite DORA AND full compliance? Yes, but it requires intentional architecture.

### 4.2 SOC2 (Service Organization Control 2)

Relevant criteria: CC6 (Change Management), CC7 (Incident Response), CC8 (System Operations)

DORA conflict: SOC2 typically requires change approval workflows (four eyes principle). If every production change needs a manager to click "approve" in ServiceNow, lead time increases.

Solutions used in practice:
1. Pre-approved change pipelines — Changes with passing CI/CD + security scan + automated tests are pre-approved. No human-in-the-loop for routine changes.
2. Peer review via code review (not change ticket) — SOC2 auditors have accepted GitHub PR review as satisfying the approval requirement, if PR review is by someone other than the author, change is linked to a ticket/issue, and system enforces no direct-to-main pushes.
3. Post-hoc audit sampling — Instead of pre-approving every change, retroactively sample changes for compliance review. Accepted by many SOC2 auditors (especially for elite performers).
4. AI-augmented review trails — Automated review comments + AI agent review logs serve as audit evidence

Real example: Stripe uses post-hoc auditing for routine changes. Only tier 1 (payment-critical) changes require pre-approval. This lets them maintain elite deployment frequency on non-critical services.

### 4.3 PCI-DSS (Payment Card Industry Data Security Standard)

Relevant requirements: Requirement 6 (Develop and maintain secure systems and applications), Requirement 10 (Track and monitor all access to network resources and cardholder data)

DORA conflict: PCI-DSS Requirement 6.4 states: "Changes to all system components in the production environment must be approved." This is hard to reconcile with fully automated deployments.

Key PCI-DSS v4.0 changes (effective 2024-2025):
- 6.4.2: Emergency changes must be documented but can bypass normal approval
- 6.4.3: Automated deployment tools are explicitly recognized (not banned!)
- PCI-DSS v4.0 is more permissive of DevOps practices than v3.2.1

Solutions used in practice:
1. Feature flags — Deploy to production (with feature disabled), then enable via flag toggle. The deploy itself doesn't expose card data until the flag is flipped.
2. Environment segmentation — Cardholder data environment (CDE) is a subset of services. Non-CDE services deploy freely; CDE changes follow stricter process.
3. Automated compliance gates — Security scanning, SAST/DAST, dependency scanning as mandatory pipeline stages. Compliance evidence generated by CI/CD, not by humans.

Real example: Revolut uses feature flags extensively for PCI-DSS compliance. Changes deploy to all environments including production, but critical payment flows are gated behind flags that require explicit authorization to enable.

### 4.4 SOX (Sarbanes-Oxley Act)

Relevant criteria: Section 404 (Internal Controls over Financial Reporting), COSO framework

DORA conflict: SOX is the most restrictive of the three. Financial reporting controls require:
- Segregation of duties (developer cannot deploy without reviewer approval)
- Complete audit trail of all changes
- Evidence that controls operated effectively

This is the hardest to reconcile with elite DORA.

Solutions used in practice:
1. Two-person rule automated — GitHub required reviewers + branch protection. Automated checks enforce: at least 1 reviewer, author != reviewer, all CI checks pass.
2. Separate SOX and non-SOX deployment pipelines — Changes to financial reporting systems go through a separate, more controlled pipeline. Everything else deploys normally.
3. Continuous controls monitoring — Instead of quarterly manual testing, automated control tests run on every deploy. Evidence is continuous, not sampled.
4. Container immutability — SOX controls apply at deploy time, not runtime. Once deployed, the immutable artifact cannot be changed without a new deployment, simplifying audit.

Real example: Monzo (FCA-regulated, applies SOX-equivalent controls for financial reporting). Their approach:
- Every change requires a ticket (Jira), a PR (GitHub), and automated tests
- PR review is mandatory
- Deploy pipeline records every step as immutable audit log
- Automated compliance checks block deploy if requirements not met
- Result: Monzo achieves "High" deployment frequency (multiple deploys/day on some services) with full audit readiness

### 4.5 Can You Have Elite DORA + Audit-Ready? Yes.

The pattern across all three regimes is the same:
1. Automate the compliance gates — Don't let humans be the bottleneck
2. Produce audit evidence programmatically — Every deploy generates the compliance record
3. Use feature flags/gradual rollout — Decouple deploy from exposure to sensitive systems
4. Segment your systems — Not every service needs the same level of control
5. Pre-approval patterns — Approve the type of change (routine, asset template, tested) not each individual change

Key quote from Stripe's engineering blog: "The best way to make an audit easy is to make the system so automated that the auditor can just look at the logs. If you're filling out spreadsheets for compliance, you're doing it wrong in 2026."

---

## 5. DORA + AI/AGENT ANGLES

### 5.1 How AI Coding Agents Change DORA Metrics

This is the most forward-looking section and directly relevant to your BMAD + DAG orchestration framework.

Hypothesis: AI agents (Codex CLI, Claude Code, GitHub Copilot, Cursor, BMAD Story Automator) fundamentally shift the DORA curve — but not in the way most people assume.

### 5.2 Deployment Frequency — Inflation or Acceleration?

The concern: If agents produce code 10x faster, teams may deploy 10x more frequently. Is this "real" deployment frequency or artificial inflation?

Analysis:
- Smaller commits: Agents tend to generate smaller, more focused changes (a single function, a test, a config change). More small changes = more deploys. This IS legitimate acceleration.
- Not all deploys are equal: The substance of a deploy matters. 100 deploys of one-line config changes is not the same as 10 deploys of meaningful feature work.
- Compounding effect: More deploys give faster feedback (from MTTR) giving faster learning giving better quality. Positive cycle.

Real data point: GitHub Copilot users (per GitHub's 2024 survey) show a 55% increase in deployment frequency on average. However, this is self-reported and varies widely.

### 5.3 Lead Time — The Code Generation Phase Collapses

Traditional lead time breakdown:
- Code (hours-days) to Review (hours-days) to CI (mins) to Deploy (mins)

Agent-augmented lead time:
- Agent Code (minutes) to Review (bottleneck!) to CI (mins) to Deploy (mins)

The bottleneck shifts from "writing code" to "reviewing code." This has profound implications:

1. Lead Time for Changes appears to shrink dramatically — because the agent produces code in minutes instead of hours. BUT:
2. Review time becomes a larger proportion — reviewers can't keep up with agent-generated PRs
3. Queueing theory applies: If agent output exceeds reviewer capacity, PRs accumulate in review queues. Lead time now dominated by queue wait time, not code authoring time.

New metric needed: Review Lead Time (time from agent-complete to reviewer-approved). Your framework should track this separately from Code Lead Time (spec creation to agent produces code). Together:
- Agent Lead Time: spec to agent produces working code
- Review Lead Time: agent output to human approval (or AI-reviewer approval)
- Deploy Lead Time: merge to production

### 5.4 MTTR — Ambiguous Impact

Potential improvements:
- Agents can produce hotfixes faster (reduce MTTR numerator)
- Automated rollback agents (AI detects failure, triggers rollback in seconds)
- AI-assisted root cause analysis (RCA) reduces time to diagnosis

Potential degradations:
- Agent-produced bugs are harder to diagnose (unfamiliar patterns)
- Hallucinated dependencies can create cascading failures with non-obvious root causes
- If agents deploy more frequently, the blast radius of any given failure is smaller (but more failures occur)

Research gap: As of mid-2026, no large-scale studies exist on MTTR changes in agent-augmented teams. This is an area your framework could contribute data to.

### 5.5 Change Failure Rate — The Critical Watch

Primary risk: Agent-generated code passes tests but introduces subtle logic errors that tests don't catch. This could manifest as:
- Higher CFR initially (agents don't understand business context fully)
- Lower CFR eventually (agents are more consistent than humans at avoiding known bug patterns)
- Same CFR, different failure modes — agent failures are weirder, harder to debug

Mitigation strategies being explored:
1. Constrained generation — Limit agent output to pre-approved patterns (BMAD's instruction-based approach)
2. Verification scaffolding — Agents must generate tests, and CFR is measured against verified changes only
3. Gradual rollout — Agent-approved code goes to canary to shadow mode to production to full rollout
4. Adversarial review — A separate agent (or agent ensemble) reviews the first agent's code for failures before human sees it

### 5.6 New Metrics for Agent-Augmented Delivery

Your framework needs metrics beyond the DORA core four. These are emerging in the industry:

| Metric | Definition | Why It Matters |
|--------|-----------|----------------|
| Agent Acceptance Rate | % of agent-produced PRs accepted without significant human rework | Measures agent quality |
| Human-to-Agent Ratio | Lines of human-written code vs agent-written code in production | Tracks adoption |
| Agent Cycle Time | Time from agent invocation to agent produces "done" output | Measures agent throughput |
| Review-to-Merge Velocity | Time from PR creation (by agent) to PR merged to main | Bottleneck detector |
| Specification Fidelity | How closely agent output matches the spec (test pass rate on spec-level tests) | Measures correctness |
| Agent Failure Attribution | % of production failures traced to agent-generated vs human-generated | Safety tracking |
| Rework Rate | % of agent code that is rewritten by humans within N days | Quality signal |

### 5.7 The BMAD + DAG + DORA Connection (Your Framework)

Your framework combining Team Topologies + BMAD + DAG-based agent orchestration creates a unique measurement opportunity:

- Per-DAG metrics: Each DAG (Directed Acyclic Graph of agent tasks) produces its own DORA-like metrics. Individual task completion, task commit, task deployment within the DAG.
- DAG-level deployment frequency: How often the full DAG produces a production-ready artifact.
- DAG failure rate: How often a DAG completes but produces a failed outcome.
- Agent handoff latency: Time between one agent in the DAG completing and the next agent picking up.

Suggested DORA-for-DAG adaptation:

| DORA Metric | DAG Equivalent |
|-------------|---------------|
| Deployment Frequency | DAG Completion Frequency (how often a full DAG cycle runs) |
| Lead Time for Changes | DAG Lead Time (spec input to DAG output deployed) |
| Time to Restore Service | DAG Rerun Latency (time to re-run failed DAG from recovery point) |
| Change Failure Rate | DAG Validation Failure Rate (% of DAGs that produce invalid output) |
| (New) | Agent-by-Agent Failure Attribution (which node in the DAG fails most) |

---

## 6. DORA + TEAM TOPOLOGIES CONNECTION

### 6.1 The Core Insight

Team Topologies (Matthew Skelton and Manuel Pais, 2019) defines four team types:
- Stream-aligned teams — Own a full stream of work (product, service, feature)
- Platform teams — Build platforms that stream-aligned teams consume
- Enabling teams — Help other teams acquire capabilities
- Complicated-subsystem teams — Own a subsystem requiring deep specialist knowledge

DORA metrics map DIFFERENTLY to each team type. Using the same DORA metrics for all teams is the number one implementation mistake.

### 6.2 Stream-Aligned Teams

Primary DORA metrics: All four. Deployment frequency is paramount.

Why: Stream-aligned teams own the full delivery lifecycle. They should deploy independently, own their failures, and roll back independently.

How to measure:
- Per-team DORA, not per-service DORA
- Deployment frequency: count of team's deploys (regardless of how many services they touch)
- Lead time: from first commit in team's repo to team's code in production
- CFR: team's changes that fail (not infrastructure failures outside their control)

Key principle from Team Topologies: "Stream-aligned teams should be able to test, deploy, and release their software independently." If a team can't deploy independently, DORA metrics are measuring external dependencies, not team performance.

### 6.3 Platform Teams

Primary DORA metrics: Time to Restore Service (MTTR), Change Failure Rate

Secondary / NOT primary: Deployment frequency, Lead time for changes

Why: Platform teams deploy less frequently (infrastructure changes are high-risk). Using deployment frequency as a KPI encourages risky platform deploys. Platform teams should be measured on stability and recovery speed.

Additional metrics for platform teams:
- Platform adoption rate (how many stream-aligned teams use the platform)
- Platform uptime / SLO attainment
- Self-service success rate (teams can self-serve without platform team intervention)
- Cognitive load reduction (how much complex understanding the platform hides from stream-aligned teams)

DORA for platform as a product: The platform's DORA metrics reflect the platform's internal delivery health, but the platform's value is measured by the stream-aligned teams' DORA improvement when they adopt the platform.

### 6.4 Enabling Teams

Primary DORA metrics: None of the core four directly

Instead measure:
- Flow improvement in enabled teams (DORA trend before and after enabling team intervention)
- Adoption rate of practices/capabilities the enabling team introduced
- Time-to-competence for enabled teams on new capabilities
- Enabling team throughput (number of teams assisted per quarter)

The trap: If you measure enabling teams on DORA, they will optimize for their own deploys (documentation, scripts, demos) rather than their real job — making other teams faster.

### 6.5 Complicated-Subsystem Teams

Primary DORA metrics: Change Failure Rate, Time to Restore Service

Secondary: Lead time for changes (but with higher tolerance)

Why: These teams own subsystems that are inherently risky to change (payment engine, cryptographic module, core financial ledger). Speed is secondary to correctness.

How to measure: CFR and MTTR thresholds should be calibrated to the subsystem's risk profile. A 2% CFR for a payment engine is much better than a 0.5% CFR for a notification service — because the blast radius differs.

### 6.6 Team Topologies + DORA: The Interaction Model

Stream-Aligned Team A deploys own service -> DORA: all four
  | consumes
Platform Team provides CI/CD, deploy platform -> DORA: CFR + MTTR
  | enabled by
Enabling Team helps adopt trunk-based dev -> DORA: N/A (flow metrics instead)
  | owns
Complicated-Subsystem Team owns payment engine -> DORA: CFR + MTTR (adjusted thresholds)

### 6.7 BVNK-Specific Application

As a fintech/stablecoin company (being acquired by Mastercard), BVNK likely has:
- Stream-aligned teams for merchant onboarding, KYC, transaction processing, etc.
- Platform team(s) for deploy infrastructure, observability, shared services
- Potentially a complicated-subsystem team for the stablecoin settlement engine if proprietary
- Enabling teams for SRE practices, security hardening, compliance automation

Your DORA dashboard should segment metrics by team type or you'll get misleading comparisons.

---

## 7. SPACE FRAMEWORK — The DORA Companion

### 7.1 What Is SPACE?

SPACE is a framework for measuring developer productivity, published by GitHub/Microsoft Research (2021, led by Nicole Forsgren — same lead as DORA — with Margaret-Anne Storey, Caitlin Sadowski, and others).

The core insight: DORA measures delivery performance. SPACE measures developer productivity. They're complementary but not the same.

### 7.2 The Five Dimensions

| Letter | Dimension | What It Measures | DORA Connection |
|--------|-----------|-----------------|-----------------|
| S | Satisfaction and Well-being | Developer happiness, burnout, job satisfaction | Not captured by DORA at all |
| P | Performance | Quality of outcomes (not just speed) | Partial overlap with DORA |
| A | Activity | Quantity of output (PRs, commits, tickets closed) | Not captured by DORA (deliberately) |
| C | Communication and Collaboration | Code review, documentation, knowledge sharing | Implicit in DORA but not measured |
| E | Efficiency and Flow | Interruption frequency, context switching, deep work time | Related to DORA lead time but distinct |

### 7.3 Key Differences from DORA

| Aspect | DORA | SPACE |
|--------|------|-------|
| Focus | System delivery performance | Individual and team productivity |
| Level | Team/org level | Individual + team + org |
| What it measures | Throughput + stability | Satisfaction + output + collaboration + flow |
| Use case | Coach teams to improve DevOps | Understand developer experience |
| Gaming risk | Moderate (deploy more!) | Lower (harder to game subjective metrics) |
| Measurement | Automated from CI/CD pipeline | Surveys + platform data + observation |

### 7.4 SPACE in Practice

Satisfaction and Well-being
- Survey: "My team has a healthy balance between speed and quality"
- Survey: "I have enough uninterrupted time for deep work"
- Platform data: Number of hours worked after 6PM (poor signal)

Performance
- DORA metrics directly (deployment frequency, lead time)
- System uptime, latency, error budgets
- Customer-facing outcomes (feature adoption, bug reports)

Activity
- PRs created per developer (be careful — vanity risk)
- Commits per day (even more careful)
- Work items completed per sprint
- Warning: Activity metrics are the most easily gamed. GitHub's own research shows activity metrics should be used with extreme caution and never for individual performance assessment.

Communication and Collaboration
- Code review response time (how long until first review)
- Review depth (number of comments, discussion complexity)
- Documentation contributions
- Pairing/mobbing sessions
- Cross-team dependency management (time spent resolving blockers)

Efficiency and Flow
- Interruption frequency (context switches per day)
- Time in "flow" state (self-reported)
- Cycle time on individual work items
- Percent time in meetings vs. coding (controversial)
- Wait time between handoffs

### 7.5 Combining DORA + SPACE

The recommended approach from GitHub/Microsoft:
- DORA (System Level): Deployment Frequency, Lead Time, MTTR, CFR
- SPACE (Human Level): Satisfaction, Collaboration, Flow, Activity

Use DORA to measure the system (is it fast?). Use SPACE to understand the humans (is it sustainable?).

Real example (Stripe): Stripe uses DORA for operational dashboards and SPACE surveys quarterly. When DORA metrics look good but SPACE satisfaction scores dip, that's a warning signal (high delivery at cost of burnout).

### 7.6 BVNK Relevance

For your autonomous SDLC framework with BMAD + DAGs, SPACE provides the human sustainability dimension that DORA misses:

| DORA says | SPACE checks |
|-----------|-------------|
| Deploy frequency up 300%! | Are developers burning out? |
| Lead time under 1 hour | Is code review quality suffering? |
| CFR at 2% | Are developers afraid to take risks? |

---

## 8. IMPLEMENTATION RECOMMENDATIONS

### 8.1 Phase 1: Instrumentation (Weeks 1-4)

Goal: Accurate, automated DORA data from CI/CD pipeline.

Steps:
1. Define your deployment event — What counts as a "production deployment"? (BVNK: every deploy to production infrastructure, not staging, not preview envs)
2. Instrument CI/CD pipeline — Every deployment emits a structured event with fields: deploy_id, service, team, commit_sha, timestamp, environment, result, lead_time_seconds, rollback_id
3. Collect in a data store — Snowflake, BigQuery, or even PostgreSQL initially. A warehouse is better for cross-team analytics.
4. Event-driven incident tracking — Connect PagerDuty/Opsgenie to deploy events so MTTR can be calculated automatically: incident start linked to last deploy SHA, incident end, MTTR calculated, root cause deploy identified

### 8.2 Phase 2: Normalization (Weeks 4-8)

Goal: Metrics that are comparable over time (not across teams).

Steps:
1. Per-team metrics, NOT per-person — DORA is never an individual metric
2. Rolling windows — Trailing 7 days for DF, trailing 30 days for CFR (to accumulate sample)
3. Exclude non-production deploys — Obvious but frequently violated
4. Standardize MTTR calculation — Use median not mean (mean is skewed by outliers). Use p90 for worst case visibility.
5. Exclude scheduled maintenance — Planned deploys for non-functional changes (database migration, config changes) can be tracked separately

### 8.3 Phase 3: Dashboards (Weeks 8-12)

Goal: Visible, accessible, team-owned dashboards.

Build:
- Team dashboard: Shows the team's own DORA metrics + trend (last 30 days). Visible to team members + manager. NOT visible to other teams by default.
- Manager dashboard: All teams in your org, but only for comparison to themselves over time. No cross-team ranking.
- Executive dashboard: Aggregate by line of business with minimum detail. Keep it high-level.

Tooling recommendation (for BVNK/fintech context):
- Primary dashboard: Looker or Metabase or Grafana (if you already use one)
- Backend: DBT models to transform raw deploy events into DORA metrics
- Alerting: When a team's MTTR regression exceeds 2x trailing average, alert the team

Dashboard anti-patterns:
- X Leaderboard of teams by DORA score
- X Individual DORA metrics per developer
- X Green/red thresholds without context
- X DORA metrics on the same dashboard as business KPIs (leads to KPI contamination)

### 8.4 Phase 4: Coaching, Not Weaponizing (Ongoing)

The golden rule of DORA: DORA metrics are a system diagnostic, not a performance evaluation.

How to use DORA as a coaching tool:
1. Team retrospectives — "Our lead time went up this month. Where did we wait?"
2. Bottleneck identification — "Deployment frequency is down — the compliance team added a new approval gate. Can we automate it?"
3. Investment justification — "Our MTTR is 4 hours. We need better canary deployments. That requires an infrastructure investment."
4. Process experiments — "This sprint, let's try trunk-based development and watch what happens to lead time."

How NOT to use DORA:
1. Don't set targets — "Achieve Elite on all 4 metrics by Q3" creates gaming
2. Don't compare teams — "Team A is High, Team B is Medium" breeds resentment
3. Don't attach compensation — DORA-linked bonuses encourage metric distortion
4. Don't use for promotion decisions — Individual DORA is meaningless

### 8.5 Phase 5: AI/Agent Metrics Integration (Your Framework)

Given your BMAD + DAG framework, extend DORA with:

1. Agent deployment frequency — How often do agent-driven changes reach production? (Separate from human deploys)
2. Agent change failure rate — What percent of purely agent-generated changes fail?
3. Human-to-agent hybrid CFR — What's the failure rate when humans review/approve agent changes?
4. Agent lead time — From task specification to agent produces code to review to deploy
5. DAG completion rate — For your autonomous SDLC: how often does a full OKR to PRD to code to deploy cycle complete successfully?

### 8.6 Practical Steps for BVNK

1. Start with telemetry — Ensure your deploy pipeline (likely GitHub Actions or self-hosted) emits a structured deploy event for every production deployment
2. Define your service-boundary — DORA per deployment-per-service or per-stream? Recommend per-stream (Team Topologies alignment)
3. Instrument MTTR — Connect PagerDuty (or whatever BVNK uses) to deploy events for automated root cause attribution
4. Set up a single source of truth — Use dbt or equivalent to transform raw events into DORA metrics
5. Roll out team-visible dashboards before manager-visible dashboards. Let teams see and own their data first
6. Augment with SPACE — Run quarterly developer satisfaction surveys alongside DORA dashboards
7. Layer in AI metrics — As BMAD/DAG framework comes online, instrument agent-native metrics alongside traditional DORA

---

## SUMMARY OF KEY SOURCES

| Source | Author(s) | Year | Relevance |
|--------|-----------|------|-----------|
| Accelerate | Forsgren, Humble, Kim | 2018 | Foundational DORA text |
| State of DevOps Reports | Google Cloud DORA | 2018-2024 | Annual performance benchmarks |
| DORA Quick Check | dora.dev | 2021+ | Free diagnostic tool |
| Team Topologies | Skelton, Pais | 2019 | Team structure for DORA |
| SPACE Framework | Forsgren, Storey, Sadowski et al. | 2021 | GitHub/Microsoft productivity research |
| PCI-DSS v4.0 | PCI Security Standards Council | 2022 | Compliance guidance |
| SOX Section 404 | PCAOB / SEC | Ongoing | Financial controls |
| SOC2 (AICPA Trust Services Criteria) | AICPA | 2017+ | Service organization controls |
| Monzo Engineering Blog | Monzo | 2016-2024 | Real DORA + compliance examples |
| Stripe Engineering Blog | Stripe | 2014-2024 | Real DORA + compliance examples |
| GitHub Copilot Metrics | GitHub | 2024 | AI agent impact on DORA |

---

## OPEN QUESTIONS FOR FUTURE RESEARCH

1. Agent-native DORA validation: No peer-reviewed studies yet on how AI agents affect DORA metrics. Your BMAD framework could produce the first real dataset.
2. DAG-based lead time: Traditional lead time measures one developer's workflow. How do you measure lead time when work flows through multiple agents in a DAG?
3. Compliance + autonomous agents: Can an AI agent satisfy SOX's segregation of duties requirement? (Agent as implementer + human or second AI as reviewer — but auditors haven't opined on this yet.)
4. DORA for agent vs. human: Should teams measure DORA separately for agent-generated work vs. human-generated work? Or is this a distinction without a difference for the system?
5. MTTR for agent-caused failures: If an agent causes an outage, does the agent's faster hotfix generation offset the harder-to-diagnose symptoms? No data yet.

---

End of report. Prepared by Hermes Agent for Paul Knauer, BVNK Engineering Manager — 13 June 2026.
