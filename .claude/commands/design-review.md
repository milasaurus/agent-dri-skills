---
description: Review a system design from a staff-level architectural lens anchored in DDIA fundamentals.
---

Invoke the agent-dri-skills:system-design-review skill.

Review the provided system design and produce a staff-level architectural assessment:

1. Read CLAUDE.md and understand the project context and constraints
2. Identify the design scope — the specific system, service, or data flow being reviewed
3. Clarify the top 1-2 system goals: correctness, reliability, latency, scale, or operability
4. Clarify the top 1-2 product goals: what business or user-facing outcomes matter most?
5. Evaluate decomposition:
   - Are concerns separated cleanly or tangled together?
   - Can components be independently tested and deployed?
   - Is business logic separated from execution and infrastructure?
6. Assess fundamentals against the design:
   - Reliability: where does the system fail open vs. fail hard? What happens to in-flight requests during a downstream outage — are they dropped, retried, or queued? Is there a dead letter queue or retry mechanism with backoff?
   - Scalability: what are the actual load numbers — RPS today, projected peak, spike multiplier? Are the read and write paths independently scalable or coupled? Where are the hot spots — specific keys, shards, or nodes that will concentrate load?
   - Maintainability: can an oncall engineer understand what the system is doing at 2am without reading source code? Are components loosely coupled enough that one team can change their piece without coordinating a multi-team deploy?
   - Availability: can the system handle a full DC or region failure? What degrades gracefully vs. fails completely? Is replication synchronous or async — and what are the consistency tradeoffs of that choice?
   - Latency: what is the p99 latency target and is it validated against the design? Are there synchronous calls on the hot path that should be async? Where does caching help and what is the invalidation strategy?
   - Operability: are SLOs defined with specific numbers — availability %, p99 latency ms? Can a bad feature path be disabled without a deploy — decider, feature flag, or config? Is there a runbook for the most likely failure scenarios?
7. Check infrastructure alignment:
   - Is this building on shared infrastructure or creating a parallel system?
   - What are the long-term maintenance implications?
8. Surface tradeoffs and produce actionable feedback:
   - State the biggest risks and key assumptions
   - Recommend concrete changes where fundamentals are violated
   - If the design is sound, state the conditions under which it can be approved

If the design has critical gaps in operability or failure handling, flag these before proceeding to recommendations. Use `system-design-review` to validate the final assessment.
