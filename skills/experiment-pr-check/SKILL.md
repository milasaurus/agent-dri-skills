---
name: experiment-pr-check
description: Review an experiment setup PR against its registered design and give separate merge and exposure decisions. Use when a change wires assignment, treatment delivery, exposure logging, or experiment metrics.
---

# Experiment PR check

## Why this skill

A green build proves neither that the two groups received different experiences nor that the primary can tell them apart. Trace one eligible unit through each arm before giving the setup a pass.

## When to use

Use on a setup or ramp PR with a tracker row, flag configuration, or equivalent design record. If a record is missing, review the evidence you have and identify which decision requires the missing record.

## Process

Lead the review with answers to the **three questions that can invalidate the whole test**.

1. **Can the configured primary measure the registered difference?** Compare the platform or analysis configuration to the tracker's formula, unit, denominator and outcome window. Calculate it for one example in each arm. A logged completion flag hardcoded to true on every retained row cannot distinguish success rates.
2. **Does assignment reach the experience being tested, and from when?** Follow both branch values to the actual render, API response, worker, or side effect. Identify the first deployed version and eligible path that delivers the difference. A flag lookup in a merged PR alone establishes neither delivery nor exposure.
3. **Do assignment, exposure and outcome identify the same experimental unit?** Trace keys through the join and aggregation. Different keys can work with a documented mapping and correct timing. Show how duplicates, missing joins and units with zero outcomes affect the denominator.

Then fill the comparison table. Use one row per independently actionable difference. Cite file and line, setting, sample or tracker version. Distinguish a verified match, implementation blocker, tracker correction, unanswerable design and missing evidence.

| Field | Tracker says | PR or deployed configuration does | Verdict and evidence | Fix and owner |
| --- | --- | --- | --- | --- |
| Assignment | Key, unit, eligibility, exclusions, split and arm weights | Trace predicate order, stable assignment and repeat visits | | |
| Treatment | Current control, treatment behavior, relevant routes and clients | Follow the flag through delivery, including fallbacks and version gates | | |
| Exposure | Trigger, identity, deduplication and time | Check both arms and whether logging happens before any treatment-dependent selection | | |
| Outcomes | Primary, guardrails, attribution window and balance checks | Trace emission to analysis, including missing outcomes and per-arm coverage | | |
| Operations | Sized audience, overlapping tests, platform settings, ramp and rollback | Compare actual reach and toggles, deployment sequence, cleanup owner and PR claims | | |

When sample traffic exists, count distinct assigned units by arm against configured weights for each rollout period. Compare exposure and outcome joins separately. A join that drops control rows can create apparent lift even with balanced assignment. Without samples, identify the query or fixture, owner and evidence required before exposure or the next ramp.

## Common rationalizations

- “The flag is off, so the setup is fine.” Prove it stays off on every affected path. A safely dormant PR can merge while exposure still waits on logging.
- “The dashboard is balanced.” Counts after a join can conceal both bad assignment and dropped outcomes. Start with assignment records.

## Red flags

Treatment and control log different meanings under the same event. An already-live path bypasses the gate. A tracker edit would silently redefine the hypothesis after exposure.

## Dispositions

Return **merge** or **hold merge** and independently **ready to expose** or **hold exposure**. Explain which evidence changes each call. If the PR can activate a broken path on merge, hold both. Mark deployment-dependent checks as unverified until observed. Return review feedback in the requested location and preserve the team's control over traffic.
