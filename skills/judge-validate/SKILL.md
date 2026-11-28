---
name: judge-validate
description: Decide whether a frozen grader can gate a specific decision using independent labels, saved predictions, error costs and repeatability. Use when qualifying a new judge, rules engine or vendor scorer for release or advisory use.
---

# What would happen if this judge made the decision on its own?

## Why this skill

A refund-policy judge agreed with reviewers on 92 of 100 replies in an illustrative test. All eight errors approved an excluded refund. If the test contained only eight excluded refunds, the judge missed every one. Overall agreement hides the failure the gate exists to catch.

## When to use

Start here when a team has a judge and needs to decide whether people can rely on it. Run this review before choosing a prompt edit, or on a frozen candidate after [tuning](../judge-tune/SKILL.md). Accept saved predictions from any grader. A runnable judge or access to its provider is optional for a retrospective assessment.

## Process

1. **Write the decision before inspecting scores.** Who will act, on which population, and what happens on pass, fail, abstention or error? Record the owner’s maximum false-pass and false-fail rates, minimum coverage, critical slices and uncertainty tolerance as appropriate. If these are missing, report what the evidence supports and what the decision owner must settle. A proposed threshold cannot authorize a release gate.
2. **Freeze the comparison.** Pin the judge, rubric, model or rules version, cutoff, preprocessing and any matcher. Use independent, adjudicated labels from cases held out of tuning. Keep labels and reviewer notes off the prediction path. Record sampling, time window and exclusions. If a scorer supplies numeric values, freeze the mapping from score to action before checking labels. For set-valued outputs validate the [pairing](../judge-matcher-create/SKILL.md) and the downstream case decision.
3. **Join by stable case ID.** Start with the intended case roster. Map saved records to case ID, run ID, output or error, and source/version. Reject duplicate or unknown IDs. Count missing predictions, missing labels, abstentions and execution errors separately. Compare matched cases and show what fraction of the roster they represent. For imported or partial runs, disclose missing coverage and any unknown provenance. If IDs or reference labels cannot be recovered, withhold the trust decision.
4. **Replay the proposed decision on the labeled cases.** If pass ships and fail sends work back, count how many reviewer-approved items would go to rework and how many reviewer-rejected items would ship. Give each count over its reference class, then show agreements over the full roster, decision coverage and the number routed to people. Keep technical errors separate. Describe these as consequences on this sample. A production forecast needs a representative sample or defensible weighting. Give uncertainty appropriate to independent cases or clusters. For example, even 0 misses in 10 independent excluded refunds leaves a one-sided 95% upper bound near 26%. Repeated predictions of the same ten refunds don’t buy ten more independent labels.
5. **Read the disagreements in both directions.** Choose a consequential false pass and false fail when each exists. Show the original input or access-controlled reference, the human label and explanation, and the judge verdict and explanation side by side. State which observation decided each verdict and what would happen to the user. Identify which direction matters more for this decision and why. If a direction has zero cases, say so. Mark unavailable evidence explicitly. The examples explain a failure mode. The full counts give its frequency.
6. **Inspect the instructions and labels before tuning.** Read the exact prompt or rules served on this run, including appended text. Which criterion owns each issue? Did drafting commentary reach the judge? Does the reference explanation cite an excluded criterion, and did it actually decide the label? Flag discrepancies for adjudication while preserving the original label and score. Surface the current rule for genuinely ambiguous evidence versus evidence the judge cannot inspect. Ask the decision owner whether each should pass, abstain or go to a person. Keep an observed pass scored as a pass even when its rationale expresses doubt. If uncertainty was never logged, its frequency is unknown.
7. **Measure stability.** For a stochastic judge, compare unchanged reruns on identical inputs by ID. Count flips among comparable pairs, changes to or from abstention, and missing or errored pairs. Report differences on the costly slices and compare them with the decision margin. If reruns are unavailable, mark stability unmeasured. For a deterministic scorer, verify replay or identify exactly what could vary upstream.
8. **Make one call.** Lead with one disposition below, the decision it applies to and who has final say. Give the replay counts, the reviewed cases and the uncertainty policy behind the call. Record version, run IDs, population, thresholds and rerun evidence. Hand policy questions to the decision owner and disputed labels to the reviewer. Send [judge tuning](../judge-tune/SKILL.md) a testable pattern only when the rubric is clear. For example, can the judge distinguish keeping both elements of an ad from keeping their visual hierarchy? Use fresh development cases for that test and keep reusable holdout evidence with the validator.

### Audit saved predictions

For binary decisions, run `python3 scripts/audit.py roster.jsonl saved.jsonl --repeat replay.jsonl` from this skill directory. The [audit helper](scripts/audit.py) reads one object per line. A roster row looks like `{"id":"r1","label":"fail"}`. A saved row looks like `{"id":"r1","verdict":"pass"}` or `{"id":"r1","error":"timeout"}`. Existing categorical runner output works directly. Omit `--repeat` if only one run exists. For a slice, supply its roster and the corresponding predictions. Use the false-pass and false-fail ID lists to select examples. Add `--review-cases ID [ID ...]` to include their input, verdicts and explanations side by side in the JSON. Supply `input_ref` or `input` and `label_explanation` on roster rows, and `evidence` on prediction rows. An input reference takes precedence over inline content. Missing fields appear as null. Keep case-level output with readers authorized for those inputs. For other output types, retain the native evidence and score with the decision’s agreed rule.

## Common rationalizations

- “The vendor already scored these.” Reuse its predictions. Verify the version, target population, IDs and independent labels before interpreting agreement.
- “One run ranked first.” Measure how often an unchanged judge disagrees with itself before treating a narrow difference as meaningful.

## Red flags

Averages conceal a costly error class. Unscored cases silently disappear. A previously inspected holdout is called fresh. A monitor and a release blocker inherit the same threshold without a decision owner.

## Dispositions

- **Safe to gate** for the named decision and population when the frozen version meets the agreed limits, including coverage, uncertainty and relevant repeatability. State the fallback.
- **Advisory only** when the evidence supports a bounded human-reviewed use and identifies why automated decisions would be unsafe.
- **Insufficient evidence** when missing labels, coverage, limits or stability prevent a defensible call for the intended use. Name the smallest check that would resolve it.
