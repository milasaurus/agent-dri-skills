---
description: Gate and design agentic systems. Use whenever multi-agent might be the answer — the primary value is forcing a documented single-agent justification at step 3 before any topology is selected.
---

Invoke the agent-dri-skills:multi-agent-design skill.

Design the multi-agent system described and produce an ADR with a
proceed / simplify first / resolve open questions / redesign disposition:

1. Read the available project instructions and any project brief to understand what the system
   does, who it serves, and what hard constraints apply (latency
   budget, cost ceiling, context window limits, reliability bar).
   If neither exists, write the task statement and constraints first
   before proceeding — a design without this foundation cannot be
   evaluated.

2. **Apply the context engineering principles before any topology
   decision.**
   - Give execution workers the decisions and evidence needed for their task.
     For an independent outcome judge, pass the brief, rubric and actual output.
     Keep hidden labels and other reviewers' opinions outside its inputs.
   - Principle 2: parallel agents make implicit decisions
     independently. If those decisions can conflict, the combined
     output will be inconsistent regardless of individual agent
     quality. Parallel architecture is only safe for tasks with
     genuinely independent subtasks (no shared state, no shared
     implicit decisions).

3. **Decide: single agent or multi-agent.** Default to single agent.
   Before choosing multi-agent for performance, evaluate:
   - Single-threaded linear agent (full sequential context, simplest).
   - Compressor model (distills long action history, no parallel agents).
   Choose multi-agent only with a specific documented reason:
   provably independent parallelism, context window hard limit,
   trust/capability isolation, or distributed team ownership. Do not
   choose multi-agent for specialization alone.

4. **Select a topology** and justify it in two sentences over the
   primary alternative:
   - Orchestrator/workers: parallel, independent tasks, fan-out/fan-in.
   - Pipeline: sequential, each step consumes the previous contracted output.
   - Hub and spoke: shared state multiple agents must read/write.
   - Peer-to-peer: dynamic workflows where optimal path depends on
     intermediate results (rare in production).
   - Hierarchical: add a coordinator per domain when a measured bottleneck justifies the extra handoff.
   Estimate reliability from the actual completion rule, including required
   parallel outputs, shared failure modes and observed recovery after retries.
   Compare the estimate with measured end-to-end results where available.

5. For each agent: name, single-sentence responsibility, model route verified for its inputs, error tolerance, cost and latency, tools (least-privilege),
   input, output, context window check.

6. Define context contracts between each communicating pair: format
   (JSON schema preferred), explicit vs. implicit handoff (default
   explicit for production), validation strategy, and what happens
   when validation fails at runtime — halt, retry, fallback, or
   structured error forward.

7. Name failure modes per agent: failure scenario, retry strategy,
   degradation path, where partial completions are recorded. Name the
   blast radius of a single agent failure. Gate all irreversible
   actions with a human-in-the-loop checkpoint.

8. Define the observability plan: inject a trace correlation ID at
   the workflow entry point and propagate it through every inter-agent
   message. Add per-agent logging, workflow health metrics, and alerts
   per agent — not just on final output.

9. Produce the ADR with all sections: task statement, single/multi
   decision + reason, topology + reason + compound reliability,
   agent inventory, context contracts, failure modes, observability
   plan, open questions.

10. Produce a disposition: **proceed**, **simplify first** (name the
    simpler alternative), **resolve open questions first** (name the
    assumptions, their gates, and what a minimal spike looks like),
    or **redesign** (name the specific structural problems).

If the decision to go multi-agent is undocumented, stop and document
it before proceeding.
