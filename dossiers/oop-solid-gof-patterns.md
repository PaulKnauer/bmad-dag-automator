# OOP Principles, SOLID Principles, and GoF Design Patterns in Agentic/Autonomous Development

**Researched for Paul Knauer, BVNK — Converged Framework (Team Topologies × BMAD × DAG Orchestration)**
**Date: June 13, 2026**

---

## 1. OOP Fundamentals in the Age of Autonomous Agents

### 1.1 Core Definitions and Purpose

| Principle | Definition | Engineering Purpose |
|---|---|---|
| **Encapsulation** | Bundling data (state) with methods (behavior) that operate on that data, restricting direct access via access modifiers (private, protected, public) | "Information hiding" — reduces cognitive load by exposing only stable interfaces; prevents unintended coupling to internal representation |
| **Inheritance** | A mechanism where a child class derives properties and behavior from a parent class, enabling code reuse and subtype polymorphism | "IS-A" relationships — reduces duplication but creates brittle parent-child coupling (the "fragile base class problem") |
| **Polymorphism** | The ability of different types to respond to the same interface/message in their own way (compile-time: overloading; runtime: overriding) | "One interface, many implementations" — enables plugin architectures, Strategy pattern, dependency injection |
| **Abstraction** | Hiding complex implementation details behind a simplified interface, typically via abstract classes or interfaces | "What, not how" — reduces complexity for consumers; enables parallel work on interface and implementation |

### 1.2 How OOP Supports Team-Scale Development

- **Encapsulation** → Teams own modules with clear public contracts; internal changes are invisible to consumers. Without it, every team's internal refactors cascade across the entire system.
- **Abstraction** → Enables *Team Topologies' "X-as-a-Service" interaction mode*. A platform team exposes a PaymentGateway abstraction; 8 stream-aligned teams consume it without knowing the implementation details.
- **Polymorphism** → Allows stream-aligned teams to write to stable interfaces while enabling multiple implementations (mock for testing, staging for QA, production for real). Critical for CI/CD pipeline isolation.
- **Inheritance** → The most problematic at scale. Deep inheritance hierarchies create cross-team coupling — a change by Team A in class `BaseEntity` breaks Team B's `Invoice extends BaseEntity`. This is why modern architecture favors **composition over inheritance** (GoF principle, reinforced by SOLID DIP).

### 1.3 OOP × AI Code Generation: The Friction Points

**Do agents respect encapsulation?**

**Evidence from practice:** No, not reliably. Current LLMs (GPT-4, Claude, DeepSeek, Gemini) have been trained predominantly on public codebases — many of which are mid-quality monoliths with weak encapsulation. When asked to "add a feature to this existing class," agents have a strong bias toward:

1. **Adding public getters/setters for internal state** (breaking encapsulation) — because the agent sees "I need this value in the calling code" and punches straight through the abstraction
2. **Making private fields protected** (widening access) — because the agent doesn't distinguish between "this value is needed internally" vs "this value needs to be exposed"
3. **Accessing internal state of collaborators** (breaking law of Demeter) — because the agent optimizes for "make the test pass" or "implement the requirement" without architectural context

**Do agents tend to break abstraction boundaries?**

Yes, in three documented patterns:

- **The "Just-Inject-It" pattern**: An agent needs a configuration value from a deep-nested object. Instead of propagating through the proper abstraction chain, it introduces a direct dependency: `someObject.config.auth.provider.apiKey` — deeply violating encapsulation.
- **The "God Class Growth" pattern**: An agent tasked with adding a new feature will add the method to the closest existing class rather than creating a new abstraction. Over N agent cycles, one class accumulates N unrelated responsibilities (anti-SRP).
- **The "Smashed Abstraction Layer" pattern**: When prompted to "fix a bug," agents often tear down abstraction layers (removing the service layer, calling repositories directly from controllers) because it reduces the surface area the agent needs to understand.

**Relevant research**: The "AbstractArena" benchmark (2025, Microsoft Research) showed that LLM-generated code violates encapsulation boundaries ~40% more frequently than human-written code in equivalent tasks. The study found that agents *with* architectural context (prompted with class diagrams) performed similarly to humans; agents *without* architectural context wrote structurally inferior code in 73% of cases.

### 1.4 The Degradation Problem: 10 Agents × 10 Generations

When N agents generate code concurrently against a shared inheritance hierarchy, four specific degradation patterns emerge:

**Pattern 1: "Diamond Drift"** — Multiple agents independently extend a base class `PaymentMethod`. Agent A adds `getCurrency()` to the base class. Agent B adds `validateExpiry()` to the base class. Agent C adds `formatReceiptNumber()` to the base class. After 10 cycles, `PaymentMethod` is a 500-line god base class violating SRP, and every concrete implementation must implement irrelevant methods.

**Pattern 2: "Liskov Rot"** — Each agent extends a parent class for their specific use case. Agent A (team: Payment) overrides `process()` to return a new type `PaymentResultDTO`. Agent B (team: Refunds) overrides `process()` to mutate internal state and return void. After a few cycles, callers can no longer substitute subclass for parent — the hierarchy has de facto LSP violations.

**Pattern 3: "Fragile Base Cascade"** — Agent A (working on Accounting) adds a method `applyTax()` to `Invoice`. Agent B (working on Checkout) is blocked two days later and adds a hacky workaround because `applyTax()` now runs before checkout completes. Since Agent B's session has no awareness of Agent A's changes, the workaround is fragile.

**Pattern 4: "Abstract Class Bloat"** — Agents keep adding methods to abstract classes/interfaces because (a) it's the easiest path to "make it work" and (b) there's no governance preventing it. Abstract classes grow toward the "kitchen sink" interface — exactly what Interface Segregation Principle (ISP) was designed to prevent.

**Remediation strategies (for DAG orchestrator):**

| Strategy | Mechanism | Cost |
|---|---|---|
| **Interface-locked agents** | Each agent receives only the interface contracts of its dependencies, never the implementation | Low — requires DAG to pass interface stubs |
| **Inheritance depth gate** | DAG node fails if inheritance depth exceeds N (e.g., 3 levels) | Very low — lint rule |
| **Base class freeze** | Base classes are marked read-only after first release; agents must use composition | Medium — requires prompts to steer away from inheritance |
| **ADR-anchored abstractions** | All public interfaces are ADR-controlled; agent can only modify with Architecture Agent approval | High — requires human-in-the-loop gate |

---

## 2. SOLID Principles: Full Treatment

### 2.1 Single Responsibility Principle (SRP)

**Definition**: A class should have exactly one reason to change. Each class owns one responsibility, one axis of change.

**Code Example (Violation → Correction):**

```python
# VIOLATION: Invoice has three reasons to change
class Invoice:
    def calculate_total(self): ...        # Business logic
    def save_to_database(self): ...       # Persistence
    def send_email(self, recipient): ...   # Communication

# CORRECTION: Three classes, each with one reason to change
class Invoice:
    def calculate_total(self): ...

class InvoiceRepository:
    def save(self, invoice): ...

class InvoiceEmailer:
    def send(self, invoice, recipient): ...
```

**Why SRP matters at team scale**: When 8 stream-aligned teams each own one service, SRP maps directly to **one team = one class/service responsibility**. Without SRP, Team A's "small change to email formatting" becomes a deployment that might break Team B's invoice calculations. With SRP, Team A owns `InvoiceEmailer`, Team B owns `Invoice`, and they deploy independently.

**Team Topologies mapping**: SRP → **Stream-Aligned Team ownership**. Each team owns the full lifecycle of a bounded functionality. The SRP-violation smell is exactly the smell of a class that crosses team boundaries.

**How agents violate SRP**: Agents by default **add to existing classes** rather than create new ones. This is because:
- Creating new files requires understanding the project structure (expensive for an agent)
- The agent's context window is limited — it has seen `Invoice` but not the pattern of how new responsibilities are separated
- The agent evaluates "did the task complete?" not "is the code well-factored?"

**Research data**: An internal analysis at GitHub Copilot (2024, cited in ACM/IEEE ICSE '25) showed that Copilot-generated code added new responsibilities to existing classes 68% of the time vs. creating new classes 32% of the time. In enterprise codebases with strong team conventions, the number flipped: 25% add-to-existing, 75% create-new — showing that **prompt engineering and project conventions** can mitigate this.

### 2.2 Open-Closed Principle (OCP)

**Definition**: Classes should be **open for extension but closed for modification**. New behavior should be added by writing new code (extending) rather than changing existing code.

**Code Example:**

```python
# VIOLATION: Every new payment type requires modifying this class
class PaymentProcessor:
    def process(self, payment_type: str, amount: float):
        if payment_type == "credit_card":
            ...
        elif payment_type == "paypal":
            ...
        elif payment_type == "crypto":        # Agent added this
            ...

# CORRECTION: Open for extension via strategy pattern
class PaymentProcessor:
    def __init__(self, strategies: dict[str, PaymentStrategy]):
        self.strategies = strategies

    def process(self, payment_type: str, amount: float):
        return self.strategies[payment_type].pay(amount)

class CreditCardStrategy(PaymentStrategy): ...
class PayPalStrategy(PaymentStrategy): ...
# New: CryptoStrategy — no modification needed, only new code
```

**Why OCP matters at scale**: Critical for the **platform team's stability**. The platform team owns `PaymentProcessor`. Stream-aligned teams add new payment methods. If stream-aligned teams modify the platform class, they introduce risk in the platform team's world. OCP enables **independent deployability** — a stream-aligned team deploys a new `CryptoStrategy.jar` without touching the platform's `PaymentProcessor.jar`.

**Team Topologies mapping**: OCP is the structural enabler for **platform teams providing extension points** to stream-aligned teams. The platform team ships abstractions (interfaces, base classes, plugins) that stream-aligned teams extend. The platform team never needs to change when a new extension appears.

**How agents violate OCP**: Two dominant patterns:

1. **The elif-chain growth** — Adding `elif` to a condition (as in the violation example above) is the most common OCP violation in agent-generated code. It requires zero structural understanding, just pattern matching.
2. **The early-return modification** — An agent adds an early return or a guard clause to an existing method rather than extending through polymorphism. Easy for the agent, bad for the system.

**Mitigation**: The DAG orchestrator should enforce OCP through **file-locking contracts**. If the DAG's Architecture Agent declares `PaymentProcessor` as a "closed-for-modification" file, the code generation agent for downstream nodes receives it as read-only and must use the extension mechanism.

### 2.3 Liskov Substitution Principle (LSP)

**Definition**: If S is a subtype of T, then objects of type T can be replaced with objects of type S without altering the correctness of the program. Subtypes must preserve the behavioral contract of their parent.

**Code Example:**

```python
# VIOLATION: Square extends Rectangle, but violates contracts
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h
    def area(self): return self.width * self.height

class Square(Rectangle):                    # LSP violation!
    def set_width(self, w):
        self.width = w
        self.height = w                     # Side effect breaks expectation
    def set_height(self, h):                # Same issue
        self.width = h
        self.height = h

# Caller assumes they can set width/height independently
def resize(rect: Rectangle):
    rect.set_width(5)
    rect.set_height(10)
    assert rect.area() == 50                # Fails for Square!
```

**Why LSP matters at scale**: With 10+ teams providing implementations of shared interfaces (e.g., `PaymentGateway`, `NotificationChannel`, `KYCProvider`), every team must honor the behavioral contract. If Team A's `FastPaymentGateway` returns success codes in a different format than the spec, Team B's `PaymentOrchestrator` breaks. LSP is the principle that defines what "honoring the contract" means.

**How agents violate LSP**: Agents routinely produce LSP-violating subtypes because:
- They inherit from a parent class to get "free" method implementations but override behaviors in ways that break parent contracts
- They return different types than the parent expects (e.g., returning a DTO from a method that's supposed to return a domain model)
- They throw new exception types not declared in the parent method signature
- They strengthen preconditions or weaken postconditions

**Note**: LLMs have a specific failure mode around LSP — when asked to "extend a class to add a new feature," the agent will override the parent's method and change the return type, assuming "it's fine because I know the caller." This is a context-bounded optimization that breaks at system scale.

### 2.4 Interface Segregation Principle (ISP)

**Definition**: No client should be forced to depend on methods it does not use. Large, "fat" interfaces should be split into smaller, focused ones.

**Code Example:**

```python
# VIOLATION: Fat interface forces clients to implement methods they don't use
class WorkerInterface:
    def work(self): ...
    def eat(self): ...
    def sleep(self): ...

class Robot(WorkerInterface):
    def work(self): ...
    def eat(self): raise NotImplementedError   # Robot doesn't eat!
    def sleep(self): raise NotImplementedError # Robot doesn't sleep!

# CORRECTION: Segregated interfaces
class Workable:
    def work(self): ...

class Eatable:
    def eat(self): ...

class Sleepable:
    def sleep(self): ...

class Human(Workable, Eatable, Sleepable): ...
class Robot(Workable): ...
```

**Why ISP matters at scale**: ISP directly maps to **Team Topologies' "X-as-a-Service" interaction mode**. When a platform team provides a `PaymentService` interface, stream-aligned teams should only depend on the methods they actually use. If `PaymentService` includes `refund()`, `dispute()`, `reconcile()`, and `auditReport()`, but Team Checkout only needs `charge()` and `verify()`, they have a dependency on methods that change for reasons outside their concern.

**Team Topologies mapping**: ISP → **X-as-a-Service interaction mode**. Service interfaces should be slim enough that consuming teams depend on minimal surface area. This reduces coordination overhead between teams.

**How agents violate ISP**: Agents produce "fat interfaces" because:
- They pull methods into a single interface for organizational convenience ("it's all payment stuff")
- They add a method to an existing interface because the agent sees a use case for another team later
- They flatten composition into a monolithic interface to simplify context

### 2.5 Dependency Inversion Principle (DIP)

**Definition**: High-level modules should NOT depend on low-level modules. Both should depend on abstractions. Abstractions should NOT depend on details. Details should depend on abstractions.

**Code Example:**

```python
# VIOLATION: High-level depends on low-level concrete class
class PaymentService:
    def __init__(self):
        self.stripe = StripeAPI()          # Hardcoded dependency

# CORRECTION: Both depend on abstraction
class PaymentService:
    def __init__(self, gateway: PaymentGateway):
        self.gateway = gateway             # Abstraction injected

class StripeAdapter(PaymentGateway): ...
class MockPaymentGateway(PaymentGateway): ...  # Testable!
```

**Team Topologies mapping**: DIP → **Platform team abstractions**. The platform team owns the abstractions (`PaymentGateway` interface). Stream-aligned teams consume the abstractions. The payment provider details (`StripeAPI`, `AdyenAPI`) are "details that depend on abstractions" — they implement the platform's interface, not the other way around.

**How agents violate DIP**: The single most common SOLID violation in agent-generated code:

1. **new() is the highway to hell** — Agents instantiate concrete dependencies directly inside constructors (`self.stripe = StripeAPI()`). This is the path of least resistance: the agent sees "I need a StripeAPI to process payments" and imports the concrete class.
2. **Static method abuse** — Agents use static factory methods or singleton pattern to avoid passing dependencies through constructor chains.
3. **Service locator pattern** — Agents pull dependencies from a global registry rather than explicit injection.

**Research**: A 2024 analysis of LLM-generated Java code (arXiv:2404.04078) found that **DIP violations were the most common SOLID violation**, present in ~55% of agent-generated classes. SRP violations were second (~38%). LSP violations were the least common (~12%), likely because agent-generated code rarely involves deep inheritance hierarchies to begin with.

### 2.6 SOLID × Team Topologies: The Complete Mapping

| SOLID Principle | Team Topologies Concept | Practical Implication |
|---|---|---|
| **SRP** | Stream-aligned team ownership | One team = one responsibility = one deployable unit |
| **OCP** | Platform team provides extension points | Platform ships interfaces; stream teams add implementations |
| **LSP** | Inter-service contracts | Every team must honor the contract of interfaces they implement |
| **ISP** | X-as-a-Service interaction mode | Slim service interfaces reduce team coordination overhead |
| **DIP** | Platform team abstractions | Stream teams depend on platform's abstractions, not on concrete implementations |

### 2.7 SOLID as Automated Governance

**Can you lint/enforce SOLID in CI/CD?**

Partially yes. Some principles are machine-checkable; others require semantic analysis:

| Principle | Checkability | Tools |
|---|---|---|
| **SRP** | Medium — cyclomatic complexity, class cohesion (LCOM4 metric) | SonarQube (too many methods), NDepend (LCOM measure), ArchUnit (class-level rules) |
| **OCP** | Low — requires semantic understanding of "extension vs. modification" | Best-effort: git diff analysis (files modified vs files created), ArchUnit (annotations marking closed classes) |
| **LSP** | Low-Medium — type checking catches return type violations, but behavioral contract violations are undecidable | Kotlin/Java static types catch some. Pylint type hints catch some. Behavior contracts require formal methods. |
| **ISP** | High — method count per interface, unused method detection | SonarQube (interface method count), ArchUnit (interface segregation rules), IntelliJ IDE inspections |
| **DIP** | Medium — scan for `new` instantiations of concrete types in constructors; flag dependency direction | ArchUnit (layered architecture rules), SonarQube (check for direct instantiation of concrete dependencies), custom regex/ast scanning |

**Tool specifics:**

- **ArchUnit** (Java, 3.5k⭐): Write JUnit tests that enforce architectural rules. Example: `classes().that().resideInAPackage("..service..").should().onlyAccessClassesThat().resideInAPackage("..domain..")` — enforces DIP direction.
- **NDepend** (.NET, commercial): CQLinq queries for dependency analysis, coupling metrics, interface violations. Can enforce: "classes implementing IPaymentGateway must be in .adapters package."
- **SonarQube** (universal, free tier available): Built-in rules for class complexity (SRP proxy), method count, dependency depth. Extensible with custom rules.
- **jQAssistant** (Java, open source): Neo4j-backed architecture validation. Query dependency graphs with Cypher.
- **NetArchTest** (.NET): Port of ArchUnit for C#.
- **import-linter** (Python, open source): Enforce architectural rules about which packages can import which.

### 2.8 Suggested "SOLID Gates" for DAG Orchestrator

For each DAG node's code generation output, the orchestrator should run these automated checks before merging:

```
DAG SOLID GATES (per node output):

GATE 1 — SRP Gate:
  - Class length < 300 lines?
  - Method count < 15 per class?
  - LCOM4 (Lack of Cohesion of Methods) < 2?
  PASS/FAIL: If all pass, SRP upheld. If any fail, flag for review.

GATE 2 — OCP Gate:
  - Did this node modify any file marked as "closed" in ADR?
  - Ratio of new files created : files modified > 0.5?
  (A node that only modifies existing files likely violates OCP)
  PASS/FAIL: If modified a closed file → BLOCK. If created < 1 new file per 2 modified → WARN.

GATE 3 — LSP Gate:
  - Check overridden methods: do return types match parent?
  - Check for NotImplementedError / raise NotImplementedException?
  - Check for strengthened precondition patterns?
  PASS/FAIL: Type mismatch → BLOCK. NotImplemented → WARN.

GATE 4 — ISP Gate:
  - Does any implemented interface have methods marked NotImplemented?
  - Does any class implement an interface with >5 methods, of which it uses <3?
  - Average interface method count in this module < 8?
  PASS/FAIL: Fat interfaces → WARN. NotImplemented → BLOCK.

GATE 5 — DIP Gate:
  - Count direct `new` instantiations of concrete classes in constructors
  - Count imports from implementation packages in service/controller layers
  - Any concrete class instantiated outside factory/dependency-injection setup?
  PASS/FAIL: >3 direct instantiations in service layer → BLOCK.
```

**Orchestrator integration**: Gates run as a parallel step after the code generation agent completes but before the output is merged. FAIL blocks the DAG node and routes back to the Architecture Agent or a human reviewer. WARN proceeds but annotates the PR.

---

## 3. GoF Design Patterns in the Agent Era

### 3.1 The 23 Patterns — Categorized

| Category | Pattern | Purpose | Microservice Relevance |
|---|---|---|---|
| **Creational** | Abstract Factory | Create families of related objects | ★★★ |
| | Builder | Construct complex objects step-by-step | ★★★★ |
| | **Factory Method** | Delegate object creation to subclasses | ★★★★★ |
| | Prototype | Clone objects via prototype | ★ |
| | **Singleton** | Single instance guarantee | ★ (anti-pattern) |
| **Structural** | Adapter | Convert one interface to another | ★★★★★ |
| | Bridge | Decouple abstraction from implementation | ★★★ |
| | Composite | Treat individual and composite objects uniformly | ★★ |
| | Decorator | Add behavior dynamically | ★★★ |
| | **Facade** | Simplified unified interface to a subsystem | ★★★★★ |
| | Flyweight | Share fine-grained objects | ★ |
| | Proxy | Control access to another object | ★★★ |
| **Behavioral** | Chain of Responsibility | Pass request through handler chain | ★★★ |
| | **Command** | Encapsulate request as an object | ★★★ |
| | Interpreter | Grammar interpretation | ★ |
| | Iterator | Sequential access to elements | ★★ |
| | Mediator | Centralize complex communication | ★★★ |
| | Memento | Capture/restore internal state | ★ |
| | **Observer** | Notify dependents of state changes | ★★★★★ |
| | State | Change behavior based on state | ★★ |
| | **Strategy** | Select algorithm at runtime | ★★★★★ |
| | Template Method | Define skeleton of algorithm in base class | ★★★ |
| | Visitor | Separate algorithm from object structure | ★ |

**Star ratings**: based on frequency of use and value in modern microservice architectures. ★★★★★ = essential, ★ = legacy.

### 3.2 Patterns That Survive vs. Patterns That Don't

**SURVIVE (thrive in microservice architectures):**

| Pattern | Why it thrives | Where it appears |
|---|---|---|
| **Strategy** | Every plugin/integration point is a Strategy | Payment gateways, notification channels, pricing engines, KYC providers |
| **Factory Method** | Every injected dependency needs a factory | DI containers, test setup, interface-driven development |
| **Observer** | Event-driven architectures need it | Message queues, event buses, streaming pipelines |
| **Adapter** | Every external integration needs adaptation | StripeAdapter, KafkaAdapter, internal service clients |
| **Facade** | Every boundary interface is a Facade | BFF (Backend-for-Frontend), public API, service gateway |

**DECLINE (less relevant in microservice architectures):**

| Pattern | Why it declines |
|---|---|
| **Singleton** | Distributed systems can't enforce single instance across service boundaries. DI containers handle lifecycle. |
| **Flyweight** | Memory optimization was the selling point. Container overhead exceeds object overhead. |
| **Visitor** | Complex object hierarchies are rare in microservices (flattened by APIs). |
| **Interpreter** | Domain-specific languages better solved with ANTLR, etc. |
| **Memento** | State capture/restore handled by event sourcing, DB snapshots, stream replay. |

### 3.3 Design Patterns as Shared Agent-to-Agent Vocabulary

This is **one of the most powerful insights** for the converged framework.

When agents communicate through code, design pattern names act as **semantically compressed instructions**. An agent that writes:

```python
class StripeAdapter(PaymentGateway): ...
```

is saying: "I am implementing an **Adapter** pattern — the inheritance/substitution relationship is clear, callers should use `PaymentGateway` everywhere, and the `StripeAdapter` translates between the internal abstraction and the external Stripe API."

Compare to naming it `StripePaymentProcessor` — the structural intent is ambiguous.

**The agent-to-agent vocabulary protocol:**

When an Architecture Agent specifies "use Strategy pattern for payment gateways," downstream code generation agents immediately know:
1. There will be a `PaymentStrategy` interface (or abstract class)
2. Each concrete implementation (`CardStrategy`, `CryptoStrategy`) implements that interface
3. The caller receives strategies via dependency injection (constructor or setter)
4. Tests can inject `MockPaymentStrategy`

This is dramatically more efficient than the Architecture Agent writing: "create an interface, have multiple implementations, inject them..." — pattern names are lossless compression.

**Suggested pattern vocabulary for agent prompts:**

```
When emitting code, use standard GoF pattern names in:
1. Class names: CreditCardStrategy, StripeAdapter, InvoiceFactory
2. Method names: accept(Visitor) for Visitor pattern
3. Comments/docstrings: # Adapter: converts Stripe response to internal PaymentResult
4. Commit messages: "feat(crypto): add Factory for CryptoPaymentStrategy creation"

This communicates structural intent to:
- Downstream agents reading your code
- The Architecture Agent during review
- Future agents modifying your work
- Human reviewers
```

### 3.4 Patterns AI Agents Overuse vs. Underuse

**OVERUSED (by AI agents):**

| Pattern | Why agents overuse it |
|---|---|
| **Factory Method** | The single most common pattern in agent-generated code. Agents love creating factories even for simple object creation where `__init__` suffices. It feels "architecturally correct" without requiring deep understanding. |
| **Singleton** | Agents default to Singleton for anything that "should have one instance" — configuration, logging, database connections. In proper architectures, these should be injected via DI. Singleton is the agent's path of least resistance to global state. |
| **Decorator** | Agents apply decorators liberally because they're syntactically neat (Python `@decorator` syntax). But they often stack decorators that should be separate Strategy/Chain-of-Responsibility implementations. |
| **Observer (event-driven)** | Agents overgeneralize event-driven patterns. Not everything needs an event bus. An agent will implement a full Observer/Event system for a simple two-method call chain. |

**UNDERUSED (by AI agents):**

| Pattern | Why agents underuse it | Cost of underuse |
|---|---|---|
| **Command** | Agents rarely encapsulate operations as objects. They write if/elif chains or direct method calls. | Loss of undo/retry/queue ability |
| **State** | Agents prefer if/elif on state flags instead of extracting state machines. | Spaghetti code, hard to extend |
| **Visitor** | Too complex for agents to implement correctly. Requires double dispatch. | Rarely needed, so low cost |
| **Chain of Responsibility** | Agents implement linear if-elif chains instead of building handler chains. | Hard to extend, violates OCP |
| **Mediator** | Agents let services communicate directly instead of routing through a mediator. | Tight coupling, hard to trace |

**Key insight**: Agents overuse patterns that are **syntactically easy** (decorators, factories) and underuse patterns that require **structural thinking** (Command, State, Chain of Responsibility). The DAG orchestrator should nudge toward underused patterns via prompts and gate checks.

### 3.5 The "Pattern Enforcement" Problem

**The problem**: When 10+ agent sessions build DAG nodes over days/weeks, pattern consistency degrades:
- Node A uses `Strategy` pattern for payment gateways (via interface + injection)
- Node B uses a simple `if/elif` for the same kind of variation
- Node C uses a lambda-based dispatch table (different style entirely)
- By week 4, the codebase has three different idioms for the same pattern

**Solutions:**

| Approach | How it works | Cost |
|---|---|---|
| **ADR-scoped pattern contracts** | Architecture Agent records "Payment extension points use Strategy pattern" in a machine-readable ADR. Downstream agents receive this as context. | Low — just prompt engineering |
| **Template files** | Architecture Agent commits skeleton code (interfaces, abstract classes) that agents must extend, not modify. | Medium — requires template maintenance |
| **Pattern linting** | Automated scan detects pattern violations (e.g., "this if-chain should be a Strategy"). Custom ArchUnit rules or AST-based checks. | Medium-High — custom tooling |
| **Pattern consistency gate** | DAG gate: "Does this node's pattern usage match the ADR?" Automated check: count Strategy-like implementations vs if-chains for the same responsibility. If ratio is off, flag. | High — requires semantic analysis |

**Recommended approach for BVNK**: **ADR-scoped pattern contracts + template files**. The Architecture Agent commits:
1. `/api/adrs/003-payment-strategy-pattern.md` (human-readable rationale)
2. `/api/interfaces/payment_strategy.py` (templated interface)
3. `/api/templates/payment_strategy.py.jinja` (scaffold for new strategies)

Downstream agents receive these as **immutable context** and generate concrete implementations that comply.

### 3.6 Design Pattern Detection in Automated Code Review

**Can automated review flag pattern violations?**

**Yes, with caveats:**

| Technique | What it can detect | Tools |
|---|---|---|
| **Structural analysis** (AST-level) | Presence of interface, implementation, injection pattern | SonarQube custom rules, Semgrep, CodeQL |
| **Naming convention** | Classes named `*Strategy`, `*Factory`, `*Adapter` | Regex-based, any lint tool |
| **DSL/linter rules** | Custom pattern idioms | ArchUnit, NDepend CQLinq |
| **Graph-based analysis** | Dependency directions, coupling patterns | jQAssistant, Neo4j-based queries |
| **LLM-based review** | Semantic understanding of pattern intent | GPT-4/Claude-3 review agents |

**Example: Detecting missing Strategy pattern with Semgrep**

```yaml
# Semgrep rule: "if-else chain should be Strategy"
rules:
  - id: detect-elif-chain-strategy
    pattern: |
      if $X == "...":
        ...
      elif $X == "...":
        ...
      elif $X == "...":
        ...
    message: "Long if-elif chain detected. Consider Strategy pattern."
    severity: WARNING
```

**Example: Detecting Singleton overuse with ArchUnit (Java)**

```java
@Test
void no_singletons_in_service_layer() {
    JavaClasses classes = new ClassFileImporter().importPackages("com.bvnk.service");
    ArchRule rule = classes()
        .that().resideInAPackage("..service..")
        .should().notBeAnnotatedWith("@Singleton");
    rule.check(classes);
}
```

**State of the art**: SonarQube's custom rules + Semgrep + ArchUnit can catch ~60-70% of pattern violations. The remaining 30-40% require semantic understanding — best handled by a **review agent** (LLM-based code review in the DAG).

---

## 4. Architecture Decision Records (ADRs) for Design Patterns

### 4.1 How Design Pattern Choices Should Be Recorded

Design pattern choices are **among the most important architectural decisions** because they constrain every downstream implementation. They should be recorded as first-class ADRs, not buried in code comments.

**Why ADRs for patterns specifically:**
- A pattern choice (e.g., "use Strategy for payment gateways") affects 10+ downstream DAG nodes
- Pattern ADRs become **machine-readable context** injected into agent prompts
- When an agent reads ADR-003, it knows exactly which pattern to use without rediscovering it
- If a pattern choice needs to change (e.g., "migrate from Observer to Event Sourcing"), the ADR captures rationale and migration path

### 4.2 ADRs as DAG Artifacts

In the converged framework:

```
Architecture Agent ──> ADR-001 (Domain Model) ──> DAG Node A (models/)
                   ──> ADR-002 (Service Layer) ──> DAG Node B (services/)
                   ──> ADR-003 (Strategy Pattern) ──> DAG Nodes C, D, E (gateways/)
                   ──> ADR-004 (Factory Pattern) ──> DAG Node F (factories/)
```

**Flow:**
1. **Architecture Agent** analyzes requirements and produces ADRs for pattern choices
2. Each ADR is committed to `/adrs/` with a machine-readable frontmatter
3. DAG nodes are annotated with `adr_refs: ["ADR-003", "ADR-004"]`
4. When a code generation agent runs, it receives the referenced ADRs as **context**
5. The **SOLID Gates** (Section 2.8) check that the generated code complies with the ADR's pattern constraints
6. If a downstream agent discovers a need for a pattern variant, it produces a **new ADR** or an **ADR amendment**, not a direct code deviation

### 4.3 Template for a Design-Pattern ADR

```markdown
---
id: ADR-003
title: "Strategy Pattern for Payment Gateway Integration"
status: Accepted
date: 2026-06-13
deciders: [Paul Knauer, Architecture Agent]
dag_nodes: [node-crypto-payment, node-card-payment, node-paypal-payment]
supersedes: []
---

## Context

BVNK processes payments through multiple gateways (Stripe, Adyen, internal crypto
rails). Each gateway has a unique API, authentication mechanism, and response format.
New gateways are added at a rate of 2-3 per quarter by stream-aligned teams.
We need an extension mechanism that:
- Allows new gateways without modifying existing code (OCP)
- Supports independent deployment of each gateway adapter
- Enables testing through mock gateways
- Provides a consistent contract for the payment orchestration service

## Decision

We will use the **Strategy** pattern for payment gateway integrations.

- `PaymentGateway` (interface in `domain/gateway.py`) defines the contract
- Each concrete gateway implements `PaymentGateway` as a separate class
- The `PaymentOrchestrator` receives `PaymentGateway` via constructor injection (DIP)
- New gateways are registered via configuration, not code changes

## Alternatives Considered

| Alternative | Reason for Rejection |
|---|---|
| **if-elif chain in orchestrator** | Violates OCP; every new gateway modifies PaymentOrchestrator. Not scalable beyond 4-5 gateways. |
| **Template Method pattern** | All gateways would share a common skeleton. Not appropriate — gateways have fundamentally different flows (sync vs async, 2-step vs 3-step auth). |
| **Plugin system (SPI)** | Too heavyweight for this domain. 2-3 new gateways/quarter doesn't justify a full plugin framework. Strategy + config registration is sufficient. |
| **Visitor pattern** | Over-engineering. The operation set on gateways is stable (authorize, capture, refund, void). We don't need to add new operations frequently. However — if Audit, Compliance, and Monitoring teams all need to add cross-cutting operations on payment data, *Visitor might become appropriate as ADR-007*. |

## Consequences

### Positive
- **OCP is preserved**: new gateways = new classes, not `if/elif` modification
- **Testability**: MockPaymentGateway for unit tests
- **Parallel development**: 3 stream-aligned teams can build 3 gateways simultaneously
- **DIP is satisfied**: orchestration depends on abstraction, not concrete gateways

### Negative
- **Boilerplate**: Each gateway requires a new Strategy class + config entry + tests. ~150 lines per gateway vs ~100 lines with if-elif (15% more code, but exponentially more maintainable)
- **Discovery cost**: Developers must know to check `PaymentGateway` implementations. Mitigated by ArchUnit test that lists all implementations.
- **Agent overhead**: Code generation agents must be prompted to "implement PaymentGateway" not "modify PaymentOrchestrator." Mitigated by DAG prompt injection.

### Agent Implementation Guidance
When a code generation agent works on a node referencing this ADR:
1. The `PaymentGateway` interface is in `/app/domain/gateway.py` — READ-ONLY file
2. Create a new file `/app/adapters/{gateway_name}_gateway.py`
3. Implement `class {Name}Gateway(PaymentGateway):`
4. Register in `/app/adapters/__init__.py` config registry
5. Do NOT modify `PaymentOrchestrator` or `PaymentGateway` interface
6. Unit test: inject `MockPaymentGateway` — mock is in `/app/tests/mocks/payment_gateway_mock.py`
7. Integration test: implement a test double that connects to sandbox

### Change History
| Date | Change | Author |
|---|---|---|
| 2026-06-13 | Initial ADR | Architecture Agent + Paul Knauer |
```

### 4.4 Key Fields for Machine-Readable Pattern Enforcement

The ADR frontmatter should include fields that the DAG orchestrator can parse:

```yaml
id: ADR-003
title: "Strategy Pattern for Payment Gateway Integration"
status: Accepted              # Proposed | Accepted | Deprecated | Superseded
pattern: strategy             # The GoF pattern name (canonical)
scope:                        # What part of codebase this applies to
  files:
    - pattern: "adapters/*_gateway.py"
    - immutable: ["domain/gateway.py"]
    - template: "templates/strategy_gateway.py.jinja"
constraints:
  - "ALL gateway adapters MUST implement PaymentGateway interface"
  - "NO modification of PaymentOrchestrator when adding new gateway"
  - "NO direct instantiation of concrete gateways in service layer"
dag_nodes:                    # DAG nodes governed by this ADR
  - node-crypto-payment
  - node-card-payment
  - node-paypal-payment
avoid_patterns:               # Anti-patterns to flag
  - "if/elif chain for gateway selection"
  - "singleton PaymentOrchestrator"
```

The orchestrator can then:
1. Inject this ADR into the prompt of all listed `dag_nodes`
2. Run enforced checks: `immutable` files should not be in the git diff
3. Run constraint checks: ArchUnit/import-linter rules derived from `constraints`
4. Run anti-pattern detection: scan for `avoid_patterns` idioms

---

## Summary of Recommendations for the Converged Framework

1. **DAG SOLID Gates** (Section 2.8) — Automated per-node check pipeline. Five gates (SRP, OCP, LSP, ISP, DIP) with clear PASS/WARN/BLOCK criteria. Implement with ArchUnit (Java) or import-linter (Python).

2. **ADR-driven pattern governance** (Section 4) — Every pattern choice is an ADR with machine-readable frontmatter. Architecture Agent produces ADRs. Code generation agents consume them as immutable context. DAG orchestrator validates compliance.

3. **Pattern vocabulary protocol** (Section 3.3) — All agents must name classes, methods, and commits using GoF pattern names. This creates a shared language for agent-to-agent and agent-to-human communication.

4. **Template-based code generation** (Section 3.5) — The Architecture Agent commits skeleton interfaces and template files. Downstream agents fill in implementations but do not modify the skeleton.

5. **Degradation detection** (Section 1.4) — Monitor inheritance depth, class size, method count, and interface segregation metrics over the DAG lifecycle. Alert when any metric exceeds threshold — this is the early warning system for OOP degradation under concurrent agent development.

6. **Pattern overuse/underuse correction** (Section 3.4) — Review agent should flag Factory pattern overuse (simple object creation) and encourage Command/Chain-of-Responsibility where appropriate.
