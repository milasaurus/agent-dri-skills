---
name: launch-instrumentation-spec
description: Map launch metrics to emitted events and warehouse records. Use when proving whether a measurement gap needs logging, a data model change, or a corrected query.
---

# Launch instrumentation spec

## Why this skill

Zero matches can mean no eligible traffic, a stale mirror, the wrong join, or an absent writer. Each calls for a different engineering response.

## When to use

Use with metric definitions or the output of [the plan](../launch-measurement-plan/SKILL.md). The [runbook](../launch-measurement-run/SKILL.md) coordinates the full chain.

## Process

1. Establish whether eligible traffic exists in the environment and window, independently of the signal under test. Before launch, inspect the writer and exercise a comparable shipped path if available. Label proxy counts with the proxy population and defer launch-specific coverage.
2. Trace each metric from its certified analytical model to source records and the producing code. Record grain, originating surface, stable unit and event IDs, payload discriminator, event time, ingestion time and settlement rules. Read the producer to distinguish intent, render, completion and acknowledgment. A present column can have the wrong meaning or contain a constant.
3. Probe on a common window where both sides existed. Count distinct eligible IDs before and after joins; report unmatched IDs, duplicated IDs, null keys and fill by relevant surface or version. Show how retries and one-to-many joins affect the numerator. For a funnel, check later-step IDs belong to the earlier eligible set at the declared grain.
4. Return one row per metric ID: source, join and filters, window, evidence, coverage, status, next owner. Use **verified**, **partial**, **query/pipeline fix**, **writer gap**, **outside definition**, or **unverified**. For a true writer gap specify the single fact that must be distinguishable, the component that knows it, where it must land, which metrics it blocks and whether old data is recoverable.
5. Pass confirmed asks to [engineering handoff](../launch-eng-handoff/SKILL.md). Route an existing raw fact missing from a reporting table to the data owner. Reconcile changed definitions back into the plan.

## Common rationalizations

“The event name matches the metric.” A card-render event may fire again on remount. Compare distinct business actions with raw events and verify the firing point.

## Red flags

A proxy sample is presented as feature traffic. A joined total reconciles only because duplicated and missing IDs cancel out. No access is mistaken for a writer gap.

## Dispositions

Return a per-metric status plus **ready for audit**, **engineering or pipeline work needed**, or **waiting for traffic/access**. Attach the query or reproducible probe.
