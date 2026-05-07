# PLANS.md

Plans in this repo follow five rules in addition to whatever skill authored them (`ce-plan`, `planning-and-task-breakdown`, or a hand-written outline). These rules cover the gap between "the plan was written" and "the plan got the work done." They don't replace plan-authoring tools — they're what those tools should produce.

## Self-contained on a cold read

A plan must be readable by someone who has only the working tree and the plan file. No "see the architecture doc," no "as discussed previously." If a reader needs a definition or context, inline it — even at the cost of some duplication. The test: hand the plan to someone who has never seen this repo. Can they execute it?

## Acceptance is observable behavior

State acceptance as something a human can run and see, not as a structural attribute of the code. "After running the server, `GET /health` returns 200 with body OK" — not "added a `HealthCheck` struct." If the change is internal, name a test that fails before and passes after, plus a scenario that exercises the new behavior end-to-end.

## Decisions are resolved in the plan, not deferred to the implementer

When a plan reaches an ambiguity, it picks a direction and records why. Never "the implementer can choose A or B." If the choice genuinely needs implementation-time discovery, name it as an explicit experiment with a promote/discard criterion — don't pretend it's resolved when it isn't.

## Four living sections, kept current during execution

A plan that goes stale during implementation has failed at its job. Every plan must contain and update these four sections as work happens:

- **Progress** — checkboxes with UTC timestamps. At every stopping point, split partially-done items into "done" and "remaining" so the next reader sees the actual state.
- **Decision Log** — each decision made mid-implementation, with rationale and date.
- **Surprises & Discoveries** — what the plan didn't predict, with concise evidence (test output, error message, profiler line).
- **Outcomes & Retrospective** — at completion, what shipped vs. planned, what was cut, what was learned.

Without these kept current, the plan is a dead artifact and the next reader has to rebuild context from `git log`.

## Idempotence and rollback for risky steps

For destructive or migration steps, name the rollback path. For repeatable steps, say so explicitly so a re-run after partial failure isn't ambiguous. Steps without recovery guidance are landmines.
