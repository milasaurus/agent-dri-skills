---
name: multi-agent-design
description: Gate and design multi-agent systems. Invoke whenever an architecture decision is being made where multi-agent might be the answer — the skill's primary value is forcing a documented single-agent justification before any topology is selected.
trigger:
  - "I need to build an agent that does X, Y, and Z — where X, Y, Z sound like separate roles."
  - "How should I architect this agentic system?"
  - "I want a researcher agent, a writer agent, and a fact-checker agent."
  - "How should I set up the orchestrator and worker agents for this?"
  - "Can you review this multi-agent design?"
  - "I need an ADR for this agentic workflow."
archetypes:
  - architect
  - tech-lead
  - staff-eng
---

## Overview

The hardest calls in multi-agent design happen before any code is written: is
multi-agent actually the right tool, which topology fits the task's dependency
graph, what context does each agent need, and how do failures propagate across
agent boundaries.

Most teams skip this and discover the answers during build — after the
coordination logic is tangled, after handoffs are implicit and non-deterministic,
after a single agent failure takes down the whole workflow. This skill drives
those decisions upfront, producing an architecture decision record (ADR) that
names the topology, agent responsibilities, context contracts, handoff protocol,
and failure mitigations before implementation starts.

**Default to single agent. Document every reason you go multi-agent. That
documentation is the first required artifact.**

## Context Engineering Principles

Context engineering is the #1 job of engineers building AI agents. Even the
most capable model cannot do its job effectively without the context of what
it's being asked to do and what decisions have already been made.

Two principles are load-bearing. Violating either produces fragile systems
regardless of how well the rest of the architecture is designed.

**Principle 1: Share full agent traces, not just individual messages.**

When a subagent receives only its assigned subtask — without the orchestrator's
reasoning, tool calls, and intermediate decisions — it fills the gap with its
own assumptions. Those assumptions will diverge from what the orchestrator
intended. In a multi-turn conversation where the orchestrator made tool calls to
decide how to break down the task, any detail could have consequences on how a
subagent interprets its instructions.

The safe default: every subagent sees the full trace of everything that led to
its task. This is expensive in tokens but the only way to ensure subagents are
reasoning from the same ground truth.

**When the full trace doesn't fit.** Raw orchestrator traces grow long and
eventually exceed a subagent's context window. The options in order of
reliability:

- **Structured summary (preferred):** a compressor model distills the trace into
  key decisions, discoveries, and constraints — not a prose recap of events, but
  a structured record of what was decided and why. The compressor must preserve
  *decisions* ("approach A was ruled out because X; approach B was chosen because
  Y") not just *events* ("three approaches were considered"). A summary that loses
  the reasoning behind a choice is not useful context.
- **Selective injection:** the orchestrator extracts the specific decisions and
  facts each subagent needs and injects them as explicit structured fields. Highest
  fidelity, but requires the orchestrator to know in advance what each subagent
  needs — which is itself a design decision worth making explicit.
- **Raw trace with oldest-first truncation:** pass the full trace but drop the
  oldest entries when it overflows. This is the most dangerous option because the
  oldest entries often contain the original task framing — the most load-bearing
  context.

If using a compressor, the compressor's output format is itself a context contract
that must be versioned and validated like any other inter-agent message.

**Principle 2: Actions carry implicit decisions. Conflicting implicit decisions
produce bad results.**

Every action an agent takes resolves an implicit choice. When two agents run in
parallel without seeing each other's work, they make these choices independently.
The result — even if both agents "succeed" — can be internally inconsistent.
(Example: two parallel agents building components of the same UI independently
choose different visual styles. Neither fails; the combined output is broken.)

The solution is not better prompting. It is either: (a) running agents
sequentially so each sees the full trace of prior work, or (b) accepting that
parallel agents can only be trusted for truly independent tasks with no shared
implicit decisions.

**Implications for architecture decisions:**

Architectures that violate Principle 1 or 2 should be rejected by default.
The simplest architecture that satisfies both is a single-threaded linear agent.
For tasks that genuinely need longer contexts than fit in one window, a
compressor model — one whose sole job is to distill a long action history into
key decisions and events — is more reliable than splitting work across parallel
subagents.

Parallel multi-agent architectures are currently fragile in production because
decision-making ends up too dispersed and context cannot be shared thoroughly
enough between agents. This is not a permanent limitation but a current one.
In 2025, the default for production systems should be sequential unless
parallelism is provably safe (truly independent tasks with no shared state or
shared implicit decisions).

## When to Use

Use this skill whenever an architecture decision is being made where multi-agent
might be the answer — before the decision is made, not after. The skill's
primary value is step 2: defaulting to single agent and forcing written
justification before any topology is chosen. Invoked after someone has already
committed to multi-agent, that gate is bypassed entirely.

Concretely, invoke when:

- a task is described and the roles sound like they could be separate agents
  ("I need something that researches, then writes, then fact-checks"),
- anyone says "orchestrator," "subagents," "worker agents," or "agent topology"
  without a written single-vs-multi-agent decision,
- an existing agentic workflow is being reviewed or critiqued,
- an ADR is being created for any LLM-based workflow.

Do not use when:

- the question is about single-agent tool use ("how do I give an agent access
  to web search") — no topology decision is being made,
- the question is about LLM architecture in general but not about whether to
  use multiple agents,
- the framework (LangGraph, CrewAI, Autogen) has already been chosen and locks
  in the multi-agent topology — the decision is made and this skill can't change
  it; focus on making the design sound within the constraint,
- a system design already exists and the question is whether it is sound
  (use `system-design-review` instead),
- the risk is whether a specific API or model can handle the task at all —
  validate those assumptions with a focused spike before designing around them.

## Process

### 1. State the task and constraints

Before choosing a topology, confirm what the system is actually doing.

- Write the task in one sentence: what does the system do and who does it serve?
- State hard constraints: latency budget (total end-to-end), cost ceiling per
  run, reliability requirement, context window limits per agent. If no
  reliability requirement is stated, default to 95% and document the assumption.
- List available tools and APIs.
- Define what "done" means: is the output a single artifact, a series of
  actions, an ongoing process, or a decision?
- Name any irreversible actions in the workflow. These require human-in-the-loop
  checkpoints regardless of topology.

**If the system is an existing codebase, read it before forming any topology
opinion.** At minimum: the entry point, the agent loop, the tool definitions,
and any existing orchestration logic. Do not propose a topology based on a
description alone — the code is the ground truth. A description says what
someone thinks the system does; the code says what it actually does. These
diverge, and the divergence is usually where the interesting constraints live.

Concretely: use `list_files` or `find` to locate the agent loop and
orchestration layer, read those files, then proceed to step 2. If you cannot
read the codebase, state that explicitly in the ADR as an open question and flag
any topology assumptions that depend on implementation details you haven't
verified.

### 2. Decide: single agent or multi-agent?

**Default to single agent.** Multi-agent adds coordination overhead, latency,
failure surfaces, and debugging complexity. A single agent with the right tools
and the right context is almost always simpler and cheaper.

Before choosing multi-agent for performance reasons, consider the simpler
alternatives: a single-threaded linear agent (full sequential context, most
reliable), or a compressor model that distills a long action history into key
decisions and events (handles long-context tasks without parallel agents). These
satisfy both context engineering principles and should be evaluated before any
parallel architecture.

Choose multi-agent only when one or more of the following is true and you can
state the specific reason explicitly:

- **Provably independent parallelism**: the task has subtasks that share no
  implicit decisions and require no shared state. Each agent could be given
  only its subtask plus the full orchestrator trace and produce a consistent
  result regardless of what other agents do. This bar is high. "They work on
  different things" is not sufficient.
- **Context window is the bottleneck and sequencing fails**: the full task
  requires more information than fits in one context window AND a compressor
  model cannot distill the history without losing critical decisions.
- **Trust or capability isolation**: certain tools must be scoped away from the
  main agent — sandboxed code execution, write access to production systems, or
  actions that require an explicit approval gate. This is a subagent used as a
  capability boundary, not a peer reasoner.
- **Distributed development**: separate teams own separate capabilities and need
  clear boundaries to develop and maintain independently.

**Do not choose multi-agent for specialization or prompt complexity alone.**
A focused system prompt and tool list achieves the same specialization in a
single agent without the coordination cost. "The prompt would be too complex"
and "each agent has a clear role" are restatements of the same argument — they
are not independent reasons to go multi-agent.

Write the decision and the specific reason. A design that goes multi-agent
without documenting why is carrying hidden load-bearing assumptions.

**This gate applies to every proposed agent boundary, not just the initial
multi-agent decision.** A system that justifies multi-agent via trust isolation
and then adds a planner/editor split on top of that justified architecture has
re-introduced the specialization problem inside a valid shell. Each boundary
stands or falls on its own reason — the four valid reasons above apply per
boundary, not once at the system level. After the initial decision is made,
enumerate every proposed agent boundary and run this gate on each one
individually before proceeding to topology selection.

### 3. Select a topology

Four topologies cover the majority of multi-agent use cases. Each maps to a
different task dependency structure. Pick the simplest one that fits.

**Orchestrator / workers (fan-out / fan-in)**

A central orchestrator breaks the task into subtasks, dispatches worker agents,
collects their outputs, and integrates them. Workers operate on their specific
subtask without knowing about the broader workflow or each other.

- Use when: tasks are decomposable into independent parallel work — multiple
  sources searched simultaneously, multiple evaluation dimensions run at once,
  multiple document sections written in parallel.
- Latency profile: `max(worker times) + orchestrator overhead`. Optimizing the
  slowest parallel branch delivers the most improvement.
- Scales well to 5–10 agents. As complexity grows, the orchestrator becomes a
  bottleneck and single point of failure if it must make decisions at every handoff.
- When things go wrong, accountability is centralized — you know where to look.
- When adding new capabilities, introduce a new worker and update the
  orchestrator. Workers are independently testable.

**Pipeline (sequential chain)**

Agent A produces output; Agent B consumes it; Agent C consumes B's output.
Each step depends on the previous step's full output.

- Use when: the task is naturally sequential — research → outline → draft →
  edit, or triage → knowledge retrieval → response generation.
- Simple, predictable, easy to trace. Errors in one step propagate forward;
  bottlenecks are serial.
- Any error early in the chain propagates through the entire process. Validate
  output at each stage before passing it downstream.

**Hub and spoke**

A hub agent maintains shared state — an interaction log, a knowledge base, a
running context object. Spoke agents perform specialized tasks but interact with
the hub rather than with each other. All state flows through the hub.

- Use when: multiple agents need to read or write the same information —
  customer support systems with shared interaction history, knowledge bases
  where agents both retrieve and contribute context, workflows where one agent's
  output becomes another agent's input via a central store.
- Enforce business rules and consistency guarantees at the hub.
- The hub becomes a bottleneck. Design what flows through the hub (shared state,
  consistency-critical information) versus what agents handle independently
  (task execution, local scratch space).

**Peer-to-peer**

Each agent knows the other agents' roles and capabilities and contacts peers
directly without a central coordinator.

- Use when: the optimal workflow depends heavily on intermediate results and
  cannot be planned upfront — research or exploration tasks where agents
  dynamically adapt based on what they find.
- Better fault tolerance: agents can route around failures without a central
  coordinator. But tracing coordination across multiple agents is significantly
  harder than tracing a centralized orchestrator.
- Less common in production systems. Default to orchestrator/workers unless
  dynamic adaptation is a hard requirement.

**When to escalate to hierarchy**

For more than 10 agents or tasks with multiple independent domains, a flat
orchestrator becomes a bottleneck. Organize agents into small teams (3–5 agents)
each with a local coordinator, and have coordinators report to a top-level
orchestrator. Clear escalation paths, local optimization within teams, global
coherence across teams. Add hierarchy only after the flat topology proves
insufficient — not as a default.

Select one topology and write two sentences justifying it over the primary
alternative. If you cannot write that justification, the topology is not yet decided.

**Calculate compound pipeline reliability before committing.** Each agent in a
sequential chain multiplies failure probability. If each agent has reliability
`p` and there are `N` agents in sequence, pipeline reliability is `p^N`:

| Agents | Per-agent reliability | Pipeline reliability |
|--------|----------------------|----------------------|
| 3      | 95%                  | 86%                  |
| 3      | 90%                  | 73%                  |
| 5      | 95%                  | 77%                  |
| 5      | 90%                  | 59%                  |
| 7      | 95%                  | 70%                  |

A 5-agent pipeline where each agent is 90% reliable produces a correct end-to-end
result barely half the time. If the system's reliability requirement is 95%+, either
the pipeline must be shorter, per-agent reliability must be higher, or the design
needs a different topology. Do this math before the ADR is written, not after the
pipeline is built.

For orchestrator/worker topologies, compound reliability applies to the critical
path through the workflow (the longest sequential chain), not across all workers.
Workers that run in parallel do not multiply failure probability — but a single
worker failure still affects the final output unless the orchestrator has an
explicit degradation path.

**Retry adjusts effective reliability.** If each agent has base reliability `p`
and you add one automatic retry on failure, effective per-agent reliability
becomes `1 - (1-p)²`. At 95% base reliability, one retry yields 99.75% effective
reliability — which changes a 5-agent pipeline from 77% to 99% end-to-end. When
retry is in the design, use the adjusted number in the table, not the base
reliability. If retry is prompt-only (the model decides whether to retry) rather
than code-enforced, use the base number — prompt-only retry is not a reliability
guarantee.

### 4. Define agent boundaries

For each agent in the topology, specify:

- **Name** — one short noun phrase (e.g., `ResearchAgent`, `OutlineAgent`,
  `QAAgent`).
- **Single responsibility** — one sentence describing what this agent does and
  what it does not do.
- **Tools** — the specific tools this agent has access to. Apply least-privilege:
  an agent that only reads should not have write tools.
- **Input** — what it receives: format, source (upstream agent, user, external
  API), and maximum expected size.
- **Output** — what it produces: format and schema.
- **Context window check** — estimate the maximum input size. Confirm it fits.
  If it doesn't, this is the topology's first bottleneck.

**Model tier selection.** For each agent, pick the weakest model that reliably
handles the task. Stronger models cost more and add latency; don't use them
where they're not needed. The tiers below are mapped to Anthropic's current
model names (Opus / Sonnet / Haiku) — verify the mapping against current model
cards when invoking this skill, as names and capability boundaries shift between
generations.

- **Opus** — multi-step planning, ambiguous judgment calls, synthesis across many
  inputs with no clear right answer, orchestrators managing complex workflows.
  Use when the agent must decide *what to do*, not just *how to do it*.
- **Sonnet** — solid reasoning over well-defined inputs, most worker agents with
  clear tasks and concrete context. Use when the task requires reasoning but the
  inputs and expected output format are specified.
- **Haiku** — structured translation with explicit schemas: date parsing, format
  conversion, extraction from structured inputs, classification with well-defined
  categories. Rule of thumb: if the task could theoretically be done with a
  template or a regex, it's a Haiku task. If it requires judgment, it isn't.
  Tasks that sound routine but require situational judgment — tone selection,
  professional register, ambiguity resolution — are Sonnet tasks, not Haiku.
  When unsure, treat as Sonnet and validate down empirically; don't assert Haiku
  without testing it at the task.

If you're unsure between tiers, start with Sonnet and downgrade to Haiku after
testing. Upgrading from Haiku to Sonnet mid-build is cheaper than retrofitting
Opus reasoning into a pipeline designed around Haiku latency assumptions.

### 5. Define context contracts

Between each pair of agents that communicate, specify:

- **Format**: structured JSON, a typed schema, free-form text, or a shared
  context object. JSON handoff gives each agent a clear contract and makes them
  independently testable. A shared context object is cleaner for single-process
  pipelines but doesn't travel across process boundaries without serialization.
- **Explicit vs. implicit handoff**: explicit handoff extracts specific fields
  from upstream output and injects them into downstream input. Implicit handoff
  leaves it in the conversation history and relies on the model to pick up
  relevant context. Explicit is deterministic and debuggable; implicit is less
  code but non-deterministic — two runs of the same request can produce
  different downstream inputs. Default to explicit for production systems.
- **Validation**: does the downstream agent validate the upstream output before
  processing? Validation should happen at the contract boundary, not inside the
  downstream agent's reasoning loop.
- **Validation failure behavior**: name explicitly what happens when validation
  fails at runtime. The options are: (a) halt the workflow and surface the error
  to the orchestrator; (b) retry the upstream agent with a correction prompt;
  (c) fall back to a cached or default value; (d) pass a structured error forward
  so the orchestrator can decide. "The downstream agent figures it out" is not
  a defined behavior.
- **Clarification**: can the downstream agent request clarification, or does it
  make its best attempt and pass the result forward?

**Compressor output as a contract.** If a compressor model is used to distill
the orchestrator trace, its output is an inter-agent message like any other.
Define it here: what fields it must contain (decisions made, constraints
discovered, context required by downstream agents), the schema it must conform
to, and what happens if it omits a required field or produces a malformed summary.
A compressor that "summarizes helpfully" without a defined output schema is an
undefined contract at the most load-bearing point in the context chain.

A context contract that says "whatever the upstream produces" is not a contract.
It is a hidden assumption that will surface as a bug.

### 6. Name failure modes and mitigations

For each agent:

- What happens when it fails — error, timeout, hallucination, or partial output?
- What is the retry strategy: fixed retry, exponential backoff, or give up after
  N attempts?
- What is the graceful degradation path: skip this step, use a cached result,
  fall back to a simpler approach, or escalate to human review?
- Where is partial completion recorded so work isn't lost on retry?

For the system as a whole:

- What is the blast radius of a single agent failure? Does the orchestrator
  capture the error and proceed, retry the failed agent, or halt?
- What is the total latency budget? Sum the serial steps; take the max over
  parallel branches. Identify which parallel branch is the slowest and what
  happens if it misses the budget.
- Are there irreversible actions (sending an email, writing to a production
  database, making a financial transaction)? These require an explicit
  human-in-the-loop gate before execution.
- How do errors in one pipeline stage propagate? Validate output before passing
  it downstream; don't rely on a downstream agent to detect and recover from a
  malformed upstream response.

For teams building on durable execution infrastructure (Temporal, Inngest, or
similar): sub-agents map naturally to Activities (discrete, can fail, have side
effects, independently retriable); the orchestrator maps to the Workflow
(coordination and state, not execution). Note this mapping if it applies.

### 7. Plan for observability

Before writing code, name:

- How each agent's input, output, and intermediate steps will be logged.
- **Trace correlation ID**: inject a trace ID at the workflow entry point and
  propagate it as an explicit field through every inter-agent message. Without
  a shared trace ID, you cannot connect telemetry across agent hops, match a
  user complaint to the specific execution that failed, or reconstruct the call
  tree from logs. This is the single highest-leverage observability decision —
  it must be in the design before the first line of code, not retrofitted later.
- How to trace a request across the full agent call tree using the correlation ID
  — not just the final output.
- What monitoring tracks overall workflow health: success rate per agent,
  latency per stage, error rate at inter-agent boundaries.
- What alert fires when a specific agent degrades — not just when the whole
  workflow fails.

A multi-agent system that can't be traced hop-by-hop cannot be debugged in
production.

### 8. Produce the ADR

One document (a `multi-agent-design.md` next to the plan or spec) capturing:

1. **Task statement** — one sentence, plus hard constraints.
2. **Single vs. multi-agent decision** — which and why.
3. **Topology** — which and why, with rejected alternatives named.
4. **Agent inventory** — name, responsibility, model tier, tools, input, output,
   context window check.
5. **Context contracts** — format, handoff type (explicit/implicit), validation
   strategy, for each inter-agent message.
6. **Failure modes** — per agent: failure scenario, retry strategy,
   degradation path.
7. **Observability plan** — tracing, logging, alerting.
8. **Open questions** — anything that cannot be resolved without a spike.
   Specifically: latency budget fit, context window fit, tool reliability at
   scale. Name each open question and what would need to be true for it to be
   resolved before building starts.
9. **Disposition** — see below.

**MVP guidance**: if the design has more than 3 agents, validate that each one
is strictly necessary. A 2–3 agent system with clear roles and structured
handoffs is the right starting point. Add agents when the simpler system proves
insufficient, not before.

## Rationalizations

- "More agents means more capability."
  - Rebuttal: more agents means more coordination overhead, more latency, more
    failure surfaces, and harder debugging. Capability comes from the right tools
    and the right context, not from adding agents. One capable agent beats three
    poorly coordinated ones.

- "Each agent should be small and focused."
  - Rebuttal: granularity is not a virtue in itself. An agent that's too narrow
    requires a complex orchestrator to wire it to others. The right granularity
    minimizes the total complexity of the system — including the coordination
    cost.

- "We can define the context contract later."
  - Rebuttal: context contracts are the load-bearing interfaces of a multi-agent
    system. An undefined contract produces non-deterministic behavior that only
    surfaces in production. Define contracts before writing code.

- "Agents can figure out what to do when they get a bad input."
  - Rebuttal: LLMs are resilient but not reliable. A bad upstream output
    produces a bad downstream output with no error signal. Validate at
    inter-agent boundaries; don't treat agent robustness as a substitute for
    explicit schema validation.

- "We'll use implicit handoff — less code."
  - Rebuttal: implicit handoff is non-deterministic. Two runs of the same
    request can produce different downstream inputs because the model weights
    conversation history differently. Implicit breaks across process boundaries
    and is hard to debug. Use explicit handoff for any workflow you intend to
    ship.

- "Each subagent gets the task description — that's enough context."
  - Rebuttal: the task description is not the context. The context is everything
    the orchestrator has done, decided, and discovered on the way to assigning
    the subtask — the tool calls, the intermediate reasoning, the implicit
    choices. A subagent that only sees the task description resolves all those
    implicit decisions independently, and its resolutions will diverge from the
    orchestrator's intent and from other subagents' resolutions.

- "Parallel agents speed things up — that's worth the tradeoff."
  - Rebuttal: parallel agents are only safe when their tasks are truly
    independent — no shared state, no shared implicit decisions. Most real
    tasks have layers of nuance where one agent's choices constrain another's.
    The speed gain disappears when you have to reconcile inconsistent outputs.
    If parallelism is the goal, first prove the subtasks are genuinely
    independent; then validate that each agent can receive the full orchestrator
    trace and still fit in the context window.

- "Peer-to-peer is more flexible."
  - Rebuttal: flexibility in coordination means loss of traceability. Peer-to-peer
    systems are hard to trace, hard to monitor, and hard to debug in production.
    Use orchestrator/workers unless dynamic adaptation is a hard requirement and
    you can't model it in the orchestrator's planning logic.

- "We should build hierarchy from the start so it can scale."
  - Rebuttal: hierarchy adds coordination overhead and debugging complexity.
    Build the flat orchestrator/worker topology first. Add hierarchy when the
    flat topology proves insufficient — not as a precautionary measure.

- "The orchestrator can handle any worker failure."
  - Rebuttal: only if you've explicitly defined what the orchestrator does on
    failure — retry, degrade, halt, or escalate. An orchestrator that receives
    a malformed worker response and has no defined behavior is not handling the
    failure; it's propagating it.

## Red Flags

- The decision to go multi-agent is not documented with a specific reason.
  "It's complex" is not a reason. Parallel execution, context window limits,
  specialization, or trust isolation are reasons.
- No topology is named. The design is described as "agents collaborating" or
  "agents working together" without specifying the dependency structure.
- An agent's responsibility spans multiple domains or produces outputs of
  different types.
- Context contracts between agents are described as "whatever the upstream
  produces" or left undefined.
- Handoffs are implicit with no plan to make them explicit before production.
- No failure mode is named for any agent.
- An irreversible action exists in the workflow with no human-in-the-loop gate.
- The design has more than 3 agents and no MVP validation path — no plan to
  confirm each agent is strictly necessary before building.
- Peer-to-peer is chosen without specific justification for why orchestrator/
  workers is insufficient.
- Hierarchy is chosen without confirming that a flat orchestrator fails first.
- The observability plan is limited to "log the final output."
- Open questions that affect the topology (latency budget, context window fit,
  model reliability) are not named and not queued for spiking.
- Parallel subagents are used for tasks where one agent's implicit decisions
  constrain another's. The team has not confirmed the subtasks are genuinely
  independent (no shared state, no shared implicit decisions). This is a
  Principle 2 violation.
- Subagents receive only their assigned subtask without the orchestrator's full
  trace of decisions and tool calls. This is a Principle 1 violation.
- The design chose multi-agent for specialization — a focused system prompt and
  tool list achieves the same specialization in a single agent without the
  context-sharing problem.
- A compressor model or sequential single-threaded approach was not evaluated
  before reaching for parallel agents to solve a context-window problem.
- An agent boundary exists whose sole justification is that the agent "owns" a
  domain or role. Domain ownership is specialization by another name. A
  "planner agent," "writer agent," or "editor agent" whose boundary isn't backed
  by one of the four valid reasons must be collapsed into the main reasoning
  agent.
- The ADR proposes a topology for an existing system without evidence that the
  codebase was read. A design based on a verbal description of an existing system
  is not an architecture decision — it's a guess. For existing systems, the code
  is the brief.

## Dispositions

For the architecture decision record, produce one of:

- **Proceed** — the topology is justified, agent boundaries are clean, context
  contracts are defined, failure modes are named, observability is planned, and
  the ADR is complete. Ready to build.
- **Simplify first** — a simpler topology (fewer agents, single-agent) would
  serve the task. State what single capability would need to fail before
  multi-agent is warranted. Build the simpler version; return to this design if
  it proves insufficient.
- **Resolve open questions first** — specific load-bearing assumptions (latency
  budget fit, context window fit, tool reliability at the required call volume)
  cannot be resolved from the design alone. Name each assumption, what would
  need to be true for it to pass, and what a minimal spike to validate it looks like.
- **Redesign** — the current topology has structural problems. Name them
  specifically: agent responsibilities overlap, context contracts are undefined,
  failure modes cascade without mitigation, or the orchestrator is taking on
  work that a worker should own. State the specific changes required and what
  the new topology should look like.

A design review that ends in "something to think about" without one of these
four dispositions has not completed its job.

## Verification

Before closing, the agent should be able to answer:

- Is the decision to use multiple agents documented with a specific reason?
- For each proposed agent boundary: is the reason for that specific boundary
  one of the four valid reasons (provably independent parallelism, context
  window hard limit, trust/capability isolation, distributed team ownership)?
  If the reason is specialization alone — the agent "owns" a domain or role —
  the boundary must be collapsed.
- Is a single topology named, justified over the primary alternative, and
  matched to the task's dependency structure?
- Has compound pipeline reliability been calculated (`p^N`)? Does the result
  meet the system's reliability requirement?
- Does each agent have a one-sentence responsibility, a model tier (with
  justification), a tool list, and defined input and output?
- Is the context contract for each inter-agent message defined — format,
  handoff type (explicit or implicit), validation strategy, and what happens
  when validation fails at runtime?
- If the orchestrator trace exceeds a subagent's context window, is there a
  defined compaction strategy (structured summary, selective injection)?
- Is there a named failure mode and mitigation for each agent?
- Is the total latency modeled: `max(parallel branches) + serial overhead`?
- Are irreversible actions identified with a human-in-the-loop gate?
- Is a trace correlation ID injected at entry and propagated through every
  inter-agent message?
- Is the observability plan specific enough to trace a failed request hop-by-hop?
- Are open questions named with what a minimal spike to validate them looks like?
- Does the ADR exist and contain all required sections?
- What is the disposition — proceed, simplify first, resolve open questions, or
  redesign?
