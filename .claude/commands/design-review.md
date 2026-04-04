---
description: Review a system design from a staff-level architectural lens.
---

Invoke the agent-dri-skills:system-design-review skill.

Review the provided system design and produce a staff-level architectural assessment:

1. Read CLAUDE.md and understand the project context and constraints
2. Identify the design scope — the specific system, service, or data flow being reviewed
3. Confirm the business goal and user-facing impact
   - What behavior changes for the end user?
   - What is the business value — cost reduction, revenue,
     reliability, velocity, or new capability?
   - If the business value isn't stated, ask for it before
     proceeding. A design without a clear goal cannot be
     evaluated against the right quality bar.
4. Evaluate decomposition and leverage points
   - Are concerns separated cleanly or tangled together?
   - Identify the interfaces, stateful systems, and data model
     — scrutinize these hardest. They are the highest-leverage
     points and the most expensive to fix later.
   - Can components evolve independently without a global change?
5. Assess fundamentals against the design
   - Data model: primary key structure, consistency guarantees
     across multiple stores, TTL and retention strategy.
   - Reliability: fail open vs. fail hard, retry behavior,
     hot key concentration, read/write path coupling.
   - Scalability: actual RPS numbers, 10x load behavior,
     N+1 read patterns, caching and invalidation strategy.
   - Rollout: staged plan, feature flags, success metric,
     rollback trigger.
   - Observability: SLOs with specific numbers, lifecycle
     trace, alerts for likely failure scenarios.
   - Migration: backfill or dual-read strategy, rollback
     safety, downstream consumers of old format.
6. Produce a clear disposition
   - Approve, approve with conditions, or list specific
     changes required.
   - Make feedback actionable and scoped — directional,
     not prescriptive.
   - Do not block on perfection. If the design is sound,
     say so and note what to revisit post-launch.

If the business value or user-facing impact is missing, flag this before any other feedback. Use `system-design-review` to validate the final assessment.
