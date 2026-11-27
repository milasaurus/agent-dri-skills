---
name: launch-measurement-run
description: Coordinate or resume measurement for a product launch. Use when the request spans planning, instrumentation, engineering, audit, and reporting.
---

# Launch measurement run

## Why this skill

A dashboard can be complete while the launch is still unmeasurable. The runbook tracks which claims the available evidence can support and which stage can unblock the rest.

## When to use

Start here for a full launch or a status check. For one deliverable, go directly to its stage.

## Process

1. Read the brief, shipped or proposed user flow, target audience, rollout dates and existing measurement artifacts. Find out what decision the owner needs to make. If the goal or eligible population is unclear, ask the question that changes the plan. Treat an unconfirmed goal as an assumption in a requested draft.
2. Follow the chain below. Read each stage when needed. Reuse current artifacts, including work completed outside this chain. For a status request, report the first unresolved dependency and its owner.

| Stage | Input → output | Ready to advance when |
| --- | --- | --- |
| [Plan](../launch-measurement-plan/SKILL.md) | Brief → metric definitions | The decision, eligible unit and limits of the claim are explicit. |
| [Instrumentation](../launch-instrumentation-spec/SKILL.md) | Definitions → metric-to-signal map | Each metric has a verified source, provisional evidence or an explained gap. |
| [Engineering handoff](../launch-eng-handoff/SKILL.md) | Confirmed gaps → scoped implementation asks | Route writer changes to the producer owner and modeling changes to the data owner. Carry both acceptance checks into audit. Skip this stage only if neither needs work. |
| [Logging audit](../launch-logging-audit/SKILL.md) | Intended contract + deployment evidence → observed coverage | The checks use the launch's own eligible traffic. Record pending rows if traffic or delivery is still outstanding. |
| [Dashboard](../launch-dashboard-metrics/SKILL.md) | Definitions + audit → verified reporting surface | Panels reproduce their source counts and expose coverage gaps. |

3. Keep a short checkpoint in the existing launch artifact: stage, metric IDs, definition version, evidence links with environment and window, outstanding decisions, owner and next check. Distinguish first eligible exposure, first usable instrumentation and earliest fully observed outcome window. These can be three different dates.
4. On resume, open the last checkpoint and check what has changed in the rollout, schema or metric definition. Reopen affected rows and downstream results. Continue independent rows. If a warehouse or renderer is inaccessible, supply the exact query or check and expected result shape for someone with access. Mark it unexecuted.
5. Use the user's chosen destination. When the request is to draft, return drafts. Ticket creation, publication and messaging follow the user's authorization for those actions.

## Common rationalizations

“The PR merged, so continue from the dashboard.” Check which build and data the audit actually saw.

## Red flags

A stage reports completion from another stage's prose. A pre-launch proxy has become a production number. An inaccessible source is reported as empty.

## Dispositions

Return **complete**, **continue at <stage>**, or **waiting on <dependency>** with the artifact and next action. A dashboard draft can coexist with an open logging audit.
