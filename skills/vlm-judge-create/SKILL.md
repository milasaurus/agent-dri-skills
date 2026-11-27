---
name: vlm-judge-create
description: Build and validate a vision-language model (VLM) judge for images, video, or visual comparisons. Use when turning a human visual decision into a repeatable grader with an input contract, labeled examples, and a measured scope of use.
---

# Create a VLM judge

## Why this skill

A judge for assembly instructions might approve a diagram because the part is present even though the arrow points to the wrong socket. The useful question is whether the grader catches the mistakes that would make a reviewer reject the work.

## When to use

Use to create a new visual grader or bring an existing visual rubric into a caller's evaluation harness. For an exact property such as image dimensions, implement a deterministic check. For a judge that already has a contract and needs better agreement, use [judge tuning](../judge-tune/SKILL.md).

## Process

1. **Define the decision.** Identify the reviewer, downstream use, unit, required evidence, and cost of a false accept or false reject. Pick the output shape: a single label, a preference between candidates, or a list of findings. Define tie, insufficient evidence, and borderline cases where they make sense. Ask a domain reviewer to settle ambiguous rubric terms using examples.
2. **Build the labeled set.** Include clear passes, clear failures, near misses and unusable inputs from the intended domain. Record human labels and optional notes separately from the material sent to the model. Keep variants of the same source scene, document or video together when splitting development from held-out validation. Record disagreement and label provenance. If labels are unavailable, deliver a runnable candidate and labeling plan with alignment marked unmeasured.
3. **Specify exactly what the model sees.** Order and label the instruction, reference media and candidate media. Pin resizing, cropping, orientation, frame sampling and timestamps when relevant. Inspect a rendered sample at the resolution the model receives. Test a missing attachment and a detail lost in preprocessing. For a preference judge, swap candidate order and map the answer back to the item identity. A temporal claim needs footage that covers the event.
4. **Build the candidate in the available harness.** Return the effective prompt, model and settings, media transform, response schema, graded field, and matching rule in the caller's format. Wire or supply a minimal runner that assembles the inputs, calls the model, parses its response and saves a per-item result. Reuse existing adapters. If no runtime was supplied, provide a concrete config and sample invocation or interface, and identify what remains unexecuted.

   For the assembly example, label the two images `reference` and `candidate`. A minimal prompt is “Does the arrow in the candidate point to the socket marked in the reference? Return a verdict and the visible detail that supports it.” The parsed result might be `{"verdict":"fail","evidence":"The arrow ends at the left socket; the reference marks the right."}`. Grade only `verdict` against the label set `pass | fail | unclear`. A decode failure produces a runner error. A readable but ambiguous diagram can produce `unclear`.

5. **Measure the judge before using its scores.** Smoke-test the full media-to-score path, then compare against independent human labels. For categorical judgments show the confusion matrix, accuracy, per-class errors, and chance-corrected agreement (Cohen's kappa) where defined. For extracted lists, specify one-to-one matching and report precision, recall and F1. Validate a learned matcher separately. Keep missing labels, model abstentions, malformed outputs and provider failures visible with their denominators. Report labeled and scorable coverage. State the agreed treatment of errors and abstentions before comparing scores.
6. **Deliver four identifiable artifacts.** Provide the labeled set version or its specification, candidate config, saved run record with per-item evidence, and reusable judge version if registered. A run ID identifies one experiment. A judge version identifies the configuration downstream callers will reuse. Register a reviewed version only when requested. Record its intended scope, held-out evidence, limitations and owner. Keep row-level media and labels in the caller's approved store.

When the caller consumes one verdict per document, screen or clip but the runner grades multiple pages, crops or frames, specify how those observations combine. Score the final verdict at the unit the caller uses.

## Common rationalizations

- “The image URL is in the prompt.” Inspect the actual request and rendered pixels. A reference can be cropped, reordered, expired, or delivered as text.
- “A 95% pass rate is good.” A judge returning the majority label can have high accuracy while missing every important defect.

## Red flags

The prompt includes annotator notes or answer-bearing filenames. Related examples cross the development split. The same judge chooses a winner when A and B are swapped purely because it favors the first slot.

## Dispositions

Choose **candidate ready for calibration**, **validated for the stated scope**, or **hold for evidence or repair**. Name the deciding result, what the caller can use today and which outputs still need human review.
