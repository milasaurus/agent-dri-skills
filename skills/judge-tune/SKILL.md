---
name: judge-tune
description: Tune an existing judge prompt or one inference setting against human-labeled examples. Use when a grader misclassifies cases and a reviewer wants to compare revisions, validate the winner on unseen data, or register a reviewed version.
---

# Tune a judge

## Why this skill

Adding a clause can fix four false rejects and introduce four false accepts. Compare both sets of changed decisions before calling the revision better.

## When to use

Use with a defined judging task and a development set with human labels. This loop targets one categorical label per item, including human-labeled pairwise preferences. For list extraction or numeric scores, agree on a task-appropriate matcher and objective first. For a new visual contract, start with [VLM judge creation](../vlm-judge-create/SKILL.md). To evaluate a change to the agent being judged, use [agent change evaluation](../agent-change-eval/SKILL.md).

## Process

1. **Agree on the experiment.** Confirm the tuning set and separate sealed holdout, label vocabulary, graded field, metric, consequential error classes and budget. Identify who decides whether a revision is worth keeping. In interactive tuning, pause for the reviewer's decision on the set, baseline, each proposed run and the next round. Honor any explicit preauthorized batch limits. Treat a request to draft a prompt as permission to draft it.
2. **Read the development evidence.** Inspect the items, their actual inputs, labels and annotator notes in the approved store. Resolve conflicting interpretations with the reviewer. Keep hidden answers, label frequencies and notes out of the judge input. Pin the set, scorer and media preprocessing. Start with the deployed prompt if present or the shortest prompt that states the task and exact allowed outputs.
3. **Show what will actually run.** Present the effective prompt including any schema suffix, graded field, model/version, decoding settings, representative input layout, item count and cost or call limit. Save the baseline run and the per-item predictions. Estimate ordinary score variation by repeating the unchanged baseline when the judge is stochastic and budget permits. If noise is unknown, qualify small gains.
4. **Propose one falsifiable edit.** Group development misses by observable cause. Inspect correct answers too, especially ones whose explanations cite irrelevant evidence. Distinguish a bad instruction from an unreadable input, parse failure, ambiguous label or invalid matcher. Show the smallest prompt diff, the error pattern it should fix, and currently correct cases it could break. Keep case IDs in the experiment log and case-specific clues out of the prompt. A model, resolution or temperature change is a separate experiment.
5. **Compare and decide with the reviewer.** Evaluate the same items and report paired fixes and new regressions, including class-specific false accepts and rejects, coverage, errors and cost. For categorical labels, report accuracy and Cohen's kappa when defined. Kappa is undefined when expected agreement equals one. Treat a small change within rerun variation as inconclusive. Maintain the best supported configuration under the agreed metric and harm limits. Branch the next trial from it and record rejected edits and reasons. Stop on budget exhaustion, lack of a testable hypothesis, or the reviewer's decision.
6. **Validate once the candidate is frozen.** Run the untouched holdout through the authorized evaluator. During tuning, keep its inputs, labels, notes and item-level errors inaccessible to the tuner. Use aggregate held-out results and counts for the promotion decision. If holdout feedback guides another edit, treat that set as development evidence and obtain fresh validation. When only development results exist, label the gain preliminary.
7. **Hand off the decision.** Record dataset versions, baseline and selected run IDs, prompt/config diff, development versus held-out results, uncertainty, regressions, and decision owner. Use references to protected evidence in the tuning log. Register an immutable copy of the exact saved configuration only on authorized promotion. A registry entry alone establishes no release threshold.

## Common rationalizations

- “The explanation sounds better.” Follow the changed labels through to human agreement. A better explanation may reveal a rubric defect without improving agreement.
- “Let's try the runner-up on the holdout too.” Comparing revisions on that set turns it into a selection set.

## Red flags

The tuner sees validation examples before freezing the candidate. The candidate wins by abstaining on hard cases. A new prompt and a new model are credited independently after changing together.

## Dispositions

Choose **keep baseline**, **try the proposed revision**, **inconclusive**, or **promote for the validated scope**. State the evidence and the next owner action. Separate the recommendation from any registration or rollout actually performed.
