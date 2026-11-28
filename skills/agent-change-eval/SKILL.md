---
name: agent-change-eval
description: Compare an agent change with the current system on representative tasks. Use when deciding whether a change to prompts, models, retrieval, tools, or orchestration improves outcomes enough to release.
---

# Agent change evaluation

## Why this skill

An agent can use fewer calls by giving up sooner. Evaluate the externally observable outcome of an assigned task, including failures and partial delivery. A change to a proxy needs an explanation in terms of the work the user or downstream system receives.

## When to use

Use for one-shot or long-running workflows, interactive or unattended systems, and single agents or delegated tasks. For a PR test plan, trace verification or bounded iterations toward a candidate, use [agent hill-climbing](../agent-hillclimb/SKILL.md). If the capability lacks a reusable task suite, use [create evals](../create-evals/SKILL.md) to build one. For protocol compatibility alone use [model-api-conformance](../model-api-conformance/SKILL.md). If a release needs a broader product measurement plan, continue with [launch-measurement-plan](../launch-measurement-plan/SKILL.md).

## Process

**Choose the size of the evaluation first.** A side-by-side inspection of a few examples can guide exploration. For a localized change, run the check that exercises the affected behavior. For a shared model, prompt or default, include regression cases across the workflows that depend on it. Record which behaviors your chosen scope leaves untested.

Distinguish two decisions. To **protect an existing capability**, freeze the cases and grader. For variable outcomes, rerun the unchanged baseline against itself (an A/A comparison) to estimate how much the score moves without a change. To **establish a new capability**, add cases where success and failure are distinguishable and define the acceptance criterion with the people who use the result. Keep existing regression checks alongside the new test when both decisions matter.

1. **Frame the decision.** Name the baseline, candidate, eligible unit of work, expected mechanism, and failure that would overturn the case for release. If multiple variables change together, attribute the result to that bundle. Define success from the original request and constraints. For an unattended workflow, the consumer might be a service accepting a reconciliation record; a thumbs-up or human session is unnecessary.
2. **Build a matched comparison.** Run each version from equivalent starting state with identical inputs, permissions, tool/data snapshots and budgets except for the intended change. Use isolated state or a recording sink for side effects. Include typical, difficult, unsuccessful and multi-step cases when representative. Keep cases used for tuning separate from held-out validation. Repeat variable cases within budget; repeated runs on one task do not create additional independent tasks.
3. **Grade the resulting work.** Prefer a deterministic oracle for exact contracts, such as record totals or delivery status. For semantic qualities use a calibrated independent grader or blinded domain reviewers with the original brief and resulting evidence. Use separate fields for required conditions, optional preferences, and missing evaluation evidence. Count failed delivery in the assigned population. Report the fraction that could be graded and whether unknowns could change the decision. For example, four verified successes, one wrong result and one ungradable result across six assigned tasks means four verified successes out of six, five gradable cases out of six, and at most five successes.
4. **Compare paired outcomes.** Report eligible counts, baseline and candidate success, paired difference and uncertainty appropriate to the independent unit. Inspect cases the candidate breaks as well as those it fixes. Include tail latency and cost of all attempts where material. Decide the minimum useful improvement and acceptable regressions with the owner before inspecting results. Preserve hard requirements separately from aggregate scores.
5. **Choose the release evidence.** Offline improvement can justify a limited trial. When feasible, assign comparable live units before routing and retain their assignment across retries, shared state or collaborators. Choose outcomes the system can actually observe. Shadow runs can compare outputs and operational costs but cannot measure how people respond to an unseen answer. If randomization is infeasible, explain the limits of replay, shadow or observational evidence. Specify the stop/rollback condition for any proposed trial. Running this evaluation confers no rollout authority.

### When a conversation can branch

Restore both versions to the same decision point, including the state visible then. Give them the same next logged request. Keep later history and reference answers out of the agent and simulator inputs. For example, if the original agent asked “cancel which booking?” and the candidate already canceled one, feeding both the recorded reply “the second one” creates a fictional comparison. Score the first response or let a versioned simulated user react to each version’s actual state. Record where the trajectories diverge. Pair any controlled random draws by case and user decision, then report simulated behavior separately from observed user outcomes.

### Before a grader decides a release

If the change under test is an agent, pin the judge across both arms. Use [judge creation](../judge-create/SKILL.md) to build the grader from the task criteria, or [judge tuning](../judge-tune/SKILL.md) when the grader itself is the candidate. If the grader changes mid-comparison, rescore both saved outputs with the same validated version before attributing a difference to the agent.

For a judgment call, get independent labels from people who use or review the result. Tune the rubric on one set, then check grader agreement on held-out examples, including consequential misses. Record the rubric and grader versions, number of labeled examples, and disagreements that could reverse the decision. If the grader routinely accepts a failure the domain reviewers reject, keep that criterion under human review. In the readout, show whether the paired change is distinguishable from ordinary baseline variation as well as large enough to matter.

## Common rationalizations

“The candidate completed more of its tool calls.” Check whether more eligible tasks reached the intended final state. A different tool path may complete the same task equally well.

## Red flags

Only successful runs enter the denominator. The agent grades its own claim to completion. Changes in case mix or grader version are presented as improvements. A follow-up task is automatically counted as a correction.

## Dispositions

Deliver the comparison recipe, case-level evidence or runnable evaluator when the inputs permit, and a decision: **reject or repair**, **inconclusive** (state the missing evidence), **eligible for a limited trial**, or **supported for release within the tested scope**. Label proposed thresholds and distinguish measured outcomes from predictions.
