---
name: launch-logging-audit
description: Verify deployed launch telemetry against the intended metric contract. Use after instrumentation ships or when dashboard counts look wrong.
---

# Launch logging audit

## Why this skill

A merged writer, a deployed writer and a queryable event are distinct milestones. Even real landed rows can count the wrong unit.

## When to use

Use with an intended metric definition and a rollout boundary. Read [the handoff](../launch-eng-handoff/SKILL.md) if it contains acceptance examples. See [the runbook](../launch-measurement-run/SKILL.md) for stage order.

## Process

1. Identify the environment, build, flag/exposure cohort and actual deployment window. Check eligible traffic and measured ingestion lag. When there has been no eligible traffic, give the next verification condition and mark it pending.
2. For each signal test firing (first/last seen), grain and duplicates, semantic correctness, attribution coverage across relevant slices, stability over refreshes, and availability at the analytical destination. Exercise failure or retry examples from the handoff. Verify both the numerator and eligible denominator against an independent source at the same grain.
3. Trace at least one discrepancy to the first boundary where IDs diverge. Distinguish a missing writer from delayed ingestion, an unmodeled field, an invalid filter, a version mix or an immature observation window. For example, five surplus events and five missing events can leave totals identical. Compare ID sets and multiplicities.
4. Produce a dated audit row for each metric ID with expected and observed counts, missing/duplicate IDs or rates, sources, window, limitations, owner and next check. Record the earliest defensible coverage date; keep unverifiable earlier history separate. Carry verified and partial rows to [dashboard metrics](../launch-dashboard-metrics/SKILL.md).

## Common rationalizations

“There are production rows, so it works.” Inspect who was eligible and whether every supported path supplied the required keys.

## Red flags

An inner join drops missing units before computing fill. The reader checked a test tenant only. A closed ticket is cited as the production receipt.

## Dispositions

Return **verified**, **partial with coverage**, **failed contract**, or **pending traffic/data** per signal. Name the repair owner and which claims the dashboard can support.
