---
name: launch-eng-handoff
description: Convert verified launch logging gaps into implementation-ready engineering asks. Use when a metric is blocked on an event, identity, or persisted field.
---

# Launch eng handoff

## Why this skill

“Track conversion” leaves the hardest design choice to the implementer: which component knows the business action happened, at what grain, and how the value survives downstream.

## When to use

Use with evidence from [instrumentation](../launch-instrumentation-spec/SKILL.md), independently or through [the runbook](../launch-measurement-run/SKILL.md).

## Process

1. Recheck the missing fact against the writer, pipeline and existing open changes. Reuse or amend an existing issue if it covers the same defect. Direct a query-only gap to the analytical owner.
2. Draft an ask per independently shippable defect or related set with one owner. Include blocked metric IDs, evidence and window, exact firing condition, unit, identifiers, payload and destination. Give the required behavior for retries, partial batches or multiple surfaces when they affect counting. Specify ownership across producer, ingestion and reporting.
3. Give an acceptance example with input and expected records: a two-item action where one item fails must still allow each item outcome to be attributed to the original request. Name an independent reconciliation query, rollout dependency, backfill limit and needed-by point. Explain whether the gap blocks launch, blocks measurement, or can wait.
4. Return a draft in the requested tracker format. File or update only if requested, recording the actual issue reference. Preserve open checklist items even if a parent issue closes. Hand the acceptance examples and release reference to [the logging audit](../launch-logging-audit/SKILL.md).

## Common rationalizations

“It is just one field.” If the producer cannot tell which item succeeded, no downstream aggregation can reconstruct it.

## Red flags

A proposed event duplicates an existing signal. The ticket omits the sink or the owner of the transformation. A forward-only field has a deadline after its first cohort.

## Dispositions

Return **draft ready**, **existing work covers it**, **route to data owner**, or **needs evidence** for each ask. Distinguish a drafted ticket from a filed one.
