---
description: Review a system design from a staff-level architectural lens anchored in DDIA fundamentals.
---

Invoke the agent-dri-skills:system-design-review skill.

Review the provided system design and produce a staff-level architectural assessment:

1. Read CLAUDE.md and understand the project context and constraints
2. Identify the design scope — the specific system, service, or data flow being reviewed
3. Clarify the top 1-2 quality goals: correctness, reliability, latency, scale, cost, or operability
4. Evaluate decomposition:
   - Are concerns separated cleanly or tangled together?
   - Can components be independently tested and deployed?
   - Is business logic separated from execution and infrastructure?
5. Assess DDIA fundamentals:
   - Reliability: what failure modes exist and how does the system respond?
   - Scalability: what happens at 10x load? Where are the bottlenecks?
   - Maintainability: can the next engineer understand and modify this safely?
   - Availability: how does the design handle partial failures?
   - Latency: where are the hot paths? Is caching or precomputation appropriate?
   - Operability: can this be debugged and recovered without reading source code?
6. Check infrastructure alignment:
   - Is this building on shared infrastructure or creating a parallel system?
   - What are the long-term maintenance implications?
7. Surface tradeoffs and produce actionable feedback:
   - State the biggest risks and key assumptions
   - Recommend concrete changes where fundamentals are violated
   - If the design is sound, state the conditions under which it can be approved

If the design has critical gaps in operability or failure handling, flag these before proceeding to recommendations. Use `system-design-review` to validate the final assessment.
