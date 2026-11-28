---
name: agent-hillclimb
description: Turn a behavior-changing PR into targeted tests, verify an agent run from evidence, or iterate against a baseline. Use when a specific agent behavior needs debugging or improvement and each candidate can be tested on comparable tasks.
---

# Hill-climb an agent change

## Why this skill

A scheduling agent starts saying “I moved both meetings” after a prompt edit. The trace shows two tool calls. The calendar shows only one meeting moved. The next experiment depends on where the second change went missing. Editing the completion message would leave the calendar wrong.

## When to use

Choose the smallest workflow that answers the request. A diff and “what should I test?” calls for a **plan**. A trace and “did it work?” calls for **verification**. A measurable failure, a baseline and a request to improve it call for a **climb**. Each is a useful stopping point.

Use the caller’s existing runner, graders and evidence store. If there is no representative suite, [create one](../create-evals/SKILL.md). For a release decision about an already selected candidate, use [agent change evaluation](../agent-change-eval/SKILL.md). A quick review of a single skill edit may need only a small matched replay. For the corresponding commands in a Luma checkout, see the optional [workflow map](references/luma-workflow.md).

## Process

### Plan a test from a PR

Read the diff and follow it to the path a real request takes. Identify who receives the changed instruction, which flag or permission makes it reachable, and what outcome should change. Choose a case that would fail under the old behavior, a nearby case that should still pass, and any consequential regression the change could introduce. Reuse representative cases and starting state where available.

For each test give the input, setup, baseline and candidate revisions, expected difference, and the trace event or final-state check that would settle it. Identify the smallest runnable command or manual replay supported by the checkout. Mark tests as proposed until exercised. If the runner lacks the tool or identity needed for this path, identify the surface that can test it.

### Verify what happened in one run

Read the saved trace, transcript or export. Establish the actual agent, model, loaded skill revision, tools and starting state wherever the evidence permits. Follow the affected request from instruction to tool arguments, execution result and final artifact or record. Quote or link the event that settles each claim. Separate what the agent said, what it attempted and what the system committed.

Report each required outcome as **observed**, **contradicted**, or **unverified**, with the evidence or missing observation. A queue acknowledgment proves submission. A terminal failure proves failed delivery. A missing final read leaves delivery unknown. One run can locate a failure. Estimating improvement requires a comparison.

### Run a bounded climb

1. **Set the target.** Pin the baseline revision and state the hypothesis, target metric, smallest useful gain, hard requirements and cost or latency limits. Record the case bank, split, scorer, execution surface and round or spend budget. Reuse the same checks that will score the final comparison. Reserve unseen cases by independent task or source. Use isolated state for each replay.
2. **Check the baseline.** For variable behavior, repeat the unchanged baseline on the same cases. Inspect per-case flips, scoring coverage and room to improve. Check that each assigned model actually served, the edit reached its intended role, and the suite exercises that behavior. A saturated metric or an unavailable tool calls for a better test. Unknown variation limits what a small gain can establish.
3. **Try one change.** Read the previous rounds before editing. Choose one change to the prompt, skill, tool handoff or routing rule that could fix the observed cause. Run it alongside the baseline with matched state and settings. Inspect fixes and regressions by case ID, including missing outputs and retries. Use code for exact requirements. Use blind human review or a validated independent judge for qualities the code cannot see. If the grader changes, regrade both versions under the same rule.
4. **Record the decision.** Save the hypothesis, exact change, run IDs, input and grader versions, cases fixed and broken, missing evidence, cost, decision and reason in the project’s experiment log. Keep a development change only if it beats ordinary variation by a useful amount and meets its guardrails. Revert a regression in the experiment arm or retain the last supported candidate. If results are inconclusive, name the observation that would distinguish the explanations. Stop when the target is met, the budget is spent, or another round would repeat an exhausted hypothesis.
5. **Confirm the selected version.** Freeze it and compare it with the baseline on the reserved cases. Run the selected configurations through the durable evaluation path when available, verify completion and record the report and artifact IDs. If only local results exist, label them preliminary. If validation results inform another edit, reserve fresh cases. Hand the evidence to [agent change evaluation](../agent-change-eval/SKILL.md) for a rollout decision.

## Common rationalizations

- “It got cheaper.” Check whether it skipped a required operation. A report missing a mandatory section fails even if the writing is excellent.
- “The candidate won by one case.” Check whether unchanged baseline runs flip that same case and whether a missing result could reverse the call.

## Red flags

The assistant’s completion message is the only evidence. A fallback model silently handled the candidate. A winning edit includes the answer to a test case. Only successful jobs enter the comparison.

## Dispositions

For a plan, return **ready to run** or **blocked on setup** with the test cases. For verification, return the per-outcome findings and evidence. For a climb, return **keep**, **iterate**, **revert**, or **inconclusive**, naming the last supported version and whether independent confirmation ran. A development keep selects a candidate for validation.
