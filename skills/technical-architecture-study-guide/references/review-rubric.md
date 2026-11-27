# Review Rubric

Apply this before calling a guide complete. Review it like a skeptical technical lead, not a friendly copy editor.

Apply each check to the system and scope under review. A read-only library, for example, can explain its caller contract and failure behavior without inventing queues, billing, or delegated workers.

## Grounding

- Are current behavior, inference, recommendation, and open questions distinguishable?
- Does every material implementation claim have source support?
- Did facts from a reference document leak into an unrelated system?
- Are contradictions and missing evidence visible?

## Product and system boundary

- Is the product problem concrete?
- Are functional, non-functional, and product requirements separated?
- Are scale and constraints stated without invented precision?
- Is the system boundary clear enough to know what is out of scope?

## Ownership and state

- Does every important component have one clear responsibility?
- Does each durable entity have an owner?
- Are product truth, workflow state, projections, caches, and object bytes separated?
- Can the reader tell which system wins when views disagree?

Reject language such as “the platform handles it” when no component or state owner is named.

## End-to-end flow

- Does one representative request connect the client, admission, execution, side effects, storage, and delivery?
- At each asynchronous boundary, are commit, retry, duplication, ambiguity, and reconciliation addressed?
- Does the walkthrough include user-visible intermediate states?
- Can a reader locate a failure from the last durable record that exists?

## Trust, authority, and cost

- Are authentication, authorization, approval, affordability, and credential scope explicit?
- Does delegated work preserve actor identity and cancellation lineage?
- Is untrusted content prevented from silently becoming trusted configuration or memory?
- Are provider cost, internal cost, and customer-facing credits or pricing kept separate?

## Failure and consistency

- Are at-least-once delivery and idempotency described honestly?
- Are stale reads, concurrent writes, conflicts, and compensation covered?
- Does cancellation describe propagation and reconciliation, not a boolean flag?
- Does the kill switch stop descendants, external work where possible, new spend, and credentials?
- Are backpressure and overload behavior explicit?

## Scale and operations

- Are the likely partition key and bottlenecks named?
- Are queue isolation, fairness, provider limits, and hot tenants considered where relevant?
- Do metrics distinguish operational telemetry from product analytics?
- Are freshness checks and reconciliation views tied to decisions or customer harm?

## Verification

- Are deterministic tests used for contracts and state transitions?
- Are statistical evaluations used only for variable behavior?
- Is human judgment reserved for outcomes that actually require it?
- Is completion proved by persisted results and verified side effects rather than a success message alone?

## Tradeoffs and decisions

Every major tradeoff must answer:

1. What are the real alternatives?
2. What does each option make easier?
3. What does each option make worse?
4. What is the current or proposed default?
5. What evidence would change the decision?

Reject a tradeoff that lists only benefits or would fit almost any system.

## Study-guide quality

- Can a new technical lead restate the shortest mental model?
- Can they explain every major component without reading code?
- Can they walk one request and one failure?
- Can they defend the selected tradeoffs?
- Do study questions have inline answers?
- Do open questions include a tradeoff, working default, and decision evidence?

## Strict editing pass

Remove:

- repeated explanations
- generic claims and filler
- unsupported certainty
- code detail that does not improve system understanding
- headings with no decision or learning value
- diagrams that are harder to read than prose
- tables whose cells have become paragraphs
- recommendations disguised as current behavior

The document is ready only when its remaining detail helps the reader reason about ownership, flow, failure, cost, trust, or change.
