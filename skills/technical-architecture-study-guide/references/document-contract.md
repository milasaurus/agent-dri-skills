# Document Contract

Use this contract to draft or audit a technical architecture study guide. Preserve the architectural questions, but rename, combine, or omit headings when the technical area has a better equivalent. Never leave an irrelevant section in place merely to match the template.

## Reader outcome

The finished guide should let a technical lead:

1. explain the product and system requirements
2. draw the main components and state ownership
3. walk one request from admission to completion
4. defend the important design choices
5. diagnose a failure from the last durable boundary
6. discuss consistency, scale, cost, security, and release behavior
7. distinguish current behavior from recommendations and open questions

## Recommended structure

### 1. What are we designing?

Cover the product problem, intended users, questions to settle, product requirements, functional requirements, non-functional requirements, constraints, non-goals, and expected scale.

Do not mix user-visible requirements with implementation choices.

### 2. What is the high-level architecture?

Include:

- a readable component map
- the major phases of a request
- a short mental model for reading the system
- a component-by-component explanation
- one representative end-to-end request
- the invariants that hold the design together

For every component, explain ownership, inputs, outputs, prohibited decisions, and failure behavior.

### 3. What state is durable, and who owns it?

Separate:

- durable product truth
- workflow or execution state
- caches and projections
- files, objects, or artifacts
- versioned configuration
- ephemeral process state

Include a source-of-truth versus projection map. Explain which system wins when two views disagree.

### 4. Walk through one operation

Trace one representative product action through the system. At each step, name the input, owner, durable write, next handoff, user-visible state, main failure, and relevant tradeoff.

### 5. How does the system find, read, and modify domain data?

Explain the technical area's equivalent of navigation and search: listing, querying, indexing, reading authoritative records, inspecting raw data, resolving stable identity, detecting stale reads, and handling concurrent edits.

Include a safe read-modify-verify sequence.

### 6. What is the core data model?

List the durable entities and their relationships. The model should make failures locatable by showing the last durable entity that exists.

Include a component-responsibilities table when it improves comparison:

| Component | Owns | Does not own |
| --- | --- | --- |

### 7. Where does uncertain or external behavior stop and deterministic control take over?

Use the boundary that fits the system:

- model versus code
- policy versus mechanism
- planner versus executor
- control plane versus data plane
- user intent versus authorized operation
- internal transaction versus external provider effect

Explain validation, authorization, approval, affordability, idempotency, and finalization.

### 8. How do coordinators, executors, workers, and specialist systems fit together?

Explain which layer chooses work, which controls lifecycle, which performs side effects, how delegation works, how actor identity survives delegation, and how budgets and cancellation propagate.

If multiple execution paths exist, explain why and whether they should converge on one lifecycle contract.

### 9. Walk through the most important production flow

Choose the highest-value or highest-risk flow. Show the parent request, child or external work, provider boundaries, storage, finalization, billing or settlement, and delivery back to the product.

End with a debugging guide based on the last boundary that exists.

### 10. How do reusable capabilities, configuration, and context work?

Adapt this to the system's reusable state: skills, memory, schemas, configuration, policies, plugins, models, templates, or releases.

Explain versioning, pinning, provenance, trust, migration, freshness, and reproducibility.

### 11. What execution modes exist?

Compare the relevant modes, such as synchronous versus asynchronous, direct versus orchestrated, interactive versus batch, or parent versus specialist execution.

Explain routing, product behavior, operational cost, and failure semantics.

### 12. How does consistency and failure handling work?

Cover the cross-system handoffs that can become ambiguous. Address:

- strong and eventual consistency
- per-entity ordering versus global ordering
- at-least-once delivery
- idempotency and deduplication
- read-your-writes behavior
- conflict detection
- compensation versus rollback
- cancellation
- kill switches
- backpressure
- repair and reconciliation

Close with the practical consistency goal in plain English.

### 13. How does the system scale and stay affordable?

Explain partitioning, concurrency, queue isolation, fairness, hot tenants, latency budgets, storage growth, payload or context growth, provider limits, and cost attribution.

Keep vendor cost, internal compute, and customer-facing pricing separate.

### 14. How do we operate and debug it?

Explain actor and request tracing, correlation IDs, metrics, logs, product analytics, cost telemetry, freshness checks, reconciliation views, alerts, and runbooks.

Do not treat an analytics dashboard as operational truth.

### 15. How do we verify and release behavior?

Separate:

- deterministic tests
- integration and failure-injection tests
- statistical evaluations
- production canaries
- human judgment

Define the evidence required to prove an operation or delegated worker is finished. Include release gates, rollback behavior, and owners.

### 16. What tradeoffs did we choose?

For each material decision, state what was chosen, what was rejected, what the choice buys, what it makes worse, and what evidence would trigger reconsideration.

Reject tradeoffs that could describe any architecture.

### 17. How should a technical lead explain this design?

Provide an interview walkthrough:

1. clarify requirements
2. estimate scale
3. establish durable truth
4. draw the architecture
5. walk one request
6. discuss failures and recovery
7. scale the bottlenecks
8. close with chosen tradeoffs

Add study questions with inline answers. Add genuinely unresolved design questions with **Tradeoff**, **Working default**, and **Decision evidence**.

## Representation rules

- Use question-based headings.
- Keep diagrams narrow enough to read at normal document width.
- Use short node labels and explain the flow below the diagram.
- Prefer prose when a diagram would require zooming.
- Use tables for repeated comparison fields, not for mini-essays.
- Keep code references out of the main narrative unless they prove a contract.
- Use one concrete product example throughout when possible.
