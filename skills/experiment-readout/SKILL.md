---
name: experiment-readout
description: Interpret a completed experiment or rollout and publish a decision record with one explicit action. Use at a planned read, a registered stop condition, or the end of a rollout observation window.
---

# Experiment readout

## Why this skill

A dashboard can report a winner even when one arm lost data halfway through. Reconstruct who could receive each experience and which outcomes had time to arrive before interpreting a difference.

## When to use

Use when an owner needs a decision from an experiment or ramp. Start with the registered design, setup review, assignment and delivery history, and the data cutoff. If a source is missing, say which conclusions still depend on it.

## Process

1. **Reconstruct the run.** Identify the registered primary, eligible population, arm definitions, randomization unit, minimum worthwhile effect and stop rule. Mark changes to delivery, eligibility, allocation, logging or metric definitions with timestamps. Identify valid, comparable periods and disclose any retrospective exclusions. Preserve the registered analysis as the headline where valid.
2. **Validate assignment and measurement separately.** Compare unique assignments with expected allocation in each period. Then show per-arm counts through delivery, metric joins and outcome maturity. Investigate sample ratio mismatch at assignment separately from unequal row loss after a join. Keep assigned units with no success in the registered denominator. Distinguish a verified zero from an unobserved outcome.
3. **Estimate the effect at the right unit.** Show control and treatment counts, rates or means, absolute difference with uncertainty, and practical threshold. Use analysis consistent with the randomization unit, outcome window and planned stopping rule. Handle allocation changes within comparable periods. Apply the planned sequential method if interim looks drive the decision. For a ramp without a concurrent comparable control, report observed safety and usage plus the limits on attribution.
4. **Read the decision in plain English.** Say who benefited, by how much, and which plausible effects remain given the interval. Check each guardrail against its registered boundary with maturity and coverage. Identify exploratory slices and missing guardrails. A nonsignificant result with a wide interval can still include worthwhile benefit or harm.
5. **Record one action.** Lead with the selected action, owner, deadline or next read. Include the population and dates, result and uncertainty, guardrails, caveats, and evidence links. Publish to the requested tracker or decision record when authorized and report where it landed. Otherwise return the publish-ready entry. A readout records the decision. Changing traffic or flags requires its own instruction.

## Common rationalizations

- “More treatment users completed the flow.” Compare rates across assigned units and check exposure coverage. A bigger arm can produce more completions at exactly the same success rate.
- “The average looks flat, so it doesn't matter.” Compare the uncertainty interval with the smallest meaningful benefit and harm. Flat estimates alone cannot establish equivalence.

## Red flags

A dashboard silently replaces the registered primary. Recent units have only had one day to complete a seven-day outcome. An attractive subgroup appears only after slicing an inconclusive result.

## Dispositions

Choose exactly one action under the registered decision rule. Give its owner and timing.

| Action | When the evidence supports it |
| --- | --- |
| Continue | The planned run is still valid and immature. Give the next scheduled read and what will mature then. |
| Ship | The decision threshold is met and required guardrails support rollout. Name the rollout owner. |
| Stop | A planned harm or futility boundary is met. Identify the stop owner and affected scope. |
| Iterate | A valid result leaves a specific, testable revision. State the hypothesis for a newly registered test. |
| Invalidate | A design or data failure prevents the intended inference. Name the repair and what must be rerun. |
| Decide on business grounds | The valid result leaves the choice to an explicit cost, safety or product tradeoff. State what the evidence rules out, what remains uncertain and who decides. |
