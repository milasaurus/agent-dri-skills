---
name: judge-matcher-create
description: Build a one-to-one scorer for set-valued findings and compute precision and recall from matched items. Use when an agent must find every requirement, action item, discrepancy or visual defect, including paraphrases and duplicates.
---

# Did the agent find every required item?

## Why this skill

Three expected actions and three predictions can still mean one action was missed. If two predictions describe the same action, only one can claim it. Return the pairs, the extra prediction and the omitted action so the reviewer can see the mistake.

## When to use

Use for unordered collections of independently identifiable items. The extractor may read text, pixels or structured records. A list of steps whose order matters also needs a sequence check. A scalar count alone cannot identify which items match.

## Process

1. **Define one item.** Agree on fields that identify it and differences that change its meaning. For meeting actions, “Mina sends the contract” and “Mina sends the invoice” share an owner but differ in deliverable. Decide whether dates, location or severity matter. Split compound items under the same documented rule on both sides. Review true duplicates in the reference annotations. Preserve predicted duplicates with separate IDs.
2. **Separate extraction from grading.** The extractor sees the task and source evidence only. Freeze its output before loading the human reference set. The matcher receives the two lists, the equivalence rule and any evidence needed to apply it. Assign IDs local to each case. Treat a missing reference list, an invalid list or a failed extractor as a distinct unresolved outcome. An explicitly empty list is valid.
3. **Decide which pairs qualify.** Prefer stable keys or explicit deterministic rules when they settle identity. For paraphrases or visual ambiguity, build a separate semantic matcher that proposes eligible ID pairs with evidence. Pin its model, prompt, threshold and preprocessing. Calibrate on independently labeled positive and hard-negative pairs, including reversed roles, nearby defects, duplicates and ambiguous alternatives. If multiple models are available, consider an independent family to reduce shared phrasing bias. Send unresolved pairings for review when they could change the decision.
4. **Assign and score in code.** Build a runnable adapter in the target harness. Use [the bundled scorer](scripts/score.py) for unweighted eligible pairs or reuse an equivalent implementation. Maximize the number of valid one-to-one matches. A greedy first match can leave a valid item unmatched. The helper uses input order to resolve equivalent assignments. If match quality or severity determines priority, specify and implement the secondary objective and test it. Reject unknown IDs and cross-case pairs. Save the selected pairs, their evidence, unmatched IDs, and any extra predictions that also qualified for an already matched reference.
5. **Report with denominators.** Each selected pair is one true positive. Each extra prediction is one false positive, including an extra paraphrase. Each missed reference is one false negative. Report precision, recall and F1 alongside counts. Declare the empty-case and aggregation conventions. The helper emits null for a zero denominator and marks agreement on two empty sets explicitly. For a suite, pooling counts weights larger sets more heavily. An average across cases gives each scored case equal weight. State how unresolved and empty cases enter the release decision.
6. **Exercise the matcher before handing it off.** Run a duplicate plus an omission, a paraphrase, a similar but wrong item, two empty lists, one empty side and a case where one prediction has two eligible matches. Inspect the chosen pairs as well as the score. Validate a model-based matcher's own decisions on held-out annotated pairs and end-to-end assignments using [judge validation](../judge-validate/SKILL.md). Without that evidence, label its scores provisional.

### Try the duplicate case

From the skill directory, run `python3 scripts/score.py examples/meeting.json`. The two contract predictions compete for one reference. The fixture produces two matches, one extra prediction and one missed action. Both precision and recall are 2/3. The fixture supplies approved pairs. For real inputs, implement the eligibility step inferred from the caller’s task.

## Common rationalizations

- “Just deduplicate the output.” That hides repeated findings. Keep an occurrence ID for each prediction.
- “The matcher can tell us the F1.” Have it identify defensible pairs. Code owns the assignment and arithmetic.

## Red flags

The extracting judge sees the key. Two predictions earn credit for the same finding. Empty output from a failed tool scores as a correct empty set. A model-based matcher grades itself.

## Dispositions

Return **ready for the stated matching contract**, **candidate pending matcher validation**, or **hold for unresolved equivalence or evidence**. Deliver the runnable matcher or adapter, its versioned rule, case-level pairs, scores and evidence behind the call.
