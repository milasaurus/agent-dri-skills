---
name: launch-measurement-plan
description: Define the metric tree and decision rules for a product launch. Use when turning a brief or release goal into a measurable plan.
---

# Launch measurement plan

## Why this skill

A feature can generate more clicks by adding an extra step. The primary outcome should tell the owner whether the user finished the intended work.

## When to use

Use for a full measurement plan or a metrics-only pass. Start a multi-stage run with [the runbook](../launch-measurement-run/SKILL.md).

## Process

1. Trace one user from eligibility through discovery, attempt, completion and useful outcome. Identify where entry points converge, who can act on shared objects, and what existing workflow the feature might replace. Verify the flow against the build or design supplied. Capture disagreements with the brief.
2. Name the decision and the headline outcome. Add primary measures that explain the journey, secondary diagnostics that can change a decision, and guardrails such as failure, latency, spend or harm. Check substitution against the existing workflow as well as total use across both. For a metrics-only request, deliver these definitions without expanding into tickets or dashboard design.
3. For each metric give a stable ID, question, unit (person, team, request or output), numerator, denominator, qualifying event, exclusions, clock start, outcome window, splits and interpretation. Separate repeat use from first adoption. Include failed eligible attempts when measuring the chance of reaching an outcome. For time among completers, also show the share reaching completion.
4. Label each claim descriptive, comparative or causal. A staged ramp, opt-in cohort or before/after trend can describe adoption; attributing lift needs a credible counterfactual. If effect estimation matters, identify the comparison, assignment unit, guardrails and meaningful change to settle before exposure. Leave unknown thresholds as open decisions with an owner.
5. Return the metric tree and one row per definition with its evidence status. Hand stable IDs to [instrumentation](../launch-instrumentation-spec/SKILL.md).

## Common rationalizations

“Adopters convert more, so launch caused lift.” Show the selection bias and restate the claim at the strength of the evidence.

## Red flags

Calendar cohorts have different time to return. A team-level numerator uses a user denominator. The funnel ends at a button click although users still need to receive an output.

## Dispositions

Mark each claim **ready to instrument**, **descriptive only**, or **needs a definition or comparison**. State which decision remains possible.
