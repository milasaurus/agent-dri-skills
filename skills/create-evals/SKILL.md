---
name: create-evals
description: Create a reusable evaluation suite for a product or agent capability. Use when turning a brief, user feedback, or recurring failures into representative tasks, observable end states, grading rules, and a repeatable pilot.
---

# Create evals

## Why this skill

A reporting assistant can find every source row and still send the wrong totals to the customer. Retrieval coverage helps explain the failure. An eval that opens the delivered report and checks its totals can catch it.

## When to use

Use this to author or extend a suite that can be run against successive versions of a capability. A PR is optional. Start from a brief, examples of work users need to finish, or a recurring failure in feedback. Use [agent hill-climbing](../agent-hillclimb/SKILL.md) to apply the suite to a behavior-changing PR and iterate on a fix. If the suite already exists and the decision is whether a particular change improved the agent, use [agent change evaluation](../agent-change-eval/SKILL.md). If the tasks and end states are already defined and only the grader is missing, use [judge creation](../judge-create/SKILL.md).

## Process

1. **Pick the decision and the unit.** Who needs the result, what do they do with it, and what would a false pass cost? A file can be correct while the overall job is incomplete. Choose the artifact, job, or interaction that answers the question. Keep three kinds of evidence distinct:

   | Question | Evidence to collect |
   | --- | --- |
   | Can the system complete the task? | A repeatable trial, the resulting work or final state, and checks against the brief. Tool calls, cost and latency help diagnose what happened. |
   | Does the suite cover work that matters? | Representative workflows from practitioners, observed usage and recurring failures. Record which users and workflows are missing. |
   | Did the experience improve for people? | User studies, feedback or an appropriately designed production experiment. A saved file or repeated request may have several explanations. |

2. **Build the case bank.** Look for an existing suite, prompt bank, scorer and run command before adding infrastructure. Sample common workflows across the audiences, input conditions and surfaces where behavior differs. Add consequential failures and plausible near misses, labeling deliberately difficult and aspirational cases separately so their frequency doesn't imply production prevalence. Preserve the relevant context while removing private details. Keep variants from the same source, customer brief or incident in one split. Use development cases for iteration and reserve unseen cases for validation. With little data, call the first set a pilot.
3. **Write a task a user could actually give.** Give each case an ID, provenance, workflow, starting state, user-visible brief, and scoring-only expected end state. Specify required deliverables, counts, literal text, formats, and what must survive an edit **when the task calls for them**. State which choices the agent can make freely. Tie every scored requirement to the brief, the supplied reference, or an applicable product contract. If two sources conflict and no precedence is defined, send that criterion to review. Keep answer keys, later turns and annotator notes out of agent inputs.
4. **Choose how each requirement is scored.** Use a hard pass/fail check for an invariant, full/partial/fail for fulfillment when partial work is useful, and an anchored quality or preference rubric where judgment matters. Apply a criterion only to relevant cases. Include a reason for partial, failed, missing-evidence and inapplicable results. Reuse a suitable grader. For a new one, run [judge creation](../judge-create/SKILL.md) with the criterion and available evidence. Calibrate judgment calls against independent domain reviewers. Keep a proposed quality metric advisory until its agreement and error costs support using it as a gate. A high craft score cannot offset a failed requirement.
5. **Wire and exercise the suite.** Use the caller's harness. Restore each case's starting state in isolation, supply only its public input, run the system, and collect independent evidence of the result. Preserve the evidence and the task, system and grader versions. Test the grading path with a known good result, a convincing near miss, and unavailable evidence. Then run a small baseline on development cases when the runtime is available. Repeat variable trials within budget. Label replayed fixtures, simulated behavior and actual executions explicitly. The [offline ticket-update example](examples/ticket_update.py) exercises the scoring path with five synthetic observations.
6. **Hand over something repeatable.** Deliver the versioned cases, split or pilot status, criteria and scoring hooks, setup/reset instructions, run command and pilot readout. Report full-task success over assigned tasks, alongside partial outcomes, grading coverage, missing evidence and case-level reasons. Distinguish a confirmed failure to deliver from an evaluator that could not inspect delivery. Include required slices and operational diagnostics where they could change the decision. Record what the suite can establish, where human review is needed, and what production evidence would answer any remaining UX question.

## Common rationalizations

- “The model omitted the preferred layout.” Was that layout requested? If several layouts meet the brief, accept them.
- “The agent scored well on average.” Show how many jobs met every mandatory condition and which condition blocked the rest.
- “This complaint came up repeatedly.” Turn it into a regression case. Estimate its prevalence separately.

## Red flags

The only oracle is the agent's claim of success. Test cases share source material with tuning cases. A shared workspace carries state from an earlier trial. An uncalibrated judge blocks a launch. An inapplicable quality criterion counts against the output.

## Dispositions

Choose **ready for repeated measurement**, **pilot only**, or **blocked on evidence or harness**. Name the deciding evidence and the next action. The disposition describes the suite's readiness. Take a release decision through [agent change evaluation](../agent-change-eval/SKILL.md).
