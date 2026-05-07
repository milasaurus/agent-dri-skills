---
name: eng-feasibility
description: Build a focused spike to validate a project's load-bearing assumptions before committing to a build. Lists the assumptions that would kill the project if false, defines falsifiable go/no-go gates for each, and turns the spike's findings into a build / pivot-architecture / pivot-narrative / stop decision.
trigger:
  - "A new project, prototype, or feature has uncertain technical foundations and a build is about to start."
  - "An engineer is about to commit to a multi-week effort but hasn't tested the core hypothesis end-to-end."
  - "A team wants to know whether a project's assumptions hold before investing in production infrastructure."
archetypes:
  - tech-lead
  - staff-eng
---

## Overview

Before a build starts, list the project's load-bearing
assumptions, write a single-file spike that exercises them
against real services, and capture the learnings and pivots
in a `tradeoffs.md` that converts the result into a build /
pivot / stop decision. The assumptions list is always the
first deliverable — it is what makes "is this project worth
the time?" a decidable question.

The spike de-risks development on two axes: *technical
feasibility* (does the API / model / integration actually do
what we need?) and *information architecture and user flow*
(does the end-to-end experience hang together when we walk
through it?). Both surface problems while they are still
cheap to fix.

Required artifacts:

- **Assumptions list** — categorized must-hold / should-hold
  / nice-if-it-holds, each with a falsifiable gate.
- **Spike** — single-file experiment that exercises the
  must-hold assumptions end-to-end against real services.
- **`tradeoffs.md`** — durable record of what each spike run
  validated, what was learned, and which pivots followed.
- **Decision** — build, pivot architecture, pivot narrative,
  or stop.

## When to Use

Use this skill when:

- a build depends on a behavior bet (LLM picking the right
  strategy, an API meeting a latency budget, a model
  achieving a quality bar) that has not been validated
  end-to-end,
- the team can't estimate the work, can't break it down, or
  is debating between multiple solutions because an
  empirical fact is missing,
- the project will use an API, SDK, or platform the team
  has not shipped on before,
- collaboration spans teams or unfamiliar codebases and the
  technical scope is unclear.

Do not use when:

- the integration is well understood and the risk is
  execution, not validity,
- the project's risk is product-market fit (use a
  user-tested prototype instead),
- the assumption can be answered by reading the docs in
  five minutes (read the docs first).

## Process

1. **Frame the project.** State what the project is, who it
   serves, and what ships. Write the core hypothesis in one
   sentence; sharpen it until it is falsifiable.

2. **List the load-bearing assumptions.** This list is the
   precondition for code. Categorize each:
   - **Must hold** — project does not exist if false. Spike
     these.
   - **Should hold** — architecture changes if false but the
     project survives. Test if cheap; otherwise log as a
     risk.
   - **Nice if it holds** — optimization or polish. Don't
     spike.

   Cover at minimum:
   - **API capability** — "Endpoint X accepts parameter Y."
   - **Model / behavior** — "The LLM can reliably do task T."
   - **Latency / cost** — "Op O completes in under N seconds."
   - **Data shape** — "Output URLs are valid for ≥T minutes."
   - **Integration** — "Service A and B can be wired with
     the contract in the docs."
   - **Information architecture / user flow** — "The
     end-to-end flow (steps the user takes, decisions they
     make, where state lives between them) hangs together
     when walked through." Walking the flow inside the
     spike — even with a CLI or pseudo-UI standing in for
     the real interface — is the cheapest way to catch a
     missing step, an ambiguous decision, or a state-handoff
     gap before they become refactors.

   Two-to-four must-hold items is the sweet spot.

3. **Define a go/no-go gate per must-hold assumption.** Each
   gate is measurable and falsifiable. "It works" is not a
   gate. "≥3/5 cases produce the expected output" is.

4. **Time-box the spike.** Ask: what's a reasonable window
   to gain enough understanding to return to normal
   planning? Hours-to-a-day for most spikes. If the box
   blows, reset based on what you've learned — don't extend
   silently.

5. **Write the spike** as a single file:
   - Hardcode inputs at the top (CLI arg or env var
     override is fine).
   - Print everything: inputs, outputs, intermediate
     values, timing.
   - Real services only — no mocks.
   - No abstractions you'd reuse later: no Pydantic models,
     no FastAPI routes, no error envelopes, no config files.
   - Re-runnable across 5+ hand-picked inputs that span the
     space of expected use.
   - **Walk the user flow end-to-end inside the spike**, even
     if it stands in for the real UI with `input()` prompts
     or printed menus. Information-architecture problems
     show up immediately when you have to describe each step
     to the user in flat text — missing inputs, ambiguous
     branches, and state that has to be remembered between
     calls all surface here, when they are still cheap.
   - Canonical reference: image-morpher `spike/spike.py` —
     ~270 lines, one file, no production scaffolding. The
     spike walks the real user flow (round-0 → pick winner
     → pick intent → round-1) via console prompts; that
     walkthrough is what surfaced the LLM-as-router IA
     problem on day 0.

6. **Run the spike** across the hand-picked inputs and tally
   pass/fail against each gate. Capture results in
   `tradeoffs.md` as you go (see step 7) — not in the
   terminal scrollback.

7. **Write `tradeoffs.md`** — the durable artifact that
   captures, for each assumption, what was validated and
   the pivot it forced. The spike writes here as it runs;
   it is not a polish-at-the-end document. Sits next to the
   spike (e.g. `spike/tradeoffs.md`).

   For each must-hold assumption, record:
   - **Assumption.** What was tested.
   - **Gate.** The pass condition set up front.
   - **Result.** Pass / fail / inconclusive, with evidence
     (sample inputs, outputs, error codes, timings).
   - **Learning.** What's now true that wasn't before. Side
     findings (URL TTLs, undocumented fields, SDK
     migrations, silent no-ops) belong here too — they are
     often more valuable than the gate result.
   - **Pivot.** What changes in the build or plan because
     of this finding. Pros/cons table for architecture
     pivots. "No change required" is a valid pivot — but a
     `tradeoffs.md` with no pivots anywhere is suspicious.

   Strongest finding leads. Keep it digestible in one
   sitting. Don't assume the reader knows the domain —
   link to tickets, docs, code. A finding that changes
   nothing is an observation, not a finding — push for the
   "so what."

8. **Produce a decision.** One of:
   - **Build** — assumptions hold, gates pass.
   - **Pivot architecture** — assumption failed but project
     survives; update the plan.
   - **Pivot narrative** — gate failed but the failure is
     interesting; reframe the project around what it
     teaches.
   - **Stop** — foundation does not hold; document so the
     next team doesn't repeat it.

## Red Flags

- No written assumptions list exists before the spike.
- The list contains only "should hold" / "nice if it holds"
  items; project-killers are not named.
- A go/no-go gate is missing or unmeasurable for any
  must-hold assumption.
- The spike has more than one file, abstractions, a config
  system, or imports the project's package.
- The spike runs against mocks instead of real services.
- The spike was written before the assumptions were listed.
- No `tradeoffs.md` exists, or it is missing the
  assumption / gate / result / learning / pivot structure
  for any must-hold assumption.
- The spike "passed" but produced no findings that change
  the plan — gates were lenient or the spike was too narrow.
- The spike grew into a multi-week project.

## Verification

Before declaring the spike complete, the agent should be
able to answer:

- Is the core hypothesis stated in one falsifiable sentence?
- Are the must-hold assumptions named, categorized, and
  gated?
- Did the spike exercise the assumptions end-to-end against
  real services?
- Did findings reshape the plan? If not, were gates too
  lenient or the spike too narrow?
- Is the decision (build / pivot architecture / pivot
  narrative / stop) explicit?
- Does `tradeoffs.md` record each must-hold assumption with
  its gate, result, learning, and pivot?

## Reference: image-morpher

Canonical example. Read before running this skill:

- `docs/project-brief.md` — names the core hypothesis and
  lists open technical questions to validate before any
  build.
- `docs/plan.md` Unit 1 ("Spike") — Day 0 precondition.
  Decision 7 documents the plan pivot the spike forced
  (LLM-as-router → user-picks-strategy). The "Open
  questions to validate while building" and "Risks" tables
  enumerate assumptions explicitly.
- `spike/spike.py` — the single-file spike, ~270 lines,
  real Luma + real Anthropic calls, no production
  abstractions.
- `spike/README.md` — describes the spike as "the
  apparatus, not the experiment."

The spike's most valuable output was the plan pivot in
Decision 7, not a passing gate. A spike that "passes"
without reshaping anything is suspicious.
