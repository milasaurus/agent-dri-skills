---
name: experiment-design
description: Design and size a controlled experiment or staged rollout and register its launch gate. Use when a team has a product decision to make before building an experiment.
---

# Experiment design

## Why this skill

A flag can change the product for thousands of people without answering the question that justified the change. Decide what evidence would change the launch decision while the design is still cheap to change.

## When to use

Use before implementing a comparison or choosing a rollout strategy. Reuse metric definitions from an existing [launch measurement plan](../launch-measurement-plan/SKILL.md) when available.

## Process

1. **Trace the product flow.** Follow an eligible unit from entry to assignment, first possible treatment, and the outcome deadline. Ask who shares the treatment. A scheduler that changes a team's shared queue may need team-level assignment even if individual requests generate the events.
2. **Choose what the comparison can answer.** Write the decision, current experience, proposed change, and expected mechanism. For causal lift, specify a concurrent randomized control, stable assignment key, eligibility, arm weights and exclusions before assignment. For a safety ramp, specify stages, stop conditions and rollback. A ramp without a comparable control can establish operational safety but leaves causal lift open.
3. **Check live and scheduled tests.** Compare their dates, audiences, shared state, surfaces and primary outcomes against this design. Name each plausible interaction. Choose exclusion, a shared randomization layer, a joint design, or an explicit reason overlap is acceptable. Record which registry or owners you checked. An inaccessible registry leaves overlap unverified.
4. **Specify a metric the change can move.** Define one primary with direction, numerator, denominator, unit, outcome window and source. Walk one control and one treatment example through the calculation, including a unit with zero outcomes. Check equivalent event semantics across arms. Record guardrail thresholds, sources and who can stop the rollout. Register the smallest effect worth acting on and the decision rule before observing outcomes.
5. **Size against eligible traffic.** Use a baseline and variance from comparable units. For a randomized test, calculate sample per arm with a method suited to the metric, allocation, randomization unit, target detectable effect, power and error rate. Match the calculation to the decision rule. Power to distinguish a four-point gain from zero is different from power to show the gain exceeds four points. Clustered data need cluster-aware sizing. Show inputs, assumptions and achieved precision or detectable effect if traffic is fixed. Convert required samples to days using new unique eligible units per arm per day, then add outcome maturation. If the planned horizon cannot detect a worthwhile effect, change the design or record a different decision. For a safety ramp size stages around the risk and time needed to observe the guardrails.
6. **Fill the tracker and pre-launch gate.** Use the team's existing tracker when available. Otherwise return these two paste-ready rows. A missing decision-critical input gets an owner and a verification step.

| Tracker row | Fields to fill |
| --- | --- |
| Setup | Experiment ID and owner, question, variants and allocation, unit and eligibility, treatment point, exposure trigger and key, deduplication, mapping to the outcome unit, overlap decision, primary and guardrails, sizing inputs and horizon, analysis and stop rules |
| Pre-launch gate | Setup version, PR or configuration, owner and evidence for assignment, treatment delivery, metric coverage and rollback, unresolved items, who can approve exposure and when to read results |

Hand the same versioned setup to [experiment PR check](../experiment-pr-check/SKILL.md). Record the location of any tracker update. If you cannot write there, return the completed rows and label them as drafts.

## Common rationalizations

- “We get a million requests a day.” If assignment is by account, size on eligible accounts. Repeat requests from a few large accounts can make the estimate look much more precise than it is.
- “We can pick the metric after the ramp.” Use exploratory measures to inform the next experiment. Register the metric that will decide this one now.

## Red flags

Eligibility depends on a treatment-only action. The comparison group can receive the treatment through shared state. No one can say what a zero in the primary means.

## Dispositions

Choose **ready to build**, **revise design**, or **rollout for safety only**. Give the deciding reason, owner and next check. Track readiness to expose separately in the pre-launch gate.
