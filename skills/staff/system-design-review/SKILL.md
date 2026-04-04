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
- a team is building or extending ML/data infrastructure, ranking systems, or recommendation pipelines,
- a reviewer must decide whether the design is sound enough to approve, refine, or require non-trivial changes.

## Process

1. Scope
   - Confirm what this design is trying to accomplish and who it serves.
   - Agree the top 1-2 quality goals for the review: correctness, reliability, latency, scale, cost, or operability.
   - Check whether this is intended to reuse shared infrastructure or create something that will need independent maintenance.

2. Decomposition
   - Check whether concerns are separated cleanly or tangled together.
   - Map the core execution and data flow through the system's components.
   - Verify whether pieces can evolve independently without forcing a single global change.

3. DDIA fundamentals
   - Reliability: what failure modes matter, and how does the system tolerate them?
   - Scalability: will it still work if load grows 10x or the data shape changes?
   - Maintainability: can a future engineer understand and change it safely?
   - Availability: how does it behave when partial dependencies fail?
   - Latency: where are the hot paths and are latency expectations realistic?
   - Operability: can operators detect, diagnose, and recover from bad outcomes?

4. Operability
   - Confirm the design can be debugged and recovered without reading source code.
   - Ask whether the system exposes enough observability to explain expected and failure behavior.
   - If the design is acceptable, make feedback specific, actionable, and scoped to the review context.

## Rationalizations

- "This is a special case; the normal stack is too slow."
  - Rebuttal: special cases become maintenance liabilities. Confirm whether a true shared-infrastructure exception exists and keep the default path as the first option.

- "We can add monitoring later once it’s working."
  - Rebuttal: observability drives correct architecture. If you can’t debug the design now, you can’t safely launch it later.

- "We only need today’s traffic profile."
  - Rebuttal: staff review requires testing against growth. A design that fails at 10x is unsafe even if it works today.

- "This is just a data pipeline, not a system design problem."
  - Rebuttal: data-intensive systems are systems. They still require explicit failure handling, layered architecture, and operability.

- "The component is reusable enough; we can refactor later."
  - Rebuttal: reusable components must be designed up front. If composability is missing, you are already building technical debt.

## Red Flags

- A single service or module owns candidate generation, scoring, and ranking with no clear separation.
- The design relies on hardcoded rules or control flow instead of configuration and reusable components.
- No explicit failure modes, retry/backoff behavior, or degraded-path handling are documented.
- Observability is limited to dashboards, with no tracing or structured diagnostics for runtime decisions.
- The proposal creates duplicate infrastructure instead of reusing shared infrastructure or a common library.
- No evidence the architecture was evaluated against 10x load or meaningful scale assumptions.

## Verification

In a review, the agent should be able to answer these questions clearly:

- what are the system's component boundaries and how does data or control flow through them?
- what are the primary failure modes and how does the system behave when they occur?
- where is business logic configured versus hardcoded?
- how would an operator detect and investigate a bad outcome?
- what changes if load grows 10x or the external shape shifts?
- can this design be modified without rewriting the core infrastructure?
