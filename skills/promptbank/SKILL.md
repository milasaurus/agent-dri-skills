---
name: promptbank
description: Build and version a reusable prompt set from production traffic using a sampling recipe. Use when an evaluation needs real requests from a defined population, or a team wants to refresh an existing bank and understand how its coverage changed.
---

# Build a representative prompt set

## Why this skill

A support team wants to test refund requests. Sampling conversations that issued a refund leaves out denials, abandoned attempts, and requests the agent never recognized. Sample at the point a request becomes eligible, before its outcome is known. A bank represents the population its recipe could actually reach.

## When to use

Use an existing recipe if supplied. Otherwise write one from the evaluation question and record the choices that affect which cases qualify. For a recipe-only request, deliver the recipe and mark the bank unbuilt. For a build request, use the caller’s approved read-only source or export, preparation pipeline and private artifact store. If a validated sampler exists, use its stages and checks.

## Process

1. **Define the draw.** Pin the source snapshot or export version, time window and timezone, target population, sampling unit, eligibility, exclusions, and target count. Specify deduplication, strata and quotas if needed, and a reproducible selection rule. For example, take one eligible support request per ticket, group by entry channel, allocate quotas from eligible ticket counts, then select by a seeded hash of the stable ticket ID with the ID as a tie-breaker. This estimates the mix of tickets. Sampling every turn would give long conversations more weight.
2. **Select before inspecting outcomes.** Read the eligible cohort and record eligible and selected counts per stratum. Include failures, retries and abandoned work when they belong to the target population. If rare or costly failures are deliberately oversampled, label them as a challenge set or retain the sampling weights needed for a population estimate. If the source misses a channel or the sample falls short, record the gap. Widening the recipe creates a different bank.
3. **Prepare replayable inputs.** Retain the request, relevant context available at that point, and authorized references for required starting state. Keep later replies, outcomes and grading labels out of the input. Apply the source’s permitted wording, redaction, retention and reuse rules. For “move it to Friday,” preserve enough preceding context to identify the appointment. If redaction removes that evidence, record the drop or its replay limitation. Keep raw traffic inside its approved boundary.
4. **Verify the prepared bank.** Check unique case IDs, eligibility at the pinned snapshot, context availability, redaction, and counts from selection through preparation. Inspect a small authorized sample across the intended slices. Record drops by reason, including preparation failures, and compare the final mix with the eligible cohort. If development and holdout splits are needed, keep related cases from one conversation, incident or source together. A sample drawn from a failures-only export can support regression testing. Its overall pass rate cannot estimate performance across all traffic.
5. **Freeze and hand off.** Store the prepared inputs and a manifest with the recipe version, snapshot, selection seed or ordering, counts, limitations, permitted use, and a content digest over the prepared bank. Read it back at its versioned reference and verify the count and digest. A refresh gets a new version when the inputs change. Pass the pinned bank to [create-evals](../create-evals/SKILL.md) for success criteria and graders, or to [agent-hillclimb](../agent-hillclimb/SKILL.md) for a matched comparison. Give both versions of the agent the same case IDs. If a smaller subset is needed, record it separately.

## Common rationalizations

- “We asked for 100 and got 83.” Report 83, the missing slices and the reasons. Quietly extending the date window changes the population.
- “The seed is the same.” A seed can repeat a draw from a fixed snapshot. It cannot reconstruct yesterday’s source rows or guarantee identical paraphrases. Pin the prepared artifact.

## Red flags

The query joins only to successful actions. Multiple retries enter as independent tasks. Hidden answers leak into replay context. A saved recipe is reported as a prepared bank.

## Dispositions

Return **ready for the stated population**, **limited to named slices or diagnostic use**, or **unbuilt**. For a completed build, give the bank reference and digest, eligible count, target versus prepared count, drops and coverage gaps. For an unbuilt bank, give the recipe and the missing input or execution step.
