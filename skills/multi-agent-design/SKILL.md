---
name: multi-agent-design
description: Design or review agent delegation. Use when deciding between a tool, one agent, or child sessions, or when an existing multi-agent workflow needs clearer ownership, handoffs, or recovery.
---

# Design a multi-agent system

## Why this skill

A worker finishes its turn and reports “done.” The write might have landed, the parent might still be waiting for the result, and a collaborator might already have edited the same item. Each is a different fact with a different source of evidence. Design for the sentence the parent can truthfully say to the user.

## When to use

Use for a new architecture, a migration from inline tools to child sessions, or a review of a deployed delegation path. If the topology is fixed, review its contracts and identify the smallest change that would address the observed failure. For retry policy inside one agent, use [loop governance](../agent-loop-governance/SKILL.md). For a change limited to a provider contract, use [model API conformance](../model-api-conformance/SKILL.md).

## Process

### 1. Establish the baseline and the reason to split

Name the user, the requested outcome, hard constraints, and how success is observed. For an existing system, trace one request from admission through execution, durable state, and the user-visible response. Read the relevant code and tests. Label design proposals and unverified behavior separately from the current path.

Start with one agent and its tools. For **each** proposed boundary, describe what breaks in that design and which evidence would change your mind. Compare the cheapest viable alternatives:

| Candidate | When it earns its place |
| --- | --- |
| Direct operation or tool | The caller can express the desired result in one validated operation. Code owns calculations, policy and writes. |
| One agent with a skill or focused context | Instructions, narrower tools, selective reads or compaction address the problem. Different role names alone add no value. |
| One parent with an optional specialist | Some requests require a separately scoped, multi-step read, decide, act and verify loop. The child can keep local working history, recover or pause independently, and return evidence the parent can use. This can pay off even with a single child. |
| Several workers | The work has genuinely separable decisions, bounded parallel reads or disjoint writes. Identify shared resources and implicit decisions. State how callers resolve conflicts and join the results. |

Record the routing rule in user terms. Include a positive request, a similar request the parent should handle directly, and a mixed request. Name what the parent retains during delegation, including prior constraints, ongoing conversation and responsibility for the final answer. Team ownership can justify an interface. Explain why that interface needs an agent at runtime.

### 2. Pick the topology and draw the authority boundary

Choose the simplest topology that fits the dependencies. A pipeline passes one validated result to the next stage. Fan-out/fan-in suits independent work. A hub can serialize contested writes from several workers. Consider a hierarchy only after identifying a coordinator bottleneck, and peer coordination only when the workflow actually needs peers to route requests. For each agent, name its decision, model requirements, tools, maximum useful context, owner of side effects, and evidence returned.

Define the handoff in the caller's native format. For a read-only child it can be a short brief with referenced sources and an output schema. For a child that writes or can outlive the turn, specify:

| Boundary | What to pin down |
| --- | --- |
| Intent and evidence | Original task, confirmed names and constraints, stable references, starting revision, expected result. Pass a bounded working set with a path to inspect more within scope. Preserve decisions when compressing context. Keep reviewer inputs independent of generator self-assessments and hidden labels. |
| Authority | Preserve the initiating actor, tenant and resource scope. Runtime code resolves grants, allowed tools, write footprint, approval scope and expiry. Reading a related object gives the child no write grant. Correlation IDs are for tracing. Identify who can authorize an expansion and where nested approvals appear to the user. Bind approval to the actor, operation and version actually reviewed. |
| Execution | State which judgments the model makes, which calculations are deterministic, and which service validates and commits changes. Identify indirectly affected records such as containers or indexes. Check relevant revisions at commit and define how to handle a changed input. |
| Return contract | Distinguish child lifecycle, observed effects, result delivery to the parent, and task quality. Return useful evidence for committed changes, verified unchanged items, skipped or rejected work, and unknown outcomes. A legitimate no-op needs evidence that the requested state already held. |

For a read-only reviewer, see whether a versioned [judge](../judge-create/SKILL.md) suffices. A stateful reviewer earns the extra boundary when it needs its own observations, interaction or authority.

### 3. Walk the unhappy path

Apply the following to the parts that cross processes, mutate shared state, or can continue after a turn ends. For an in-process read with no side effects, a timeout and explicit error may suffice.

- **Launch and replay.** Allocate a stable child identity per logical delegation. Bind it to parent, task and inputs. On a retry with the same identity and inputs, recover the existing work. Reject a changed brief under that identity. A deduplicated launch still needs a separate idempotency or reconciliation strategy for downstream writes.
- **Concurrent work and uncertain commits.** Describe the action footprint, concurrency checks and atomic unit. After a lost acknowledgement, reconcile against authoritative state before another write. Keep confirmed partial work visible. If undo is supported, reverse only the effects that remain safe to reverse.
- **Stop and resume.** Bound turns, elapsed time, cost and delegation depth where applicable. Enforce shared budgets across the tree. Define how cancellation races with approval and commit. Check that the request and approved version are still active at the commit boundary. Fence new launches and late writes after cancellation or supersession. Decide whether outstanding work is cancelled, detached under an explicit owner, or allowed to finish without publishing to the old request.
- **Join and delivery.** Define which results are required, optional or competing. Use the appropriate join rule: all required results, first acceptable result, or a bounded partial result. Separate the identity of an output revision from the workers producing candidates. A late worker for an old revision cannot overwrite the selected result. Cover normal return, denial, failure, timeout and cancellation with a recoverable terminal delivery path. Record what the parent has consumed so restarts neither lose a finished child's result nor apply it twice.

Use the [worked cases](references/delegation-cases.md) for a shared-state editor, competing workers, and a request that stays single-agent. For a framework migration, list the observable behaviors the old path already provided, including progress, approvals, cancellation, partial success and undo. Compare the new path on the same initial state before switching traffic.

### 4. Decide how to prove the topology is worth keeping

Trace the root request through child, attempt, action, receipt and parent consumption. Distinguish time waiting for approval or delivery from time spent in the model. Count child spend once in the root total, including retries and losing workers. Budget serial steps plus the critical parallel path, queuing and integration. For required stages, combine conditional success probabilities. Five independent required stages at 95% each yield about 77% end-to-end success. Measure correlated failure and retry recovery from real runs.

Compare the candidate with the simplest viable baseline on matched tasks. Check routing in both directions, preservation of unrelated work, parent claims against actual effects, complete-task success, latency and cost. Include a replay, an interrupted handoff and a concurrent change when relevant. Rate usefulness or preference independently from execution integrity. A test that changes the inputs and topology together measures the combined workflow. Use [create evals](../create-evals/SKILL.md) for a missing suite and [agent change evaluation](../agent-change-eval/SKILL.md) for a matched comparison.

### 5. Deliver the decision

Produce an architecture decision record (`multi-agent-design.md` next to the plan when a file is requested). Include task and constraints, current behavior, baseline and rejected alternatives, chosen topology, per-agent inventory, context and authority contracts, a successful and interrupted request traced end to end, failure handling, observability, evaluation and the decision. Identify assumptions, the smallest experiment that could settle each consequential one, and what evidence would reverse the recommendation.

## Common rationalizations

- “The work has three steps, so we need three agents.” Trace the decisions. Three ordered transformations may need one tool.
- “Both workers edit different records.” Check shared containers, indexes and constraints affected by those edits.
- “The child returned success, so the task passed.” Compare its report with durable effects, then check whether those effects satisfy the brief.

## Red flags

The handoff omits a user-confirmed constraint. Child authority comes from free-form context. A parent waits forever when a worker exits without its success callback. A late result can overwrite a newer decision. A model route is chosen without checking the input modality or quality bar.

## Dispositions

Choose **proceed**, **simplify first**, **resolve open questions first**, or **redesign**. State the decisive evidence. For a simplification, name what would justify adding a child. For an open question, name the test and acceptance condition. For a redesign, identify the broken boundary and its replacement.
