# BFF, UI Component Design, UX & Micro Frontends — Research for Converged Agentic Framework

**Prepared for:** Paul Knauer, Engineering Manager, BVNK
**Context:** Team Topologies × BMAD AI agent orchestration × DAG-based autonomous development
**Date:** 2026-06-13

---

## 1. BFF — Backend for Frontend

### 1.1 The Core Pattern

The **Backend for Frontend** pattern was codified by **Phil Calçado** at **SoundCloud in 2015** (originally observed at Netflix as the "API per client-type" model). The fundamental insight: instead of building one general-purpose API and forcing every client to adapt, **create one backend per client type**.

**Client types:** Web browser (aggregates data for full-page renders, SSR), iOS/Android native (returns JSON mapped to native models, optimised for battery/payload), IoT/embedded (minimises payload, session-less, often protobuf or CBOR), 3rd-party/partner (rate-limited, versioned — this is typically a public API, not a BFF).

**Source:** Calçado, P. (2015). "Pattern: Backends For Frontends" — thoughtworks.com/insights/blog/bff

### 1.2 Why BFF Exists — Solving the "One-Size-Fits-All API" Problem

Before BFF, monolithic backend APIs were designed to serve every client equally. This caused:

- **Over-fetching:** Mobile clients download 10x the data they need because the web variant needs it
- **Under-fetching:** Web clients make 7 round-trips to render a dashboard because the API was not designed for that view
- **Brittle versioning:** One breaking change in the "general" API breaks every client
- **Cross-client coupling:** A mobile feature request requires changing the shared API, which risks regressions on web

BFF solves this by giving each client type a **dedicated backend whose sole purpose is to serve that client's UI**. The BFF is the "interface adapter" in clean architecture terms — it translates between the UI's needs and the downstream service contracts.

### 1.3 BFF vs API Gateway — Critical Distinction

**API Gateway** (shared infrastructure, Platform Team owned): Cross-cutting concerns — auth, rate-limiting, routing, caching. Zero business logic. Released independently of any frontend.

**BFF** (owned by consuming frontend team, Stream-aligned Team): Client-specific data aggregation and transformation. Rich view-model assembly and data shaping. Released in lockstep with its frontend.

**Critical insight:** A BFF often sits **behind** an API Gateway. The Gateway handles auth/RBAC, the BFF handles UI-specific aggregation. They are complementary, not alternatives.

**Source:** Newman, S. (2021). *Building Microservices, 2nd Ed.* O'Reilly. Chapter on "Backends for Frontends."

### 1.4 BFF Boundaries in Team Topologies

In **Team Topologies** (Skelton & Pais, 2019), the BFF is a natural boundary for **Stream-aligned Teams**:

- **Stream-aligned Team:** Owns the BFF for its domain-specific frontend. The BFF is its "friendly API boundary" that shields the frontend from service topology changes.
- **Enabling Team:** May help a stream-aligned team set up its first BFF or adopt GraphQL.
- **Platform Team:** Provides the shared BFF infrastructure — the runtime, BFF SDK/framework, observability, and deployment pipeline.
- **Complicated-Subsystem Team:** If BFF has a particularly complex data aggregation algorithm (e.g., real-time pricing engine), that could be extracted into a separate BFF owned by a CS Team.

**Source:** Skelton, M. & Pais, M. (2019). *Team Topologies.* IT Revolution.

### 1.5 BFF in an Agentic DAG

In a DAG-based autonomous development pipeline, the **BFF is a DAG node** with:

- **Depends on:** Frontend spec (what data the UI needs), Service contracts (what downstream APIs provide)
- **Produces:** API endpoint definitions, GraphQL schema, data transformation logic
- **Executes:** Generates the BFF code (Node.js/GraphQL), deploys it, runs integration tests
- **Artifacts:** OpenAPI spec or GraphQL SDL, integration test suite, deployment manifest

**Key principle:** The BFF should be generated from the **UI component tree** — each component declares its data requirements (via GraphQL fragments or data hooks), and the BFF agent composes those into a single aggregated response or a GraphQL resolver tree.

### 1.6 GraphQL as the BFF Protocol of Choice

GraphQL has become the de facto standard for BFF implementations because:

1. **UI-driven data selection:** The frontend describes exactly what data it needs in a query; the BFF executes exactly that query
2. **Single round-trip:** One GraphQL query resolves data from multiple downstream services via a single BFF resolver
3. **Strongly typed schema:** The GraphQL schema serves as the contract between frontend and BFF
4. **Client code generation:** Tools like GraphQL Code Generator produce typed hooks/queries/mutations from the schema

**Real-world adopters:** Netflix (Apollo Federation + subgraphs), GitHub (Ruby + graphql-ruby), Shopify (Ruby + GraphQL, Storefront API as BFF), Airbnb (Node.js + Apollo Server, micro BFFs per travel domain).

**Source:** Apollo Federation specification — apollographql.com/docs/federation

### 1.7 BFF Ownership in Multi-Team Environments

**Three models:**

1. **Single shared BFF** — One Web BFF owned by a dedicated Platform team. All teams contribute resolvers/modules. Best for small orgs (1-2 teams contributing to same frontend).

2. **BFF-per-domain** — Each stream-aligned team owns its own BFF microservice. The frontend calls multiple BFFs. Requires frontend orchestration. Best for larger orgs where team autonomy is paramount.

3. **Federated GraphQL BFF (recommended)** — Each team owns a **subgraph** (part of the overall GraphQL schema). The Platform Team owns the **supergraph** (Apollo Gateway) that composes subgraphs into one endpoint. The frontend calls one GraphQL URL. Best for medium-to-large orgs.

Each subgraph is a BFF owned by its stream-aligned team. The Platform Team provides the Gateway, BFF runtime, schema registry, and contract testing infrastructure.

**Source:** Apollo Federation 2.0 — "Managed Federation" architecture. Also: Shopify's decomposition into domain-specific subgraphs (shopify.engineering/graphql-federation-at-shopify).

---

## 2. UI Component Design

### 2.1 Component-Based UI Architecture

Modern frontend development is built on **component-based architecture**. The core idea: the UI is a tree of self-contained, reusable elements that manage their own state, rendering, and behavior.

| Framework | Component Model | Key Concept |
|---|---|---|
| **React** | Functional + Hooks | useState/useEffect side-effect isolation |
| **Vue** | Single-File Components (SFC) | template, script, style in one file |
| **Svelte** | Reactive components | Compile-time framework (no virtual DOM) |
| **Web Components** | Native browser API | customElements.define(), Shadow DOM, slots |

**For agentic development, React (or a React-like framework) is the safest default** because:
- Largest ecosystem of tooling for code generation (Vercel AI SDK, Copilot, Cursor)
- Most design systems are React-first (MUI, Radix, Shadcn)
- Storybook (component testing) has first-class React support

### 2.2 Design Systems as the UI "Platform"

In Team Topologies, the **Platform Team owns the design system** as a platform product consumed by all stream-aligned teams.

| Design System | Framework | Ownership Model | Token System |
|---|---|---|---|
| **Material UI (MUI)** | React (JSS/Emotion) | Full component library | MUI Theme: palette, typography, spacing, breakpoints |
| **Radix UI** | React (unstyled primitives) | Headless accessibility primitives | You bring your own styling (CSS/Tailwind) |
| **Shadcn/ui** | React + Tailwind | Copy-paste components (not a package) | Tailwind config = design tokens |
| **Tailwind CSS** | Utility-first CSS | Styling engine, not components | tailwind.config.js = design token source |
| **Ant Design** | React (CSS-in-JS) | Full enterprise component library | ConfigProvider theme tokens |
| **Chakra UI** | React (styled-system) | Component library with prop-based styling | theme.ts tokens |

**Platform Team publishes the npm package; agents consume it.** The design system is a DAG dependency, not a DAG output.

### 2.3 Atomic Design & DAG Mapping

**Brad Frost's Atomic Design (2016)** provides a natural decomposition hierarchy:

- **Atoms** — Basic HTML elements (Button, Input, Label, Icon). DAG node: Atomic Components DAG. Depends on: Design tokens.
- **Molecules** — Simple component groups (FormField = Label + Input + Error, Card). DAG node: Molecular Compositions DAG. Depends on: Atoms.
- **Organisms** — Complex UI sections (CheckoutForm, ProductGrid, Header). Depends on: Molecules + API data.
- **Templates** — Page-level wireframes (CheckoutPageLayout, ProductListing). Depends on: Organisms + BFF schema.
- **Pages** — Specific instances (/checkout, /products?category=x). Depends on: Templates + real data.

Each DAG node produces a **verified output** (tested components, validated schema) before the next node begins.

**Source:** Frost, B. (2016). *Atomic Design.* bradfrost.com/blog/post/atomic-web-design

### 2.4 Component Composition Patterns

| Pattern | Description | When to Use |
|---|---|---|
| **Composition over inheritance** | Compose small components, dont extend large ones | Always |
| **Container/Presentational** | Container: logic + data fetching. Presentational: pure rendering | Partially superseded by custom hooks |
| **Custom Hooks** | Extract stateful logic into use* functions | React modern approach |
| **Render Props** | Pass rendering logic via a prop (e.g., renderItem) | Rarely needed now; hooks cover most cases |
| **Compound Components** | Select.Trigger, Select.Option pattern | Complex primitives (Radix, Reakit) |
| **Slot/Children** | <Layout><Sidebar /><Main /></Layout> | Layout components |

**Agentic generation rules:**
1. Agents MUST prefer composition — a Button inside a Card, not a CardWithButton mega-component
2. Agents MUST extract reusable hooks — shared useQuery pattern instead of duplicate data fetching
3. Agents MUST NOT generate 500-line components — split into smaller files
4. Agents SHOULD use design system primitives rather than raw <div> and inline styles

### 2.5 AI Agents Generating UI Components — Anti-Patterns

| Anti-Pattern | Why It Happens | Prevention in DAG |
|---|---|---|
| **Over-engineering** | Agent builds a generic super-component with 18 props when only 3 are needed | Cyclomatic complexity gate on generated components |
| **Ignoring design system** | Agent imports <div> with inline styles instead of design system <Button> | Lint rule: no inline styles; enforce design system imports |
| **CSS-in-JS spaghetti** | Agent writes 200 lines of styled.div when Tailwind utilities suffice | Enforce design tokens via config, reject arbitrary values |
| **Missing accessibility** | Agent produces <div onClick={...}> instead of <button> | Automated axe-core check on every DAG node output |
| **Over-nesting** | 12 levels of <div> wrappers for a simple layout | Lint: max JSX depth = 4 |
| **No loading/error/empty states** | Agent optimises only the happy path | State coverage check: loading, error, empty, success |
| **Duplicate components** | Agent generates new UserAvatar instead of using existing one | Component registry / catalog lookup before generation |

### 2.6 Testing UI Components

| Layer | Tool | What It Tests | Runs In DAG |
|---|---|---|---|
| **Unit / Component** | Testing Library, Vitest | Component renders correctly, user interactions work | Every component DAG node |
| **Snapshot** | Vitest + toMatchSnapshot | Component output does not change unexpectedly | On component library roots |
| **Visual Regression** | Chromatic, Percy, Playwright diff | Pixels match approved baseline | Component library release (deploy gate) |
| **Integration** | Playwright/MSW | Component + BFF work together | Per micro frontend DAG node |
| **E2E** | Playwright | Everything works end-to-end | Shell-level DAG (post all frontends) |
| **Accessibility** | axe-core (via Testing Library or Playwright) | WCAG 2.1 AA compliance | Every component DAG node |
| **Performance** | Lighthouse CI | Bundle size, CLS, LCP, FID | Deploy gate on production |

**Source:** Testing Library docs (testing-library.com)

---

## 3. UX (User Experience) Design

### 3.1 The UX Design Process

The canonical UX process (ISO 9241-210, Human-centred design for interactive systems):

Research (Users, needs) -> Wireframes (Lo-fi) -> Prototypes (Hi-fi) -> Visual Design -> Usability Testing -> Implementation

### 3.2 UX in the Agentic Pipeline

| UX Activity | Can an Agent Do It? | DAG Integration |
|---|---|---|
| **User research** | No (no real users) | Human-led; results feed into DAG as spec documents |
| **Synthesis (personas, journey maps)** | Partial | Agent produces persona cards as DAG artifacts |
| **Wireframing (lo-fi)** | Yes | UX Agent DAG node produces wireframe artifacts (SVG/HTML) |
| **Prototyping (hi-fi)** | Yes | UX Agent DAG node produces interactive prototypes |
| **Visual design** | Yes (limited) | Styling Agent applies design tokens to wireframes |
| **Usability testing** | No (no human participants) | Human gate; agents can automate heuristic evaluation (NN Group heuristics) |
| **Spec writing** | Yes | UX Agent produces component specs consumed by Frontend DAG nodes |
| **Design token generation** | Yes | UX Agent generates tokens.json from brand guidelines |
| **Accessibility evaluation** | Yes | a11y DAG Gate (every frontend node), runs axe-core |

**Recommendation:** Place a **UX Agent** early in the DAG that reads the product spec, generates lo-fi wireframes, produces/validates design tokens, generates a11y specifications, and exports artifacts consumed by downstream Frontend DAG nodes. The UX Agent is a **human-reviewed gate** — wireframes and tokens are reviewed by a human designer before downstream DAG execution proceeds.

### 3.3 Design Tokens as the Interface Contract

Design tokens are the **bridge between UX and engineering** — named, reusable design decisions expressed as platform-agnostic values (typically JSON).

**Categories:** Colour (color.primary.500 = #0052FF), Typography (font.size.body = 16px), Spacing (spacing.md = 16px), Border radius (radius.sm = 4px), Shadow (shadow.card = 0 2px 8px...), Animation (animation.duration.fast = 200ms), Breakpoint (breakpoint.md = 768px), Z-index (zIndex.modal = 1000).

**Token format:** W3C Design Token Community Group spec — JSON with type annotations and descriptions.

**Tooling:** Style Dictionary (Amazon), Token Studio (Figma plugin), Specify, Supernova.

**In the DAG:** Design tokens are generated by the UX Agent or Platform Team and published as an npm package (@bvnk/tokens). Every downstream frontend DAG node imports tokens — no component should hardcode a colour, font size, or spacing value.

**Source:** W3C Design Tokens Community Group (tr.designtokens.org/format)

### 3.4 UX Handoff — From Figma to Agent-Generated Code

**Recommended approach:** Figma Design File -> Figma API (REST/Webhook) -> UX Agent (extracts tokens, generates spec, exports SVG) -> Frontend Agent (reads spec, generates JSX, uses design system imports)

**Tools for Figma-to-code bridge:**
- **Figma REST API** — extract component definitions, styles, and tokens programmatically
- **Anima / Zeplin** — generate component specs from Figma layers
- **Builder.io / Mitosis** — compile Figma designs to React/Vue/Svelte code
- **Locofy.ai** — Figma plugin to React/Tailwind code

**Simplest approach for an agentic pipeline:** The UX designer exports design tokens (via Token Studio + Style Dictionary) and wireframes (via Figma export SVG/PDF). The UX Agent reads these exports and generates the component spec that downstream Frontend Agents consume.

### 3.5 The "UX Debt" Problem in Agentic Development

**The problem:** AI agents optimise for **functional correctness** — does the component render, does the button call the API, does the form submit? They do NOT optimise for visual polish, information hierarchy, cognitive load, error message clarity, motion design, or copy quality. This creates **UX debt**.

**Prevention in the DAG:**
- **Heuristic evaluation agent** — Runs Nielsen's 10 usability heuristics against generated UI (post-frontend DAG gate)
- **Design token enforcement** — Linter rejects hardcoded values that should be tokens (every DAG node)
- **Layout consistency check** — Compares generated spacing against design system defaults (post-frontend DAG test)
- **Copy review gate** — Extracts all user-facing strings for human review (DAG pause node)
- **Visual regression baseline** — Captures approved screenshots; pixel diff requires human approval (deploy gate)
- **State completeness check** — Ensures every component has loading, empty, error, and success states (per-component DAG test)

### 3.6 UX Review as a DAG Gate

The DAG should include a **UX Review Gate** between "Feature Complete" and "Production Ready":

[...Frontend DAG Nodes...] -> UX Review Gate -> [a11y Gate] -> [Production Ready Assessment]

**Gate criteria (automated + human):**
1. All components use design tokens (no hardcoded values)
2. Component spacing matches design system grid (8px base unit)
3. All interactive elements have hover/focus/active states
4. Loading, empty, and error states exist for every data-driven component
5. Copy is consistent (tone, terminology, capitalisation)
6. Human UX reviewer signs off on a visual diff
7. No visual regressions from baseline

### 3.7 Accessibility as a Non-Negotiable DAG Gate

| Check | Tool | WCAG Criterion | Automated? |
|---|---|---|---|
| Color contrast | axe-core, contrast-ratio | WCAG 1.4.3 (AA: 4.5:1 ratio) | Fully |
| Keyboard navigation | Playwright tab tests | WCAG 2.1.1 (keyboard) | Fully |
| ARIA labels | axe-core, Testing Library | WCAG 4.1.2 (name, role, value) | Fully |
| Focus management | Playwright focus tests | WCAG 2.4.3 (focus order) | Partially |
| Screen reader | axe-core, vocally | WCAG 4.1.1 (parsing) | Fully |
| Touch targets | Lighthouse | WCAG 2.5.5 (min 44x44px) | Partially |
| Heading hierarchy | axe-core | WCAG 1.3.1 (info and relationships) | Fully |
| Alt text | axe-core | WCAG 1.1.1 (non-text content) | Fully |

**Policy:** Zero known a11y violations allowed in production. The DAG gate **blocks deployment** if axe-core reports any WCAG 2.1 AA violation. Exceptions require documented human override.

**Source:** Deque Systems — axe-core documentation (deque.com/axe). WCAG 2.1 — w3.org/TR/WCAG21.

---

## 4. Micro Frontends

### 4.1 Core Concept

**Micro Frontends** extend microservice thinking to the frontend: decompose a monolithic frontend application into **independently-deployable, loosely-coupled fragments** owned by separate teams.

The concept was formalised by **Cam Jackson** (ThoughtWorks, 2019) and popularised by companies like:
- **IKEA** — modular product pages per category
- **Spotify** — "Everything" feature teams own their UI
- **Zalando** — 500+ micro frontends in production
- **DAZN** — micro frontends per sport/region

**Source:** Jackson, C. (2019). "Micro Frontends" — martinfowler.com/articles/micro-frontends.html

### 4.2 Integration Patterns

#### A. Server-Side Composition
Page assembled on the server before being sent to the browser.

| Technique | Tooling | How It Works |
|---|---|---|
| **SSI (Server-Side Includes)** | Nginx, Apache | HTML fragments composed via include directives |
| **Tailor** | Zalando (Node.js) | Fragment-based streaming HTML composition |
| **Podium** | FINN.no (Node.js) | Podlet-based composition with HTTP fragment fetching |
| **ESI (Edge-Side Includes)** | Varnish, Akamai | Edge-level fragment composition |

**Podium example** (https://podium-lib.io): Layout server registers podlets (header, search) and composes their HTML into a single page response.

**Pros:** Fast initial render, SEO-friendly, simple browser model.
**Cons:** Server must compose fragments in real-time; cascading fragment failures.

#### B. Client-Side Composition
Each micro frontend ships its own JS bundles; the browser composes them.

| Technique | Tooling | How It Works |
|---|---|---|
| **Web Components** | Custom Elements, Shadow DOM | Each MFE is a custom-element; composition via HTML tags |
| **Module Federation** | Webpack 5, ModuleFederationPlugin | Remote modules loaded at runtime; shared dependencies |
| **Single SPA** | single-spa.js | Meta-framework: registers apps, manages lifecycle (mount/unmount) |
| **Iframes** | (Avoid if possible) | Each MFE in its own iframe — heavy, hard to style |

**Module Federation (recommended for agentic DAG):** Each MFE exposes components via remoteEntry.js. The Shell imports them via React.lazy(). Shared dependencies (react, react-dom, @bvnk/ui) are configured to avoid duplication.

**Source:** Webpack Module Federation — webpack.js.org/concepts/module-federation (Zack Jackson).

#### C. Edge-Side Composition
Composition at the CDN edge (Cloudflare Workers, Fastly Compute@Edge, Vercel Edge Functions).

**Example:** Cloudflare Worker routes /checkout to payments-mfe origin, / to shell origin.

**Pros:** Near-zero latency for fragment assembly, global distribution, no server infrastructure.
**Cons:** Vendor lock-in, complex debugging, limited runtime (Worker CPU time limits).

### 4.3 Micro Frontend Boundaries in Team Topologies

**Platform Team owns:** Shell (composition layer, routing, auth), Design system, BFF supergraph gateway, CI/CD foundation, cross-MFE monitoring.

**Stream-aligned team owns:** Its micro frontend (React app or component set), its BFF (GraphQL subgraph or REST API), its deployment pipeline (independent of other teams).

**Source:** Geers, O. (2021). *Micro Frontends in Action.* Manning Publications.

### 4.4 Micro Frontends in a DAG

Each micro frontend is a **DAG node** (or a sub-DAG):

[Design Tokens] -> [Platform Shell DAG] -> [Deploy]
       |
  [Payments MFE DAG] -> [Payments BFF DAG] -> [Payments Service]
  [Onboarding MFE DAG] -> [Onboarding BFF DAG] -> [Onboarding Service]

**DAG dependency rules:**
1. **Shell DAG** depends only on design tokens — shell is deployable independently
2. Each **MFE DAG** depends on: design tokens + shell types + BFF schema
3. Each **BFF DAG** depends on: downstream service contracts + MFE data requirements
4. **Integration tests** run after all MFEs are built
5. **E2E tests** run on the composed shell + all MFEs

### 4.5 The BFF + Micro Frontend Pairing

**Each micro frontend typically has its own BFF:** payments-mfe / payments-bff (sources: Payment Service, Ledger, Fraud), onboarding-mfe / onboarding-bff (KYC Service, User Service, Document Verification), compliance-mfe / compliance-bff (AML Service, Sanctions, Reporting).

**Why paired:** Team autonomy, data isolation, independent scaling, technology flexibility.

**When NOT to pair:** Trivially simple MFE (static footer), small app where N BFF overhead exceeds benefit, or federation graph already provides data isolation within a single gateway.

### 4.6 Micro Frontend Challenges

| Challenge | Mitigation |
|---|---|
| **Shared state** (auth token, session, cart) | Shell manages global state; MFEs receive it via props/context |
| **Shared routing** | Shell controls router; MFEs emit events for cross-MFE navigation |
| **Performance: N bundles** | Module Federation shared config, code splitting, preloading |
| **Consistency** (different CSS, different component versions) | Shared design system (pinned version), design token enforcement |
| **Testing complexity** | Contract testing (MFE->BFF) + E2E for critical paths only |
| **Dev experience** (running all MFEs locally is slow) | Shell dev server with mock MFEs; MFE dev runs only its own |
| **Versioning** (MFE incompatible with Shell) | Contract testing + semver on MFE manifest |

**Source:** Geers, O. — "Micro Frontends: Challenges and Solutions" (martinfowler.com, 2020).

### 4.7 How Agents Build Micro Frontends

**Key insight: Agents CAN work within a single micro frontend without understanding the full composition.** This is the ideal use case for agentic development.

Each micro frontend is a bounded context (one domain, one team), independently deployable, testable in isolation, and built against shared design tokens.

**Agent workflow for a micro frontend change:**
1. [Product Spec] "Add order history to Payments MFE"
2. [UX Agent] -> wireframe + spec for payments-mfe/order-history
3. [Frontend Agent] -> generates components in payments-mfe/ using @bvnk/ui, following MFE patterns
4. [BFF Agent] -> generates/updates payments-bff/ with new GraphQL resolver and integration tests
5. [Test Agent] -> runs component + integration + a11y tests
6. [Human Review] -> UX + code review focused on this MFE
7. [Deploy] -> payments-mfe + payments-bff deployed independently

**The agent does NOT need to understand:** How the Shell works, how other MFEs are built, the full deployment topology.

**The agent DOES need:** The design system package and tokens, the MFE's existing component structure and conventions, the BFF's GraphQL schema and downstream service contracts, the MFE's test patterns.

**Why this works so well for agents:** Micro frontends were designed for **team-level autonomy**. If a team can own an MFE independently, an **agent working on behalf of that team** can also own it independently — with the same constraints, dependencies, and independence guarantees.

---

## 5. Synthesis: Converged Framework for BVNK

### 5.1 The Frontend Architecture Stack

USER (Browser / Mobile)
       |
PLATFORM TEAM SHELL
  Shell Router (React Router) + Auth/Session (OIDC/OAuth) + Micro Frontend Registry (Module Federation)
       |
  Payments MFE (Stream Team)  |  Onboarding MFE (Stream Team)  |  Compliance MFE (Stream Team)
  Uses: @bvnk/ui, @bvnk/tokens |  Uses: @bvnk/ui, @bvnk/tokens  |  Uses: @bvnk/ui, @bvnk/tokens
       |
  Payments BFF (GraphQL, Apollo Subgraph) | Onboarding BFF (GraphQL, Apollo Subgraph) | Compliance BFF (GraphQL, Apollo Subgraph)
       |
  Payment Service (Downstream) | KYC/User Service (Downstream) | AML/Report Service (Downstream)

### 5.2 This Stack as a DAG

**Phase 1: Foundation (Platform Team owned)**
[Design Tokens DAG] -> [Component Library DAG (@bvnk/ui)] -> [Shell DAG (Router + Auth + Shell)]

**Phase 2: Domain Parallel (Stream-aligned teams, parallel execution)**
For each domain: [Domain BFF DAG (GraphQL schema, resolvers, integration tests, deploy)] -> [Domain MFE DAG (Components, Pages, a11y check)]

**Phase 3: Composition (Platform Team owned, depends on Phase 2)**
[Shell + All MFEs Integration DAG] -> [E2E Tests DAG] -> [Production Approval]

**Phase 4: Deployment**
[Deploy Shell] -> [Deploy MFE A] -> [Deploy MFE B] -> [Canary] -> [Production]

### 5.3 UI Component Library as Platform Artifact

**Critical rule:** The component library (@bvnk/ui) is a **platform artifact** produced by the Platform Team's component DAG. It is:

- **Imported** by every micro frontend DAG node — the DAG does NOT rebuild the component library
- **Versioned** (semver) — MFEs pin a version
- **Tested once** — visual regression tests run on the library, not per MFE
- **Published** to a private npm registry that all MFEs consume

**Dependency contract:** @bvnk/ui + @bvnk/tokens (design tokens) -> Stream-aligned team MFE also imports @bvnk/tokens for custom domain components.

### 5.4 UX Agent Role in the DAG

[Product Spec (Human or product agent)]
       |
UX AGENT DAG NODE:
  Inputs: Product spec, Existing design tokens, User personas
  Actions:
    1. Generate lo-fi wireframes (SVG)
    2. Generate/update design tokens (JSON)
    3. Generate a11y specifications (WCAG compliance targets)
    4. Generate UI component specs (props, states, interactions)
    5. Generate acceptance criteria for each component
  Outputs: Design tokens, Wireframes, A11y specs, Component specs
  Human Gate: UX designer reviews wireframes + tokens before proceed
       |
DOWNSTREAM DAG NODES (Frontend + BFF Agents consume UX outputs)

### 5.5 Testing Strategy for Agentic Frontends

| Layer | Tests | Tool | Deploy Gate? |
|---|---|---|---|
| **Component Library** | Visual regression, snapshot, a11y | Chromatic + Testing Library + axe-core | Blocks library publish |
| **Micro Frontend (Unit)** | Component tests, hook tests, state coverage | Testing Library, Vitest | Blocks MFE build |
| **Micro Frontend (Integration)** | MFE + BFF, mocked downstream | Playwright + MSW | Blocks MFE deploy |
| **BFF** | Resolver tests, schema validation, contract tests | Jest + Apollo Testing | Blocks BFF deploy |
| **Shell** | Cross-MFE navigation, auth flows, global state | Playwright | Blocks shell deploy |
| **E2E** | Full user journeys across all MFEs | Playwright (in CI) | Blocks production |
| **Visual Regression** | Pixel-level baseline comparison | Chromatic / Percy | Blocks production |
| **Accessibility** | axe-core WCAG 2.1 AA | axe-core + Playwright | Blocks every deploy |
| **Performance** | Lighthouse scores (LCP, CLS, FID) | Lighthouse CI | Warning + manual override |
| **Bundle Size** | Per-MFE bundle monitoring | size-limit or webpack-bundle-analyzer | Warning |

### 5.6 Summary: Key Design Decisions for BVNK

| Decision | Recommendation | Rationale |
|---|---|---|
| **Frontend framework** | React (Next.js for shell + micro frontends) | Largest agentic tooling ecosystem; best DAG integration |
| **BFF protocol** | GraphQL (Apollo Federation 2.0) | UI-driven queries, per-domain subgraphs, strong typing |
| **BFF ownership** | Federated subgraphs — each stream-aligned team owns its subgraph; Platform Team owns supergraph gateway | Team autonomy + single frontend endpoint |
| **UI architecture** | Micro Frontends via Module Federation | True independent deployability; production-proven |
| **Design system** | Shadcn/ui + Tailwind + Radix on React | Unstyled primitives + utility CSS + copy-paste DX |
| **Design tokens** | W3C Design Token format + Style Dictionary | Standardised, platform-agnostic, Figma plugin ecosystem |
| **UX agent** | Wireframe generator + token extractor + a11y spec generator | Structured output consumed by downstream agents |
| **a11y enforcement** | axe-core in every frontend DAG node | Zero-WCAG-violation policy; automated |
| **Component testing** | Testing Library + Playwright + axe-core | Tests resemble user behaviour; a11y built-in |
| **Visual regression** | Chromatic (deploy previews) | Git-integrated, Storybook-native, per-PR approval |
| **DAG orchestration** | Each micro frontend = independent DAG subgraph | Parallel execution, team-level autonomy, scalable |

---

## References

1. Calçado, P. (2015). "Pattern: Backends For Frontends" — thoughtworks.com/insights/blog/bff
2. Skelton, M. & Pais, M. (2019). *Team Topologies.* IT Revolution Press.
3. Newman, S. (2021). *Building Microservices, 2nd Edition.* O'Reilly Media.
4. Frost, B. (2016). *Atomic Design.* bradfrost.com/blog/post/atomic-web-design
5. Jackson, C. (2019). "Micro Frontends" — martinfowler.com/articles/micro-frontends.html
6. Geers, O. (2021). *Micro Frontends in Action.* Manning Publications.
7. Geers, O. (2020). "Micro Frontends: Challenges and Solutions" — martinfowler.com
8. Apollo Federation 2.0 — apollographql.com/docs/federation
9. W3C Design Tokens Community Group — tr.designtokens.org/format
10. Deque Systems — axe-core documentation, deque.com/axe
11. WCAG 2.1 — w3.org/TR/WCAG21
12. Module Federation — webpack.js.org/concepts/module-federation (Zack Jackson)
13. Podium — podium-lib.io (FINN.no)
14. Single SPA — single-spa.js.org
15. Nielsen, J. (1994). *10 Usability Heuristics for User Interface Design.* NN Group.
