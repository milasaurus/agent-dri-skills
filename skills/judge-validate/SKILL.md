---
name: judge-validate
description: Decide whether a frozen grader can gate a specific decision using independent labels, saved predictions, error costs and repeatability. Use when qualifying a new judge, rules engine or vendor scorer for release or advisory use.
---

# Can this judge make this decision?

## Why this skill

A refund-policy judge agreed with reviewers on 92 of 100 replies in an illustrative test. All eight errors approved an excluded refund. If the test contained only eight excluded refunds, the judge missed every one. Overall agreement hides the failure the gate exists to catch.

## When to use

Use when a team asks where it can trust an existing verdict, including after [tuning](../judge-tune/SKILL.md). Accept saved predictions from any grader. A runnable judge or access to its provider is optional for a retrospective assessment.

## Process

1. **Write the decision before inspecting scores.** Who will act, on which population, and what happens on pass, fail, abstention or error? Record the owner’s maximum false-pass and false-fail rates, minimum coverage, critical slices and uncertainty tolerance as appropriate. If these are missing, report what the evidence supports and what the decision owner must settle. A proposed threshold cannot authorize a release gate.
2. **Freeze the comparison.** Pin the judge, rubric, model or rules version, cutoff, preprocessing and any matcher. Use independent, adjudicated labels from cases held out of tuning. Keep labels and reviewer notes off the prediction path. Record sampling, time window and exclusions. If a scorer supplies numeric values, freeze the mapping from score to action before checking labels. For set-valued outputs validate the [pairing](../judge-matcher-create/SKILL.md) and the downstream case decision.
3. **Join by stable case ID.** Start with the intended case roster. Map saved records to case ID, run ID, output or error, and source/version. Reject duplicate or unknown IDs. Count missing predictions, missing labels, abstentions and execution errors separately. Compare matched cases and show what fraction of the roster they represent. For imported or partial runs, disclose missing coverage and any unknown provenance. If IDs or reference labels cannot be recovered, withhold the trust decision.
4. **Measure the mistakes that reach users.** Show the confusion counts and denominators overall and for each consequential slice. Of truly excluded refunds, how many did the judge approve? Of eligible refunds, how many did it block? Show coverage and the effective errors after applying the actual abstention/fallback policy. Give uncertainty appropriate to independent cases or clusters. For example, even 0 misses in 10 independent excluded refunds leaves a one-sided 95% upper bound near 26%. Repeated predictions of the same ten refunds don’t buy ten more independent labels.
5. **Measure stability.** For a stochastic judge, compare unchanged reruns on identical inputs by ID. Count flips among comparable pairs, changes to or from abstention, and missing or errored pairs. Report differences on the costly slices and compare them with the decision margin. If reruns are unavailable, mark stability unmeasured. For a deterministic scorer, verify replay or identify exactly what could vary upstream.
6. **Return a decision record.** Include the frozen version, intended use, dataset and run IDs, evaluated population, thresholds, counts, uncertainty, rerun evidence, fallback and owner. Link representative disagreements. Keep holdout examples sealed from the tuner if the set will be reused. A proposed fix goes to tuning on fresh development cases.

### Audit saved predictions

For binary decisions, run `python3 scripts/audit.py roster.jsonl saved.jsonl --repeat replay.jsonl` from this skill directory. The [audit helper](scripts/audit.py) reads one object per line. A roster row looks like `{"id":"r1","label":"fail"}`. A saved row looks like `{"id":"r1","verdict":"pass"}` or `{"id":"r1","error":"timeout"}`. Existing categorical runner output works directly. Omit `--repeat` if only one run exists. For a slice, supply its roster and the corresponding predictions. Inspect the false-pass IDs and the per-label counts, then apply the decision contract, fallback and uncertainty limits above. For other output types, retain the native evidence and score with the decision’s agreed rule.

## Common rationalizations

- “The vendor already scored these.” Reuse its predictions. Verify the version, target population, IDs and independent labels before interpreting agreement.
- “One run ranked first.” Measure how often an unchanged judge disagrees with itself before treating a narrow difference as meaningful.

## Red flags

Averages conceal a costly error class. Unscored cases silently disappear. A previously inspected holdout is called fresh. A monitor and a release blocker inherit the same threshold without a decision owner.

## Dispositions

- **Safe to gate** for the named decision and population when the frozen version meets the agreed limits, including coverage, uncertainty and relevant repeatability. State the fallback.
- **Advisory only** when the evidence supports a bounded human-reviewed use and identifies why automated decisions would be unsafe.
- **Insufficient evidence** when missing labels, coverage, limits or stability prevent a defensible call for the intended use. Name the smallest check that would resolve it.
