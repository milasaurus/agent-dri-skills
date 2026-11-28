---
name: judge-create
description: Choose and build a judge from the task, success criteria, and available evidence. Use when someone asks to create a grader, wants the agent to choose the judge type, or needs one verdict across different kinds of evidence.
---

# Create a judge

## Why this skill

An agent says it rescheduled two meetings. The calendar records can tell you whether both moved. Reading the reply can tell you whether the agent accurately explained a partial failure. Those are two different decisions about the same task.

## When to use

Start here when the caller describes what success means. Choose the judge type yourself. If they name a type, honor that choice and flag any criterion its inputs can't establish. For an existing judge whose agreement needs improvement, follow [judge tuning](../judge-tune/SKILL.md).

## Process

1. **Identify what would settle the question.** Name the unit being graded, the required criteria and the evidence available at grading time. Separate a desired outcome from an agent's claim about it. If a consequential requirement is ambiguous, ask about the requirement. Choose the implementation without asking the caller to pick a judge type.
2. **Run the specialist for each criterion.** Use the table below. Invoke the linked skill if the host supports skill calls. Otherwise read its guide and carry out its process in the current session. Pass the criterion, input contract, example cases, output needed, and any budget or harness the caller provided. Load only the specialists needed and reuse one for criteria of the same type.

   | What settles the decision? | Specialist to run |
   | --- | --- |
   | A set of expected findings, such as all obligations in a brief or defects in an image | [Set matcher](../judge-matcher-create/SKILL.md). Use the relevant extractor below when findings still need to be derived. Pass its frozen list to the matcher. |
   | An exact rule over records, bytes, events, timestamps or numeric tolerances | [Deterministic judge](../deterministic-judge-create/SKILL.md) |
   | The meaning of a reply, source, transcript or explanation | [Text judge](../text-judge-create/SKILL.md) |
   | A visible property or change in an image or video | [Visual judge](../vlm-judge-create/SKILL.md) |
   | The required evidence is missing, or the decision rests on an undefined preference | Identify the missing input or reviewer decision. Mark the affected criterion unassessable and continue with the others. |

3. **Combine results at the level the user cares about.** Decide which criteria are required and which are advisory. Preserve each child verdict and its evidence. When all required criteria must pass, any verified failure settles the overall result as fail. If none failed and a required criterion abstained or errored, report the result as unresolved and keep the reason. Pass only once every required criterion passed. For a ranking or preference task, use the caller's aggregation and tie rule. Keep diagnostics and advisory scores visible. If the harness uses a single verdict field, map unresolved due to missing evidence to its abstention value. Preserve runner errors and the per-criterion record alongside that field.
4. **Return a working judge and say what you verified.** Exercise a pass and a plausible failure. For mixed tasks, include a case where specialists disagree and one with missing evidence. Where independent labels are available, compare the final decision at the unit the caller will consume. Otherwise mark agreement as unmeasured. Show coverage, false passes and false fails. Keep operational errors, abstentions and unlabeled cases distinct. Save the rubric, input and matcher versions, case-level evidence and the configuration that produced the run. State any unexecuted checks and the evidence still needed for release.

For example, a product image must be 1200 × 1200 and preserve the product's original label. Read the dimensions from the file and compare the label visually against the reference. A correct size with a visibly changed label fails. If the size passes and the reference is missing, the overall verdict is unresolved. A size failure remains decisive even when the visual check abstains.

For set-valued criteria, keep individual item IDs, unmatched findings and set metrics in the matcher output. Use the categorical runner below only if the caller defined a case-level threshold and an unresolved policy. For a decision about gating or relying on any existing scorer, use [judge validation](../judge-validate/SKILL.md) with the saved predictions.

### Run the example

From this skill's directory, run the [export judge](examples/export_judge.py) with the bundled categorical runner:

```sh
python3 scripts/run.py examples/cases.jsonl --judge python3 examples/export_judge.py
```

### Run a text-model judge

The [text judge guide](../text-judge-create/SKILL.md) has commands to preview the effective prompt and run the support-policy example. The same [runner](scripts/run.py) accepts any trusted command that reads one input object from stdin and returns a JSON verdict (`pass`, `fail`, or `abstain`) and evidence string. Human labels and case IDs stay on the scoring side. Mixed adapters may also return a `criteria` object keyed by criterion, as below. Map a visual judge's `unclear` to `abstain` for this runner. A child execution failure can be recorded as `{"error":"decoder timed out"}`. The runner preserves it, counts it in `criterion_errors`, and exits nonzero after saving the results.

```json
{"verdict":"fail","evidence":"The width is wrong.","criteria":{"width":{"verdict":"fail","evidence":"Expected 1200 px, got 900."},"label":{"verdict":"abstain","evidence":"Missing reference image."}}}
```

## Common rationalizations

- “The input is an image, so we need vision.” File dimensions are directly readable. Verifying which part a diagram points to requires the pixels.
- “Both graders usually agree.” Two accurate graders can still produce a wrong overall verdict if the caller requires both checks and the harness averages them.

## Red flags

The agent stops after recommending a judge type. A specialist sees the answer key. A persuasive transcript stands in for missing final state. An optional quality score overrides a failed requirement.

## Dispositions

Return **validated for the stated scope**, **candidate ready for calibration**, or **hold for evidence or human review**. Include the selected specialist or specialists, what each checked, and the evidence behind the decision.
