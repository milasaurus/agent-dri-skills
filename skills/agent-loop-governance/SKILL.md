---
name: agent-loop-governance
description: Design or review controls for an agent that can take another action on its own. Use when defining or debugging correction attempts, unattended jobs, delegated work, approvals, budgets, or stop and resume behavior. Routine one-off checks and fixed retries of safe reads usually need no governance review.
---

# Agent loop governance

## Why this skill

A worker times out after submitting an order. Its next turn proposes submitting again. Who can tell whether the first order exists, and what stops a second submission while they check? Design the runtime decision at that boundary. A prompt, a cost chart and an on-call owner can all exist while the retry still goes through.

## When to use

Reach for this skill when the requested decision is **what the agent may do next without asking again**. Use it before giving a system that authority, when expanding it, or when investigating a run that repeated work, exceeded a limit, or continued after cancellation. One worker is enough for any of these problems.

| If the request sounds like this | Use the skill to decide |
| --- | --- |
| “Let the import agent fix rejected rows and try again.” | Which validation errors identify a repairable row? Can it revise just those rows? What ends the run if the same error returns? |
| “Run triage overnight and let the agent notify customers.” | Which actions can run unattended? Who authorizes an outbound message? What happens if a restart finds a send with no receipt? |
| “Migrate these packages in parallel and recover from failed workers.” | Which writes are independent? Who owns shared files, the combined test, and the budget for reruns? What happens to queued workers after stop? |

For “check this export for missing IDs,” run the comparison directly. For a transient read error with a fixed retry policy, use the existing handler. An ambiguous write that might already have taken effect merits a governance review when designing automatic recovery. Route “should we split this into workers?” to [multi-agent design](../multi-agent-design/SKILL.md). Route “did our new repair policy improve future runs?” to [agent change evaluation](../agent-change-eval/SKILL.md).

## Process

1. **Walk one real run.** Start at the trigger. Trace one decision, the tool or worker that carries it out, where the result lands, and what schedules the next turn. Include queues, retries and child runs only where they exist. Identify the first costly or externally visible effect. Ask what durable evidence proves progress and completion. “The agent said done” is insufficient when the resulting state can be checked.
2. **Separate the work from authority over the work.** The inner loop proposes the next step. Name the code that can allow or deny it before dispatch, and the outer-loop owner who sets the objective, allowed actions, success test and intervention policy. Identify who may change each rule and how a run refers to a policy version. A run that proposes a new rule cannot grant itself that rule. Mark controls as observed, proposed, or unknown and cite the evidence available.
3. **Choose review by consequence.** For each consequential action, decide whether it can run unattended, can run with sampled review, requires approval before execution, or should be unavailable. Base that choice on reversibility, delay tolerance, affected people and the strength of the completion check. Bind a required approval to the actor, target, operation and material parameters. A changed amount or recipient needs a fresh decision. Name who can approve and what happens if no one responds.
4. **Put limits where work starts.** Define the relevant limits on attempts, elapsed time, concurrent children, model spend or external effects. Derive values from the caller’s budget and workload. Identify the enforcing component, how it accounts for in-flight work, and what it does when counters or policy are unavailable. Concurrent workers drawing from a shared budget need an atomic reservation or equivalent bounded allocation before dispatch. Include provider retries, child runs and scheduled restarts in the scope that owns the limit. If an external cost cannot be bounded exactly, state the maximum defensible exposure or label the cap as approximate.
5. **Define stop and recovery in terms of effects.** Name what counts as no progress, what can safely retry, and what must pause for reconciliation. For a timeout after a possible write, look up the original operation using a durable identifier before replay. If its outcome cannot be established and replay could duplicate an effect, hold it for an owner. Specify who can stop a run or a group of runs, how new and queued work is denied, when in-flight work can still finish, and what happens to late results. On resume, recheck authority, remaining budget and completed effects at the last durable checkpoint. Record the stop reason and who authorized resumption.
6. **Test the decision boundary.** Pick a failure that crosses two components. If stop and dispatch race, identify the instant a dispatch counts as admitted. Show that a worker claiming work after stop is denied and account for any previously admitted effect that could still land. If two children race for the last allowance, verify at most one authorized dispatch. State the starting state, injected event and observable result that would falsify each guarantee. Use isolated fixtures and label unexecuted checks as proposed.

### How does an agent know what to change on its next attempt?

Use automatic correction when the result can be checked, the failure tells the agent what it could change, and another attempt is authorized and worth its cost. A validator that always prescribes the same mechanical fix can call ordinary code. If a reviewer can only say “make it better,” get a concrete criterion or a human decision before spending another attempt.

For a task that permits revision, have the planner name an observable acceptance check before the first attempt. Give the agent a way to run the check on the actual result and see the specific failure. For example, a report can render correctly while silently omitting records. Compare the exported IDs with the requested set and return the missing IDs to the worker. Keep the acceptance rule and expected set outside the worker's write authority.

Trace three outcomes. A pass ends the task when it covers the whole request. A recoverable failure can authorize a different approach within the remaining allowance. An unavailable check, or repeated attempts with no new evidence, leaves the result unverified and triggers the run's stop or review rule. For a subjective requirement, name the person or independent reviewer whose feedback can settle it.

Fixing this report demonstrates self-correction within one run. If the agent proposes saving a new export strategy for future runs, evaluate that version separately on unseen cases before promotion. For parallel work, pilot a small batch first and verify the combined result for omissions and duplicates even when every child reports success.

### Who owns the result when workers run in parallel?

For a proposed dynamic workflow, identify which units can run independently or which decisions would benefit from independent reviews. Preserve dependencies between steps. For example, during a package migration workers may propose isolated edits, while one coordinator owns the shared lockfile and runs the integration check. Pilot a representative slice and measure integration failures and cost per accepted package before widening the batch. Treat launching workers as a separate action with its own authorization.

## What to deliver

Lead with the autonomy decision for the requested scope. Include a short walkthrough and one control table, using the caller’s actual actions and components. A useful row answers who can say no, when they do it, and what record lets someone verify the outcome.

| Decision point | Rule and scope | Who enforces it, and when | On denial or uncertain outcome | Evidence or drill |
| --- | --- | --- | --- | --- |
| Example: retry a supplier order | At most one order per approved request | Order adapter checks the durable request ID before submission | Hold an ambiguous timeout until the supplier confirms the outcome | Drop the acknowledgment after acceptance. Verify one supplier order and one reconciled local record. |

Close with the operator who reviews stopped runs and the signal that brings them in. Give the outer-loop owner a way to tell whether the objective still fits the work. For example, sample completed cases against the user's original request and review reversals alongside cost per accepted result. Say what evidence would justify removing one approval gate and what finding would restore it. Where the caller supplies no owner or threshold, identify the unresolved decision and its consequence. A lightweight read-only loop may need only a local iteration limit, a completion check and a way to stop it.

## Common rationalizations

- “We alert at the budget limit.” Trace the next dispatch after the alert. If it still runs, record how much more work can start.
- “The parent has already stopped.” Trace a queued child's delivery after cancellation. It may be authorized by a different worker using stale state.

## Red flags

The same agent can edit its own stop conditions. A new run ID resets the allowance for the same job. The only retry evidence is a missing response. A reviewer can see spend or errors but lacks a working stop path.

## Dispositions

Choose **allow** for a specified scope with demonstrated controls, **limit** for a narrower scope whose controls are sufficient, or **hold** when a consequential action has no enforceable boundary. State the deciding evidence, residual exposure and next proof needed. A design-only review can recommend a target disposition while leaving operational readiness unverified.

## Source

The distinction between the working loop and the harness with authority to stop it draws on the [public introduction to Linas Beliūnas’s essay on loop governance](https://linas.substack.com/p/ai-agent-loop-governance).

The [dynamic workflows overview](https://linas.substack.com/p/claude-code-dynamic-workflows-guide) introduces scripted coordination. Anthropic explains when to choose [parallel workflows](https://code.claude.com/docs/en/workflows) and when [iterative feedback improves a result](https://www.anthropic.com/research/building-effective-agents).

For planning and correction from environmental feedback, see [Theo’s talk transcript](https://www.linkedin.com/posts/linasbeliunas_anthropic-research-lead-nailed-it-99-activity-7475264397532225536-m9Cc). For piloting parallel work, see [Anthropic’s guide to building loops](https://claude.com/resources/articles/getting-started-with-loops).
