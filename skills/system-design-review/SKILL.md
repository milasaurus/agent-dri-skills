---
name: system-design-review
description: Review a proposed system design from a staff-level architectural lens, anchoring recommendations in reliability, maintainability, scalability, availability, latency, and operability.
trigger:
  - "A design proposal is ready for review."
  - "A team requests architecture-level feedback on a system."
archetypes:
  - architect
  - staff-reviewer
  - tech-lead
---

## Overview

This skill guides an agent through a focused architecture review that checks whether a system is built as a composable, configurable, operable architecture rather than a set of brittle point solutions.

It encodes a staff-level checklist for distributed systems and data-intensive workflows, with a strong emphasis on:
- separating business logic from execution,
- composing reusable components,
- building on shared infrastructure or avoiding independently maintained duplicates, and
- validating every design against DDIA fundamentals.

## When to Use

Use this skill when:

- a system design or architecture document is being reviewed before implementation,
- a proposal introduces a new pipeline, service, or data flow for production systems,
- a team is building or extending infrastructure, data systems, or product surfaces,
- a reviewer must decide whether the design is sound enough to approve, refine, or require non-trivial changes.

## Process

1. Scope
   - Confirm what this design is trying to accomplish and who
     it serves. What is the user-facing or customer-facing
     change? What behavior changes for the end user?
   - Identify the business goal and its value. Is this reducing
     cost, increasing revenue, improving reliability, accelerating
     developer velocity, or enabling a new product capability?
     If the business value isn't clear, the design shouldn't
     proceed.
   - Agree the top 1-2 quality goals for the review: correctness,
     reliability, latency, scale, cost, or operability.
   - Check whether this design aligns with existing technical
     direction — shared infrastructure, established patterns,
     approved tooling. If it diverges, is there a documented
     reason why?
   - Check whether this is intended to reuse shared infrastructure
     or create something that will need independent maintenance.

2. Decomposition
   - Check whether concerns are separated cleanly or tangled
     together.
   - Map the core execution and data flow through the system's
     components.
   - Identify the leverage points: the interfaces between systems,
     the stateful components, and the data model. These are where
     extra investment now prevents the most expensive rework later.
   - For interfaces: does it expose essential complexity without
     leaking accidental complexity? Is it narrow enough to evolve
     the implementation without breaking callers?
   - For stateful systems: are failure modes and consistency
     behaviors exercised in the design? Is the state schema
     tolerant of evolution over time?
   - For data models: does it only allow valid states? Is it
     simple enough that the next engineer can reason about it
     without the original author present?
   - Verify whether pieces can evolve independently without
     forcing a single global change.

3. Assess fundamentals against the design — ask the questions
   product engineers actually ask:

   **Data model and storage**
   - What is the primary key structure and how does it affect
     read and write patterns? Will range queries work at the
     expected data volume or will they require full scans?
   - Are there multiple stores being written together — and if
     one write succeeds and another fails, what is the
     consistency guarantee? Is there a compensating transaction
     or is the system eventually consistent by design?
   - What is the TTL or retention strategy? Is there a cleanup
     job, a hard truncation, or indefinite storage — and what
     are the capacity implications of each?

   **Reliability and failure modes**
   - Where does the system fail open vs. fail hard? What happens
     to in-flight writes during a downstream outage — dropped,
     retried, or queued for later processing?
   - Are there hot keys or high-volume entities whose write
     volume will concentrate load on specific shards? What is
     the strategy for handling that concentration?
   - If the read and write paths share infrastructure, will
     write spikes degrade read latency? Should they be
     decoupled into separate clusters?

   **Scalability**
   - What are the actual load numbers — RPS today, projected
     peak, spike multiplier? Is that validated against the
     storage and compute capacity in the design?
   - What happens at 10x load? Where are the bottlenecks —
     the write path, the read path, a shared dependency, or
     the data store itself?
   - Are there N+1 read patterns — fetching a list and then
     making per-item calls to hydrate details? Where does
     caching help and what is the invalidation strategy?

   **Rollout and experimentation**
   - Is there a staged rollout plan — dark writes, shadow reads,
     percentage ramp via feature flag or decider? At what
     traffic percentage do you validate before full launch?
   - What metric defines success and what defines a rollback
     trigger? Is there a holdback group or control to measure
     against?
   - Can individual code paths be disabled without a deploy?
     Are feature flags scoped per user, per region, or globally?

   **Observability and operability**
   - Are SLOs defined with specific numbers — availability %,
     p99 latency ms, error rate threshold? Are monitoring
     dashboards linked in the doc?
   - Can a missing or incorrect result be debugged without
     reading source code? Is there a request lifecycle trace
     from ingestion to delivery?
   - What alerts exist for the most likely failure scenarios —
     downstream outage, hot shard, store reject spike,
     elevated error rate on a specific path?

   **Migration and backwards compatibility**
   - If this replaces an existing system, what happens to data
     written in the old format? Is there a backfill, a dual-read
     path, or a hard cutover?
   - Can the migration be rolled back without data loss? Is
     there a plan for partially migrated state if a rollback
     is triggered mid-ramp?
   - Are there downstream consumers of the old API or data
     format that need to be migrated in lockstep?

4. Operability
   - Confirm the design can be debugged and recovered without
     reading source code.
   - Ask whether the system exposes enough observability to
     explain expected and failure behavior.
   - If the design is acceptable, make feedback specific,
     actionable, and scoped to the review context.

## Rationalizations

- "This is a special case; the normal stack is too slow."
  - Rebuttal: special cases become maintenance liabilities.
    Confirm whether a true shared-infrastructure exception
    exists and keep the default path as the first option.

- "We can add monitoring later once it's working."
  - Rebuttal: observability drives correct architecture. If
    you can't debug the design now, you can't safely launch
    it later.

- "We only need today's traffic profile."
  - Rebuttal: staff review requires testing against growth.
    A design that fails at 2x is unsafe even if it works today.

- "This is just a data pipeline, not a system design problem."
  - Rebuttal: data-intensive systems are systems. They still
    require explicit failure handling, layered architecture,
    and operability.

- "The component is reusable enough; we can refactor later."
  - Rebuttal: reusable components must be designed up front.
    If composability is missing, you are already building
    technical debt.

- "We should build this as a platform so other teams can use it."
  - Rebuttal: platforms are discovered, not designed. Build
    for the current use case first. If three independent teams
    need the same thing, then generalize. Premature platforms
    are expensive to maintain and rarely adopted.

- "This needs full architecture review sign-off before we proceed."
  - Rebuttal: reviews should unblock, not gate. If a design
    is directionally sound, say so and note what to revisit
    post-launch. Holding work hostage to a perfect design is
    a bottleneck, not a quality bar.

## Red Flags

- The business value or user-facing impact of the change is not
  stated. A design without a clear goal cannot be evaluated
  against the right quality bar.
- A single service or module owns multiple concerns with no
  clear separation between them.
- The design relies on hardcoded rules or control flow instead
  of configuration and reusable components.
- No explicit failure modes, retry/backoff behavior, or
  degraded-path handling are documented.
- Observability is limited to dashboards, with no tracing or
  structured diagnostics for runtime decisions.
- The proposal creates duplicate infrastructure instead of
  reusing shared infrastructure or a common library.
- No evidence the architecture was evaluated against 10x load
  or meaningful scale assumptions.
- The design introduces platform-level infrastructure to solve
  what is currently a single-team or single-use-case problem.
  Fix the specific problem first; generalize only when the
  pattern repeats across multiple teams.
- The review produces observations but no actionable
  recommendations. A review that doesn't tell the team what
  to do next has not completed its job.
- The reviewer is making binding decisions on implementation
  details they are not close enough to the code to evaluate.
  Staff review is directional, not prescriptive.

## Verification

In a review, the agent should be able to answer these questions
clearly before closing:

- What is the user-facing or business impact of this change,
  and is the value clearly understood?
- What are the system's component boundaries and how does data
  or control flow through them?
- Where are the leverage points — interfaces, stateful systems,
  data model — and have they been reviewed with extra care?
- What are the primary failure modes and how does the system
  behave when they occur?
- Can quality be measured? Are there specific, measurable
  thresholds — test coverage, p99 latency, error rate, SLO —
  not just "it works"?
- How would an operator detect and investigate a bad outcome
  without reading source code?
- What changes if load grows 10x or the system's usage pattern
  shifts?
- Can this design be modified without rewriting core
  infrastructure?
- Does the review output tell the team what to do next —
  approve, approve with conditions, or specific changes
  required? A review that ends in observations without a
  clear disposition has not completed its job.