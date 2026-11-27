---
name: launch-dashboard-metrics
description: Build or specify decision-ready launch dashboard panels from audited signals. Use when adding a launch view, migrating a metric source, or validating a published dashboard.
---

# Launch dashboard metrics

## Why this skill

A chart can render while its filters apply to only half the page, a source change silently changes its denominator, or an immature cohort appears to have zero returns.

## When to use

Use [audit results](../launch-logging-audit/SKILL.md) and metric definitions. For an entire launch start with [the runbook](../launch-measurement-run/SKILL.md).

## Process

1. Lead with the launch decision and headline outcome, then the user journey, diagnostics and guardrails. For every panel identify the metric ID, source, unit, population, numerator/denominator, time basis, coverage start, last refresh and treatment of missing evidence. Preserve unknown, unavailable, provisional and observed zero as distinct states.
2. Build the view in the requested tool. Where access is limited, deliver an executable query or build specification with parameters and expected shapes. Make date, audience and relevant surface filters consistent across cards, tables and trends. Expose the denominator for segmented rates. For repeat use, exclude immature cohorts from the rate and display their counts separately.
3. For an existing panel compare old and new sources over a common settled window. Record old/new counts by step, differences in business IDs and a cause for each material delta. Label intentional definition breaks. Preserve unrelated panels and filters when changing a single launch view.
4. Verify the rendered artifact against independent source totals, including one filtered view and one empty or incomplete window. Check that each funnel step appears once, IDs nest where the definition requires it, and headline and trend use consistent weighting. Test the reported symptom on a migration, such as an empty card despite available rows. If you cannot render it, say exactly which checks remain.
5. Deliver the view or spec, definition links and uncovered questions. Update the launch checkpoint with the reviewed version and any gaps. Publish only within the user's requested scope.

## Common rationalizations

“The queries ran, so the dashboard is ready.” A wrong field binding or stale filter can still make the rendered result wrong.

## Red flags

Independent cohorts are presented as a nested funnel. A pooled rate is an unweighted average of percentages. A missing source is drawn as zero.

## Dispositions

Return **verified for use**, **limited coverage** (name the usable panels), or **draft pending validation**. Report publication status separately.
