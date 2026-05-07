# Decision — snowflake-mcp-rewriter spike (day 0)

## Recommendation: **Pivot narrative** (provisional, gated on the spike run)

Don't commit to building "an LLM-backed general SQL rewriter for
Snowflake." Commit to the spike, and prepare to ship a narrower
product the spike will likely justify: **"Claude catches expensive
queries before you run them and proposes a cheaper version, with
your explicit approval."** Same plumbing, smaller and more
defensible promise.

This is a *day-0* recommendation — the spike has not been run against
real services in this environment because no credentials are
available. The recommendation is what I would tell the engineer
*before* they run it, on the basis of what the assumption
analysis surfaced. Once the spike runs, follow the decision table in
`tradeoffs.md` to confirm or replace this call.

## Reasoning

Three things pushed me off "Build" toward "Pivot narrative" before
any code runs:

1. **M3 is the load-bearing assumption and the literature is mixed.**
   "LLM rewrites SQL and the result set is identical AND it's
   meaningfully cheaper" is a *conjunction* of two non-trivial
   properties. Research on LLMs writing SQL shows reasonable
   correctness on synthesis but uneven performance on
   *cost-aware* rewrites, and the equivalence-checking literature
   for SQL is its own field. The probability the vanilla setup
   clears 4/5 equivalence AND 3/5 cost wins on the *first* attempt
   is, in my prior, well under 50%. That doesn't mean stop — it
   means assume the win will land on a sub-class of queries (most
   plausibly: predicate-pushdown / "missing WHERE" cases) and frame
   the product around that subset.

2. **M4 — the consent IA — is the part where MCP-shaped products
   most often break,** and the team has not shipped on MCP before.
   The spike's `input()`-prompt walk-through is the cheapest way to
   discover whether the right shape is one tool with a proposal
   field or two tools with an explicit handoff. Either choice
   constrains the production server design heavily — making it on
   the basis of the walk-through is a much better bet than making
   it in a design doc.

3. **M1 and M2 are *probably* fine, and that's the trap.** It is
   tempting to skip ahead to "build the MCP server" once those two
   come back green, because they're the legible, infrastructure-y
   parts. But M3 and M4 are the ones that decide whether the
   product is worth building, and they're the ones the rewritten
   narrative ("forgotten-filter detector," human-in-the-loop) are
   most resilient to.

## What "build" would require to be the right call

All four must-hold gates land cleanly:
- M1 passes (synthetic MCP client round-trips all 5 fixtures with no
  serializer surprises).
- M2 passes (≥4/5 dominant operators named correctly).
- M3 passes **on its general form** (≥4/5 equivalence AND ≥3/5 cost
  wins, distributed across at least two query classes — not
  concentrated in one).
- M4 passes (the consent walk-through is unambiguous and the
  one-tool-vs-two-tool decision feels obvious after walking it).

If only M3's general form fails (equivalence holds, cost wins are
concentrated in one query class), pivot narrative. If M3's
equivalence fails repeatedly, stop the auto-rewrite path entirely
and consider a *suggestion-only* product. If M2 fails, pivot
architecture (pre-summarize EXPLAIN before LLM ingestion). If M1
fails, stop — there is no product without MCP.

## What I would do this week

1. Run `spike.py` interactively against a dev Snowflake account on
   the TPC-H sample data. Half a day.
2. Fill in `tradeoffs.md`'s pending Result / Learning / Pivot rows
   *as the run happens*, not after.
3. Record at least one **side finding** that the gates don't cover
   — undocumented EXPLAIN field, SDK surprise, an `input()` prompt
   that read awkwardly. A spike with no side findings probably ran
   too narrow.
4. Re-read this decision file with the filled-in `tradeoffs.md`
   open. Confirm or replace the recommendation.

A spike that "passes" all four gates without forcing a single change
to the plan is suspicious — gates were lenient or the spike was too
narrow. The honest expected outcome here is **a narrower, more
defensible product**, not a green light on the original framing.
