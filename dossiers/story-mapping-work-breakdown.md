# Research: Story Mapping (Patton) + User Stories (Cohn) → Work Breakdown for Agentic Development

> Prepared for Paul Knauer — BVNK fintech context: Team Topologies + BMAD + DAG-based autonomous agent orchestration
> Research date: June 2026

---

## 1. Jeff Patton's User Story Mapping (2014)

### 1.1 Core Technique: The Story Map Structure

Patton's *User Story Mapping* (O'Reilly, 2014) solves a fundamental problem with flat product backlogs: **they destroy the narrative context of the user journey**. A flat backlog is a list of independent items sorted by priority — but user experiences are not linear, independent stacks; they are connected workflows.

**The story map has three structural layers:**

| Layer | Patton's Term | What It Holds | Analogy |
|-------|---------------|---------------|---------|
| Top row | **The Backbone** | High-level user activities (the "steps" the user takes through the journey) | The chapters of a book |
| Second row | **The Walking Skeleton** | One thin, end-to-end slice through every backbone activity that delivers real value | A single complete chapter read end-to-end |
| Below | **Detailed stories** | All the variations, edge cases, error handling, and nice-to-haves beneath each backbone activity | The paragraphs, footnotes, and appendices per chapter |

**Step-by-step construction process (Patton's standard workshop):**

1. **Map the backbone** — Arrange user activities left-to-right in workflow order. Each column is a high-level step (e.g., "Browse Products" → "Add to Cart" → "Checkout" → "Pay" → "Track Order").

2. **Add details under each backbone activity** — Brainstorm all the specific user tasks, edge cases, and variations. Stick them under the relevant backbone column as cards. Don't prioritize yet — just capture.

3. **Identify the walking skeleton** — Draw a horizontal line across the map. Above the line: the thin slice of stories that, if all built, deliver a complete (if basic) workflow. This is your **Minimum Viable Product slice**. It touches every column but only takes the simplest path through each.

4. **Prioritize remaining stories** — Everything below the line is backlog for future releases. Re-prioritize these relative to each other, not against the skeleton.

5. **Slice into releases** — Draw additional horizontal lines or group cards into release buckets. Release 2 adds more depth to specific columns. Release 3 adds edge cases, optimizations, and variations.

### 1.2 How Story Mapping Differs from Flat Backlogs

**Flat backlog problem (what Patton calls "the backlog death march"):**

- All stories are in a single ordered list
- Priority is a single dimension (stack rank)
- Context is lost — "As a user, I want to enter my credit card number" sits far from "As a user, I want to review my order," even though they're part of the same checkout flow
- The narrative arc of the user journey is invisible
- Discovery (what should we build?) and delivery (how do we build it?) are conflated

**Story map advantages:**

- **Two-dimensional** — horizontal axis = workflow order, vertical axis = priority/depth
- **Visual narrative** — the entire user journey is visible in one view
- **Discovery-ready** — gaps in the workflow are immediately obvious (empty columns = missing steps)
- **Release planning** — horizontal slices show exactly what each release covers
- **MVP definition** — the walking skeleton is the thinnest viable slice, not the highest-priority items from a flat list

Patton's famous quote: *"A backlog is not a requirements document. It's a pile of ideas waiting to happen."*

### 1.3 Discovery vs. Delivery Connection

Patton is explicit that story mapping serves **both** discovery and delivery, but differently:

| | Discovery (What should we build?) | Delivery (How do we build it?) |
|---|---|---|
| **Story mapping role** | Backbone + walking skeleton reveal the shape of the solution | Detailed cards below the line are work items for sprints |
| **Conversation type** | "What does the user actually do here?" | "How do we implement this specific card?" |
| **Output** | A shared understanding of the problem space | An ordered set of work items |
| **Owners** | Product + Design + Dev together | Dev team with PO input |
| **Artifact state** | Living map, updated as learning happens | Sprint backlog derived from the map |

**The key insight**: Story maps are not a one-time artifact. They evolve. The map above the line (backbone + walking skeleton) is relatively stable. The map below the line changes constantly as new stories are discovered during development.

### 1.4 The "Sandwich" Conversation Pattern

Patton's "sandwich" is a narrative structure for workshop facilitation. It alternates between **breadth** (big picture) and **depth** (detail) to prevent analysis paralysis.

**The pattern has three layers:**

```
Top slice (breadth):  THE USER JOURNEY  → "Who is the user? What are the big steps?"
Filling (depth):      THE DETAILS       → "Under step 2, what are all the things that could happen?"
Bottom slice (breadth): THE SLICE       → "What's the smallest whole thing we could ship?"
```

**Why it works:** Most workshop failures happen when the group goes too deep on one part of the journey (e.g., spending 2 hours on the login screen) and runs out of time for the rest. The sandwich pattern forces alternating perspectives:

1. Start wide: map the full backbone (30 min)
2. Go narrow: brainstorm details for one column at a time (60 min)
3. Go wide again: decide on the walking skeleton slice (30 min)

**Patton's specific workshop script (from the book):**

- **Frame** (5 min): "We're going to map out the user journey for X. We'll start broad, then add detail."
- **Backbone** (20-30 min): Walk through the user's steps left-to-right. Write each on a sticky note. Disagree now.
- **Details** (40-60 min): Under each backbone step, brainstorm all stories. Don't discuss priority yet.
- **Slice** (20-30 min): Draw the walking skeleton line. "If we only shipped this thin slice, would it work?"
- **Sequence** (15 min): Ask: "What must come first? What must come after?" → dependencies emerge naturally from the map layout.
- **Reflect** (10 min): "Does this feel right? What did we miss?"

### 1.5 Horizontal vs. Vertical Slicing and MVP Definition

**Traditional (wrong) approach: horizontal slicing**
Build all stories for one layer (e.g., "all database work") in sprint 1, then all stories for the next layer in sprint 2, etc. This delivers **no user value** until the very end — classic Waterfall disguised as Agile.

**Patton's approach: vertical slicing**
Every release slice cuts through every layer of the stack (UI, business logic, data, infrastructure) but only for a thin end-to-end user scenario.

**Visual representation of a story map:**

```
Backbone:     [Browse] → [Add to Cart] → [Checkout] → [Pay] → [Track]
                   |           |              |          |          |
Walking           | Search    | Add item     | Enter    | Pay via  | View
skeleton:         | by name   | to cart      | address  | card     | status
                   |           |              |          |          |
Release 2:        | Filter    | Save cart    | Edit     | PayPal   | Email
                   | by price  | for later    | address  | option   | updates
                   |           |              |          |          |
Release 3:        | Advanced  | Gift options | Multiple | Saved    | SMS
                   | search    |              | addresses| payment  | alerts
```

Each release slice is a **vertical slice** — it cuts through all backbone steps but only takes the simplest path through each.

**How this enables MVP definition:**

1. The MVP is not "the top 10 items from a flat backlog" (which would give you disconnected features across the journey).
2. The MVP is the **walking skeleton** — one thin, end-to-end slice that proves the concept works.
3. Patton's rule: *"Build a whole system, not a pile of parts."*
4. This prevents the common failure mode of building the "login page" and "database schema" in sprint 1 (horizontal slicing) and having nothing to demo.

### 1.6 Real Examples of Story Maps in Practice

**Example 1: E-commerce checkout (from Patton's book)**

A team mapped the full checkout experience. The backbone was: Browse → Select → Configure → Add to Cart → Checkout → Pay → Receive Confirmation. Under "Pay," they found 23 cards: credit card, PayPal, Apple Pay, gift card, buy-now-pay-later, coupon codes, split payment, etc. The walking skeleton only included "credit card payment with valid card" — one happy path through the most common scenario. Release 2 added coupon codes and PayPal. Release 3 added the rest.

**Example 2: Healthcare appointment scheduling (Patton consulting engagement)**

The team mapped: Find Provider → Check Availability → Book Appointment → Prepare Visit → Attend → Follow Up. The walking skeleton was: search by zip code → see next available → pick a time → get confirmation email → show up → receive follow-up survey. This was ship-able in 6 weeks. The full map revealed that "Find Provider" had 14 sub-stories (by name, by specialty, by insurance, by location, by rating, by language, etc.) — the skeleton only did search by zip code.

**Example 3: BVNK fintech context (hypothetical application)**

Backbone: Onboard → Verify Identity → Fund Wallet → Send Payment → Track → Reconcile. The walking skeleton: submit onboarding form → pass KYC check → receive test funding → send one payment via API → see it in transaction history → match with statement. Release 2: multi-currency wallets, scheduled payments. Release 3: batch payments, compliance reporting.

---

## 2. Mike Cohn's Contributions

### 2.1 The INVEST Model — Full Breakdown

Cohn introduced INVEST in *User Stories Applied* (2004) as a mnemonic for **good user stories**. It is not a checklist for "done" but a quality heuristic — stories should trend toward INVEST, not necessarily achieve all six simultaneously.

| Letter | Term | Definition | Anti-Pattern |
|--------|------|------------|--------------|
| **I** | **Independent** | Stories should be self-contained with minimal dependencies on other stories. Dependencies force ordering constraints that reduce flexibility in sprint planning. | A story that can't be started until another story is 75% done. |
| **N** | **Negotiable** | Stories are not contracts. They are placeholders for conversation. Details emerge during development through collaboration between product and engineering. | A story so detailed it might as well be a spec (this is a "requirement," not a story). |
| **V** | **Valuable** | Every story must deliver value to a user, customer, or stakeholder. If it doesn't, it shouldn't be a story (it might be a technical task). | "Implement the customer table" — valuable to the developer, invisible to the customer. Better: "Look up my account by phone number." |
| **E** | **Estimable** | The team must be able to estimate the story. If they can't, it's too vague or too complex — split it or add more conversation. | "Improve performance" — what improvement? How measured? What's the scope? |
| **S** | **Small** | Stories should be small enough to complete within a sprint (ideally a few days, not the full sprint). Small stories are estimable, testable, and reduce risk. | A story that takes 3+ sprints — this is an epic, not a story. |
| **T** | **Testable** | You must be able to verify the story is done through concrete acceptance criteria. If you can't test it, how do you know it's done? | "The system should be user-friendly" — subjective, untestable. Better: "95% of users complete checkout within 3 minutes on first attempt." |

**Cohn's own caveats on INVEST:**

- **Independence** is aspirational — in real systems, stories always have some dependency. The goal is to minimize *tight* coupling.
- **Negotiable** does not mean vague. It means the *details* are negotiable; the *outcome* is clear.
- **Valuable** is the most commonly violated — teams write stories that describe technical implementation rather than user value (e.g., "Add a column to the orders table" instead of "View my order history").

### 2.2 The Card/Conversation/Confirmation (3Cs) Model

Cohn's 3Cs is the definitive model for what a user story actually *is*:

**Card** — The physical token (sticky note, Jira ticket, index card). Contains just enough information to identify the story: title, a sentence or two of description, and the story format. The card is intentionally lightweight — it's not a spec.

**Conversation** — The ongoing dialogue between product, development, and stakeholders about the story's details. The conversation happens throughout development, not just during sprint planning. Cohn: *"The card is a promise for a conversation, not a description of the solution."*

**Confirmation** — The acceptance criteria or tests that define "done" for the story. These are negotiated through the conversation and recorded on the back of the card (or in the ticket). They serve as both agreement and test specification.

**How the 3Cs interact:**

```
Card (placeholder) 
     ↓ triggers
Conversation (details emerge)
     ↓ produces
Confirmation (agreed definition of done)
```

**Common failure modes:**

- **Card-only development**: Product hands the team a stack of cards with no conversation. Developers build what they think the card means. Result: wrong thing built.
- **Spec-in-disguise**: The card has so much detail (wireframes, legal requirements, edge cases) that there's nothing left to discuss. Conversation is dead. Result: no creative problem-solving from developers.
- **No confirmation**: Stories are "done" based on opinion, not testable criteria. Result: unpredictable quality, disputes at sprint review.

### 2.3 User Story Format — When It Helps vs. Hurts

**The canonical format:**

```
As a <user role>
I want <goal/desire>
So that <reason/benefit>
```

**When it helps:**

- **Alignment**: Forces the writer to articulate who benefits and why. This prevents stories that describe implementation details (e.g., "Add a REST endpoint") rather than user value.
- **Conversation starter**: The format invites questions. "As a what kind of user? For what purpose?" The gaps in the format naturally lead to the conversation.
- **Prioritization**: The "So that" clause makes it clear what value the story delivers, helping the PO compare stories of different types.
- **Testing**: "So that" maps to the business outcome the test should verify.

**Example (good):**
> As a compliance officer, I want to review flagged transactions in a single dashboard, so that I can identify suspicious patterns without switching between systems.

**When it hurts:**

- **Over-application**: Not everything worth doing fits the format. Technical stories (refactoring, infrastructure, tech debt, APIs consumed by systems, not people) feel forced. Cohn himself acknowledged this — he called them "technical stories" or "tasks" and said they don't need the format.
- **Formulaic rot**: Teams apply the template mechanically. "As a user, I want to click the button, so that the thing happens." The format adds no value when the role is always "user" and the goal is obvious.
- **Length abuse**: Some stories try to cram too much into the format, producing multi-paragraph "As a..." statements that are actually epics.
- **False precision**: The format can create an illusion of clarity. Just because you can write it doesn't mean you understand it.

**Cohn's guideline**: Use the format for ~80% of stories (the ones describing direct user value). For the other 20% (technical infrastructure, system integration, compliance), write a concise title + acceptance criteria without forcing the format.

### 2.4 Story Splitting Patterns (Cohn's 10+ Ways)

Cohn's story splitting patterns, detailed in *User Stories Applied* and subsequent articles, are methods to break large stories into smaller, sprint-sized pieces. **The key principle**: each split piece must still be independently valuable (if possible) and independently testable.

**The patterns:**

| # | Pattern | Description | Example |
|---|---------|-------------|---------|
| 1 | **Workflow steps** | Split a multi-step process by its natural steps | "Complete loan application" → "Enter personal info" + "Upload documents" + "Sign agreement" |
| 2 | **Business rules / variations** | Split by different rules that govern behavior | "Calculate shipping cost" → "Domestic shipping cost" + "International shipping cost" + "Express shipping cost" |
| 3 | **Happy path vs. exceptions** | Build the happy path first, then error handling | "Process payment" → "Successful card payment" + "Declined card handling" + "Expired card handling" |
| 4 | **Input methods** | Split by how the user provides input | "Enter recipe" → "Enter manually" + "Import from URL" + "Scan from barcode" |
| 5 | **Data types / variations** | Split by different types of data handled | "Display calendar" → "Monthly view" + "Weekly view" + "Agenda view" |
| 6 | **Operations (CRUD)** | Split create/read/update/delete into separate stories | "Manage user profiles" → "View profile" + "Edit profile" + "Delete profile" |
| 7 | **Roles / user types** | Split by which type of user performs the action | "Place order" → "Guest checkout" + "Registered member checkout" + "Wholesale checkout" |
| 8 | **Performance / QoS levels** | Split by non-functional requirements | "Search products" → "Basic search" + "Search with autocomplete" + "Search under 200ms" |
| 9 | **Defer quality** | Build the feature without full quality attributes, add later | "Transaction export" → "CSV export" + "CSV with formatting + column config" |
| 10 | **Scenarios / test cases** | Split by specific test scenarios | "Login" → "Successful login" + "Login with SSO" + "Login with MFA" + "Password reset" |
| 11 | **Platform / device** | Split by where the feature appears | "View dashboard" → "Desktop dashboard" + "Mobile dashboard" + "Tablet dashboard" |
| 12 | **Data scope** | Split by the amount/type of data covered | "User search" → "Search by email" + "Search by name or email" + "Full-text search across all fields" |

**Cohn's rule of thumb**: If a story can't be estimated, split it. If it can't be split with any of these patterns, you don't understand it well enough yet.

### 2.5 User Story Hierarchy: Epic → Theme → Story → Task

Cohn's hierarchy is the standard across Agile:

| Level | Size | Timeframe | Description | Example |
|-------|------|-----------|-------------|---------|
| **Epic** | Large | Multiple sprints / quarters | A large body of work that can be split into stories. An epic doesn't have acceptance criteria — it has a goal. | "Launch customer onboarding portal" |
| **Theme** | Group | Ongoing | A collection of related epics/stories grouped by a business objective. Not always used. | "Improve onboarding conversion rate" |
| **Story** | Medium | Days (within one sprint) | A thin vertical slice of value. Has acceptance criteria. INVEST-compliant. | "Log in with Google SSO" |
| **Task** | Small | Hours (within a story) | Technical decomposition of how to build the story. Not independently valuable. | "Create OAuth2 client" (under login story) |

**Important Cohn distinction**: Stories are **not** tasks. Tasks decompose the *work* of a story. Stories decompose the *value* of an epic. A common mistake is writing task-level items as stories (e.g., "Create the database schema" — that's a task, not a story).

**Hierarchy in practice:**

```
Epic:   Customer Onboarding
  ├── Story: Complete registration form
  │     ├── Task: Build form UI with validation
  │     ├── Task: Create database migration for user table
  │     ├── Task: Implement email verification endpoint
  │     └── Task: Write end-to-end tests
  ├── Story: Verify identity via document upload
  │     ├── Task: Integrate with KYC provider API
  │     ├── Task: Build file upload component
  │     └── Task: Implement OCR parsing
  ├── Story: Fund account with initial deposit
  └── Story: Complete compliance questionnaire
```

### 2.6 Estimation Techniques

**Planning Poker (Cohn, *Agile Estimating and Planning*, 2005):**

- Each estimator holds a deck of Fibonacci cards (1, 2, 3, 5, 8, 13, 21, 40, 100)
- For each story, all estimators reveal their card simultaneously
- If estimates converge (within 1-2 steps), take the average/median
- If they diverge (one person says 3, another says 21), the outliers explain their reasoning
- Re-vote until convergence
- The discussion when estimates diverge is the **real value** of planning poker — it surfaces hidden assumptions

**Story Points vs. Ideal Days:**

| | Story Points | Ideal Days |
|---|---|---|
| **Definition** | Relative size (this is 3x bigger than a 1-pointer) | Hours/days of focused work |
| **Scale** | Fibonacci (1,2,3,5,8,13,21) | Linear (hours, days) |
| **Precision illusion** | Avoids false precision — "8" means "in the ballpark of an 8" | "3 days" sounds precise but is just as uncertain |
| **Across teams** | Not comparable (Team A's 5 ≠ Team B's 5) | Comparable (in theory) but practically not |
| **Decay** | Stable over time (a 5-pointer today ≈ 5-pointer next sprint) | Unstable (depends on interruptions, meetings, context switching) |
| **Cohn's preference** | **Story points** — because they decouple from elapsed time, making velocity a useful metric | Ideal days for new teams who need a concrete reference |

**Cohn's forecasting approach:**

1. **Track velocity** — how many story points per sprint
2. **Use yesterday's weather** — the most recent velocity is the best predictor of next sprint's velocity
3. **Range forecasting** — don't predict exact dates, predict ranges using historical velocity data
4. **Release burndown** — remaining points plotted over sprints, with trend lines showing optimistic/expected/pessimistic scenarios

### 2.7 Story Decomposition → Release Planning

Cohn's release planning in *Agile Estimating and Planning* follows a five-step process:

1. **Prioritize by value, risk, and dependency** — The PO orders the backlog by business value, but risk (learn early) and dependency (required sequence) also inform ordering.

2. **Estimate relative size** — Use planning poker to assign story points to backlog items at the story level. Epics get a T-shirt size (S/M/L/XL) and are split before sprint-level planning.

3. **Velocity-based release plan** — Given a team's historical velocity (e.g., 30 points/sprint), how many sprints will it take to deliver the prioritized stories?

4. **Inspect and adapt** — Every sprint, re-evaluate the release plan. Did velocity change? Did priorities shift? Did new stories emerge?

5. **Trade-off sliders** — Release planning always involves three variables: scope, time, and quality. Cohn argues quality is **not negotiable** (the Definition of Done is fixed), so the trade-off is between scope and time.

**Connecting hierarchy to release planning:**

```
Epic 1 (Quarter 1) → Stories A, B, C, D
Epic 2 (Quarter 2) → Stories E, F, G
Epic 3 (Quarter 3) → Stories H, I, J

Sprint 1: A(5) + B(8) + C(3) = 16 pts (velocity target: 30)
Sprint 2: D(5) + E(8) + F(3) = 16 pts (catching up)
Sprint 3: G(8) + H(5) + I(3) + J(5) = 21 pts
```

---

## 3. Work Breakdown for Agentic Development

### 3.1 How Traditional Story Decomposition Changes with AI Agents

Patton and Cohn's models were designed for **human developers** who work at a certain granularity, context-switch penalty, and communication bandwidth. When AI agents enter the picture, several assumptions break:

**What changes:**

| Dimension | Human-Ready | Agent-Ready |
|-----------|-------------|-------------|
| **Granularity** | A story is ~2-3 days of work (Cohn's "Small" rule) | A story is 15-45 minutes of agent execution time. Agents can complete smaller, more atomic tasks independently. |
| **Context retention** | Humans benefit from larger stories (more context, less handoff overhead) | Agents have zero context-switch cost but suffer from context-window limitations. Smaller, well-scoped stories work better. |
| **Dependencies** | Humans manage implicit dependencies through conversation ("Hey, is the user model done yet?") | Agents need **explicit** dependency declarations. An agent cannot walk to the next desk and ask. |
| **Communication** | The 3Cs work because humans fill gaps through conversation | The "conversation" in 3Cs must be encoded as explicit acceptance criteria and interface contracts when agents are involved. |
| **Estimation** | Story points based on human cognitive complexity | Agent time depends on token budget, API costs, and search/retrieval complexity. Different estimation model entirely. |
| **Review** | Human peer review | AI-assisted review + human approval. Review bottleneck shifts. |
| **Error handling** | Humans detect and correct errors as they work | Agents need explicit error recovery instructions and rollback procedures |

### 3.2 What Makes a Story "Agent-Ready" vs. "Human-Ready"

**Agent-ready story characteristics:**

1. **Atomic scope**: One clear output (one file, one function, one API endpoint, one test suite). If the story produces multiple artifacts, split it.

2. **Explicit dependencies**: Every interface the story consumes must be declared. The story's YAML manifest includes `explicit_deps`, `consumes_interfaces`, and `interfaces_provides`.

3. **File-scope bounded**: The story specifies exactly which files it will create or modify (`file_scope`). No surprise modifications to unrelated parts of the codebase.

4. **Interface contracts**: The story declares what API signatures, data structures, or schemas it provides. These serve as the "handshake" between agent-produced work and dependent stories.

5. **Independently testable**: Each story has acceptance criteria that can be verified without running the full system. Unit tests or contract tests at story boundaries.

6. **Self-contained**: The story includes all the context the agent needs — coding standards, architecture conventions, test patterns — within its prompt or workspace configuration.

**Human-ready story characteristics (still valid for humans):**

- Broader scope (multiple files, refactoring, cross-cutting concerns)
- Relies on implicit understanding of the codebase
- Conversation-heavy ("We'll figure out the exact approach in the implementation phase")
- May span multiple layers (UI + business logic + data)
- Estimation in story points, not tokens

**The convergence model: Stories have two modes:**

```yaml
story:
  id: "FR-42"
  title: "Add user email verification endpoint"
  
  # Human metadata
  as_a: "new user"
  i_want: "to verify my email address after registration"
  so_that: "my account is activated and secure"
  
  # Agent metadata
  agent_ready: true
  estimated_tokens: 4500
  file_scope: ["src/api/verify.py", "src/auth/email.py", "tests/test_verify.py"]
  explicit_deps: ["FR-15", "FR-16"]  # user model + email service
  consumes_interfaces: ["User", "EmailSender", "TokenService"]
  interfaces_provides: ["VerificationHandler"]
  
  # Shared acceptance criteria
  acceptance_criteria: |
    Given a registered user with an unverified email
    When they POST /api/verify with a valid token
    Then their email is marked as verified
    And they receive a confirmation response with status 200
```

### 3.3 DAG-Aware Story Mapping (Extending Story Maps with Dependency Edges)

Patton's story map is a **grid** — it has workflow order (horizontal) and priority (vertical). But it does not explicitly model **dependency edges** between stories. In a human team, dependencies are managed informally ("I need the login endpoint before I can build the dashboard"). With agents, these must be explicit.

**Extending the story map with DAG semantics:**

**Level 0: No DAG (traditional story map)**
```
Backbone:   [A1] → [A2] → [A3] → [A4]
              |       |       |       |
Sprint 1:   A1.1   A2.1    A3.1    A4.1   (walking skeleton)
Sprint 2:   A1.2   A2.2    A3.2    A4.2
```

**Level 1: DAG edges overlaid on story map**
```
Backbone:   [A1] → [A2] → [A3] → [A4]
              |       |       |       |
Sprint 1:   A1.1 ──→ A2.1   A3.1 ←── A4.1
              ↓               ↓
Sprint 2:   A1.2           A3.2
              ↓               ↓
Sprint 3:   A1.3 ←──────────┘
```

Here, arrows indicate dependency edges: A4.1 depends on A3.1, which depends on A1.2. The DAG determines execution order, not just the story map's horizontal flow.

**DAG-aware story mapping rules:**

1. **Backbone columns define workflow flow, not dependency flow.** Just because "Pay" comes after "Checkout" in the user journey doesn't mean the payment story depends on the checkout story — they might be parallel.

2. **Dependency edges are orthogonal to the story map grid.** A story in column A might depend on a story in column D (e.g., the "Track Order" feature depends on the "Payment" data model).

3. **Level assignment comes from topological sort, not release lines.** Instead of "above/below the line," stories are assigned to DAG levels: Level 0 = no dependencies (can run first), Level 1 = depends on Level 0, etc.

4. **The critical path replaces the walking skeleton.** The walking skeleton was a *horizontal slice* through the map. The critical path is the *longest chain of dependencies* through the DAG — the sequence that determines the minimum delivery time.

**BMAD-DAG integration pattern:**

The BMAD DAG Automator (from the existing repo at `/home/ubuntu/github/bmad-dag-automator`) already implements this:

```
Story YAML → DagGraph (nodes + edges) → Kahn's algorithm → Levels → Critical Path → AgentPool execution per level
```

Each DAG level contains stories with no intra-level dependencies. All stories in a level can execute in parallel (up to `max_concurrent` pool size). The orchestrator advances level-by-level, merging artifacts through git branches.

### 3.4 Acceptance Criteria Formats That Work for Both Humans and Agents

**For humans** (Cohn's model): Free-form acceptance criteria, bullet lists, conversational checklists.

**For agents**: Structured, testable, unambiguous criteria that can be verified programmatically.

**Recommended hybrid: Rich Gherkin (Given/When/Then + metadata)**

```gherkin
@FR-42 @agent-ready
Feature: Email Verification
  Agents: ["claude-code", "codex"]
  FileScope: src/api/verify.py
  DependsOn: ["FR-15", "FR-16"]
  Provides: ["VerificationHandler"]
  Contract: POST /api/verify { token: string } → { verified: boolean, message: string }

  Scenario: Successful verification
    Given a registered user "alice@example.com" with status "unverified"
      And a valid verification token "abc-123" associated with that user
    When POST /api/verify with body { "token": "abc-123" }
    Then the response status is 200
      And the response body contains "verified": true
      And the user.status is now "active"
      And the verification token is marked as "consumed"

  Scenario: Invalid token
    Given a registered user "alice@example.com"
    When POST /api/verify with body { "token": "invalid-token" }
    Then the response status is 400
      And the response body contains "error": "Invalid or expired token"
      And the user.status remains "unverified"
```

**Key additions for agent-readiness:**

| Field | Purpose | Example |
|-------|---------|---------|
| `Agents` | Which agent tools are qualified for this story | `["claude-code", "codex"]` |
| `FileScope` | Exactly which files to create/modify | `["src/api/verify.py"]` |
| `DependsOn` | Explicit dependency IDs | `["FR-15"]` |
| `Provides` | Interfaces this story exports | `["VerificationHandler"]` |
| `Contract` | API signature in machine-readable form | `POST /api/verify { token } → { verified, message }` |
| `TestableBy` | How to verify without full system | `["unit: tests/test_verify.py", "contract: test_api_contract.py"]` |

### 3.5 Intersection with BMAD's Story Breakdown Pattern

The BMAD pattern (from the existing codebase) uses a specific story breakdown that differs from traditional Cohn hierarchy:

**BMAD story structure:**

```yaml
stories:
  - id: "epic-1.1"          # Epic ID . Story Number
    title: "User model with email and password_hash"
    explicit_deps: []        # Empty for foundational stories
    file_scope: ["src/models/user.py"]
    interfaces_provides: ["User", "UserCreate", "UserResponse"]
  
  - id: "epic-1.2"
    title: "Password hashing and validation utility"
    explicit_deps: []
    file_scope: ["src/auth/hash.py", "src/auth/validation.py"]
    interfaces_provides: ["PasswordHasher", "PasswordValidator"]
  
  - id: "epic-1.3"
    title: "User registration API endpoint"
    explicit_deps: ["epic-1.1", "epic-1.2"]  # Dependencies on foundational stories
    file_scope: ["src/api/register.py", "src/api/schemas.py"]
    consumes_interfaces: ["User", "UserCreate", "PasswordHasher"]
    interfaces_provides: ["RegisterHandler"]
```

**Mapping BMAD to Cohn + Patton:**

| Cohn/Patton Concept | BMAD Implementation |
|---------------------|---------------------|
| Epic | `epic-1.*` prefix groups stories by epic. All `epic-1.*` = one epic. |
| Story | Each `id` field = one story. Not broken into tasks. |
| Dependency (implicit in human teams) | `explicit_deps` as an explicit array. DAG induction can also discover implicit deps via LLM. |
| Acceptance criteria (3Cs confirmation) | Not in the YAML — handled separately via Gherkin scenarios or `state_doc.py` |
| Walking skeleton | The set of stories that can execute at Level 0 (no deps) + Level 1 (depends only on Level 0) |
| Release planning | The critical path through the DAG determines the minimum delivery timeline |
| Interface contract | `interfaces_provides` / `consumes_interfaces` — agent-to-agent handshake |
| File ownership | `file_scope` — prevents agents from overwriting each other's work |

**BMAD's key innovation over traditional story decomposition:**

1. **Dependency-first, not value-first.** Traditional decomposition prioritizes by value. BMAD prioritizes by dependency topology. Foundational data models and interfaces run first.

2. **Interface contracts replace conversation.** In human teams, the 3Cs "conversation" handles interface alignment. In BMAD, `interfaces_provides` and `consumes_interfaces` serve as explicit contracts that the orchestrator can validate.

3. **DAG induction discovers hidden dependencies.** The `DagInductor` analyzes stories with an LLM to find implicit dependencies (e.g., story B references a schema defined in story A). This surfaces hidden coupling that human teams manage informally.

4. **Level-based parallel execution.** Stories at the same topological level have no interdependencies and can execute in parallel via the AgentPool (tmux sessions per agent).

5. **Artifact bridge ensures isolation.** Each DAG level gets its own git branch. The `ArtifactBridge` merges level branches upstream, providing a safety net against conflicting agent outputs.

---

## 4. Workshop Facilitation Patterns

### 4.1 Patton's "Story Mapping in an Hour" Technique

From Chapter 6 of *User Story Mapping* — the condensed workshop format for time-constrained teams:

**Setup (5 min):**
- Whiteboard or virtual board with three horizontal lanes visible (Backbone, Details, Release Slices)
- Sticky notes (physical) or cards (virtual) in at least three colors
- One color for backbone activities, one for detailed stories, one for release markers
- Invite: the person with the "north star" vision (product), one or two who know the users (research/design), one or two who know the technology (engineering)

**The Hour Flow:**

| Phase | Duration | Activity |
|-------|----------|----------|
| Frame | 3 min | "We're mapping [product name] from [user type] perspective. Goal: find the thinnest slice we can ship in [timeframe]." |
| Backbone | 12 min | Write user activities left-to-right. Each is a column header. "What are the 5-8 big steps the user takes?" Start with a verb + noun. No more than 8 columns. |
| Detail | 25 min | Under each column, add stories. 60 seconds per story — write it, stick it, move on. No debate. "What else could happen at this step?" Silence is okay — let people write. |
| Slice | 15 min | Stand back. Look at the map. Ask: "If we shipped ONLY one thin path through all columns, what would that be?" Draw the line. "Does that feel like a real product?" |
| Check | 5 min | "What did we miss?" Big gaps in the map become obvious. Note them. Schedule a follow-up. |

**Patton's rules for the hour:**

- **No laptops during mapping.** Everyone stands or sits at the board. Laptops = multitasking = dead workshop.
- **No debating during detail phase.** "Just write it, we'll discuss later." The map catches everything; nothing is lost.
- **The walking skeleton is the goal.** If the slice doesn't feel like a real product, you haven't gone thin enough. Cut more.
- **End with an action.** Who owns the map? When is the follow-up? What's the next step for each person?

### 4.2 Full Story Mapping Workshop (2-4 Hours)

For deeper work (product definition, release planning, complex domains):

**Preparation (done before the workshop):**

- Define the product scope — what's in, what's out
- Identify primary and secondary user personas
- Gather any existing research, data, or competitive analysis
- Book 2-4 hours (no shorter — 1 hour is for refreshes, not first-time mapping)
- Invite: 5-8 people max (product, design, engineering, QA, compliance if relevant)

**Workshop Agenda:**

| Phase | Time | Activity |
|-------|------|----------|
| 1. Frame | 15 min | Share the product vision. Who is the user? What is the goal? Define scope boundaries. "We are NOT mapping [out-of-scope items]." |
| 2. Deep Backbone | 30 min | Map user activities left-to-right. Write on sticky notes. Discuss disagreements. Consolidate. Result: 5-10 column headers. |
| 3. Detail Brainstorm | 45 min | Per column: add all stories, tasks, edge cases. Use different color for known vs. speculative. Encourage "what if..." questions. |
| 4. Organize | 15 min | Group related stories. Remove duplicates. Identify stories that are actually tasks (move them). |
| 5. Walking Skeleton | 30 min | Draw the MVP line. This is the hardest part — expect debate. Criteria: does this slice tell a complete story? |
| 6. Release Planning | 30 min | Draw additional lines for Release 2, 3. Assign stories to releases. Estimate at T-shirt level (S/M/L) if time permits. |
| 7. Dependency Check | 15 min | "What stories MUST come before others?" Note critical dependencies. Flag risky dependencies (high dependency + high uncertainty). |
| 8. Retro & Next Steps | 15 min | What did we learn? What was unclear? Who digitizes the map? When is the refinement session? |

### 4.3 How This Changes When One of the "Engineers" Is an AI Agent System

The story mapping workshop itself doesn't change dramatically — the **participants and the output format** change.

**Workshop participants with AI agents:**

| Role | Traditional | With AI Agents |
|------|-------------|----------------|
| Product Owner | Same | Same |
| Designer | Same | Same |
| Human Developer | Present | Present + Agent as "junior engineer" |
| AI Agent | Not present | Represented by agent configuration / manifest |
| Agent Platform Engineer | Not present | Present (defines agent capabilities, constraints, prompt patterns) |
| Compliance | Same | Same (but needed earlier for boundary definition) |

**What changes in the workshop output:**

The workshop now produces two artifacts instead of one:

1. **Human-readable story map** — Same as before (backbone, slices, walking skeleton)
2. **Machine-readable story manifest** — YAML with dependency edges, interface contracts, file scopes, and agent configuration:

```yaml
# Generated from workshop
epic: "customer-onboarding"
version: "1.0"
agents:
  allowed_tools: ["claude-code", "codex"]
  max_concurrent: 6
  fallback_strategy: "human-escalate"

stories:
  - id: "EP-01-S-01"
    title: "KYC identity verification submission form"
    acceptance_path: "gherkin"
    deps: ["EP-01-S-00"]  # user model story
    agent_capable: true    # human builder can  bypass if agent can't handle
    file_scope: ["src/kyc/form.py", "src/kyc/schemas.py"]
    contracts: ["POST /kyc/submit"]
    estimated_tokens: 8000
    qa_strategy: "ai-test-generation + human-review"
```

**Facilitation adjustments:**

1. **Story splitting must consider agent granularity.** "Can an agent build this in one session?" If not, split further.

2. **Dependencies need explicit workshop time.** The facilitator should ask: "What does this story need that another story produces?" Record these as explicit dependencies.

3. **Interface contracts are workshop deliverables.** Don't wait until implementation to define the API between stories. The workshop should produce at least a straw-man contract for each story's provided interfaces.

4. **File allocation decisions.** Which files does each story own? Conflicts happen when two agents touch the same file. The workshop should assign `file_scope` to prevent this.

5. **Agent capability flags.** Not every story is agent-capable. Stories involving third-party integrations, security review, or complex business logic may need human leads. Flag these in the workshop.

### 4.4 Remote Story Mapping Tools and Techniques

**Tool options:**

| Tool | Best For | Limitations |
|------|----------|-------------|
| **Miro** | Virtual sticky notes, real-time collaboration, hundreds of templates | Free tier limited; can get messy with large maps |
| **Mural** | Similar to Miro, strong enterprise features | Same as Miro |
| **LucidSpark** | AWS integration, good for technical teams | Smaller template library |
| **Confluence Whiteboards** | If org is already on Confluence | Limited vs. dedicated tools |
| **FigJam** | If team already uses Figma | Less suited for complex story maps |
| **Physical board + camera** | Lowest friction, no tooling cost | Poor async experience, no persistence |
| **Markdown + YAML** | Best for agent integration (BMAD pattern) | Not visual; requires mental mapping |

**Remote facilitation techniques:**

1. **Pre-work (async).** Send participants the scope, user personas, and any existing research 24 hours before. Ask each person to draft a personal story map independently. This prevents "waiting for the quiet person to speak."

2. **Timer discipline.** Every phase has a visible countdown. Remote workshops drift worse than in-person. Use the tool's timer feature or a separate countdown.

3. **The "two-board" technique.** One board for the main story map. A second "parking lot" board for questions, concerns, and ideas that don't fit the current phase. This prevents tangential discussions from derailing the flow.

4. **"Yes, and..." rule.** When someone adds a sticky note, the next person must build on it, not dismiss it. This prevents idea killing in the brainstorming phase.

5. **Silent mapping rounds.** 5 minutes of silent individual work between group discussions. Everyone writes their ideas before anyone speaks. This prevents loud voices from dominating and gives introverts equal participation.

6. **The walking skeleton vote.** After the slice line is drawn, use anonymous dot voting to see if participants agree it's the right MVP. Divergent votes reveal disagreement that needs discussion.

7. **Export for agents.** After the workshop, convert the visual map to the YAML manifest format. This is the bridge between human workshop and agent execution. Automate this step if possible (Miro API → YAML converter).

**Recommended tool for fintech + agentic development:**

Use **Miro for the workshop** (because it supports the free-form, collaborative, visual nature of story mapping) and **YAML defined in git** for the persistent artifact (because it integrates with the DAG scheduler, version control, and agent tooling). The Miro board is the collaborative artifact. The YAML in the repo is the source of truth for execution.

---

## 5. Synthesis: Converged Framework for Paul's BVNK Context

### Putting It All Together

Paul's framework combines:
- **Team Topologies** → Stream-aligned teams with clear interaction modes
- **BMAD framework** → Agent orchestration with DAG-based scheduling
- **Story Mapping (Patton)** → Narrative-driven work decomposition
- **User Stories (Cohn)** → INVEST-compliant, Conversation-first artifacts

**The converged planning flow:**

```
Quarterly:
  OKRs → Strategic Initiatives → Epic Story Maps (Patton workshop)
    ↓
Monthly:
  Epic-level DAG induction (BMAD) → Dependency discovery + Level assignment
    ↓
Weekly:
  Story refinement → Acceptance criteria (Given/When/Then) → Agent manifests
    ↓
Continuous:
  DAG orchestrator executes level-by-level → Agent pool per level → Artifact merge
    ↓
Human-in-the-loop:
  Review gates → Compliance checks → Release decisions
```

**Key design decisions for the converged framework:**

1. **Story maps at the strategic level** (quarterly / epic initiation): Use Patton's story mapping to define the backbone and walking skeleton. This is a human-to-human artifact.

2. **DAG induction at the tactical level** (monthly / epic refinement): Convert the story map into a DAG with explicit dependency edges. Use BMAD's `DagInductor` to discover implicit dependencies via LLM analysis. The DAG replaces the story map as the working artifact for execution.

3. **Agent-ready stories at the execution level** (weekly / sprint level): Break walking skeleton stories into agent-sized units. Each has: `file_scope`, `interfaces_provides`, `consumes_interfaces`, `explicit_deps`, and `acceptance_criteria` in Given/When/Then format. Each story is 15-45 minutes of agent execution time.

4. **Human review at the integration level**: Every DAG level merges through git. Human review at the level boundary, not the individual story boundary. This balances agent autonomy with quality control.

5. **Compliance embedded in the DAG structure**: Compliance checkpoints are modeled as DAG nodes. A "compliance review" story sits as a dependency gate between agent execution and production deployment.

### Open Questions for Paul's Framework

- **Story point estimation for agents**: Do we estimate agent stories in tokens, wall-clock time, or complexity categories (A/B/C)? Or skip estimation entirely and use historical throughput from the DAG automator?

- **Error recovery in the DAG**: When a story fails (agent can't complete, test fails, artifact broken), what's the fallback? Human escalation? Agent retry with different model? Re-plan affected level?

- **The "conversation" in 3Cs with agents**: Cohn's conversation is human-to-human. In the agentic context, how is the conversation encoded? Through the prompt? Through the acceptance criteria? Through structured interface contracts?

- **Walking skeleton vs. critical path**: Patton's walking skeleton is a human decision about what to build first. The critical path is a topological inevitability. When they conflict (e.g., the highest-value walking skeleton story can't run until a foundational story completes), who wins?

---

*Sources: Jeff Patton — User Story Mapping (O'Reilly, 2014); Mike Cohn — User Stories Applied (2004), Agile Estimating and Planning (2005), Succeeding with Agile (2009); BMAD DAG Automator codebase at /home/ubuntu/github/bmad-dag-automator/; Scrum evolution research at /home/ubuntu/scrum_research_p*.md.*
