# tradeoffs.md — LLM-as-recommender spike

Durable record of what the spike validated and the pivots forced.
Format follows the eng-feasibility skill: assumption / gate / result /
learning / pivot, one block per must-hold.

> **Status — 2026-05-07.** Spike code is written and runnable
> (`spike/spike.py`). It has **not been executed** in this environment
> because no `ANTHROPIC_API_KEY` is available. Each must-hold below
> records the gate set on day 0 and the **conditional pivot** that
> follows from the result, so an engineer running the spike tomorrow
> can fill in `Result` + `Learning` and read off the consequence
> directly. Anything written as "expected" is a hypothesis to be
> overwritten with measurement — flagged with `⟂` so it can't be
> mistaken for evidence.

## Headline finding (to be written after the run)

The strongest finding leads here once the spike runs. Two sentences:
what's now true that wasn't, and the one decision that followed.

> Placeholder — replace with the actual top-of-funnel finding (good or
> bad) after running. If the headline is "all four gates passed,
> nothing changed in the plan," the gates were too lenient — push back.

---

## M1 — Output shape reliability

- **Assumption.** Given system prompt + user history + 200-item
  catalog, the LLM returns exactly 20 distinct, in-catalog item IDs in
  parseable JSON with no preamble.
- **Gate.** ≥ 9/10 calls (5 fixtures × 1 rep + 5 stretch reps if
  needed) produce: parseable JSON, length 20, all unique, all in the
  supplied catalog. Purchase exclusion (rule 4 in the system prompt)
  tracked alongside as a soft gate — failures here mean a post-process
  filter is required, not that the project dies.
- **Result.** _To be filled after running spike.py — paste the M1
  line from the roll-up._
- **Learning.** _To be filled. Side findings to watch for: does the
  model wrap the JSON in markdown fences? Add a preamble despite the
  prompt? Drop to 19 items when the prompt gets long? Hallucinate
  IDs that look syntactically right (`sku_1234` for an out-of-range
  index) when the catalog is dense?_
- **Pivot.**

  | Result                    | Pivot                                                                                                                                                |
  |---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
  | Pass (≥ 9/10)             | No change. Build with a defensive parse + post-filter for the rare bad call.                                                                         |
  | Fail on length / parse    | Switch to JSON-mode / structured output (where supported) before declaring fail. If still failing, this is a stop or model swap.                     |
  | Fail on catalog membership| Stop or pivot architecture: re-rank a constrained candidate list using logit-bias or a verifier model. "Just prompt it harder" is not a known fix.   |
  | Fail on purchase exclusion| Build a deterministic post-filter step. Do not rely on the model. Add the filter to the plan; not a project-killer.                                  |

---

## M2 — Ranking quality vs. baseline

- **Assumption.** The LLM's top-20 has at least comparable
  top-of-list relevance to the existing recommender on the same
  histories.
- **Gate.** Mean recall@5 vs. the baseline-stand-in ≥ 0.40 across 10
  histories AND human judgment "plausible or better than baseline" on
  the top-5 for ≥ 7/10. Both halves required.
- **Result.** _To be filled. Recall@5 from the roll-up; human leg by
  reading top-5 of each fixture in `results.jsonl`._
- **Learning.** _To be filled. Watch for: does the LLM just rank by
  category match (i.e. mimic the baseline)? Does it ignore recency?
  Does it surface novelty the baseline never would? Does it recommend
  the highest-priced item regardless of history?_
- **Pivot.**

  | Result                                                          | Pivot                                                                                                                                                                                              |
  |-----------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
  | Both halves pass                                                | Build, but plan for an offline eval against a real holdout before launch. Spike pass ≠ launch-ready.                                                                                               |
  | Recall passes, human judgment fails                             | Pivot narrative: the LLM matches the baseline statistically but doesn't add value. Re-frame as "use LLM for re-ranking the head-of-list only" or stop.                                             |
  | Recall fails, human judgment passes                             | Likely the stand-in baseline is a poor proxy. Re-run M2 with a real production-baseline snapshot before deciding. Do not stop on this alone.                                                       |
  | Both fail                                                       | Stop. The core hypothesis ("LLM ranks well from raw events + catalog") is false at this prompt design. A bigger-model retry is allowed once; beyond that, stop.                                    |
  | Pass on long-history, fail on cold-start (F3)                   | Architecture pivot: route cold-start to a non-LLM fallback. The LLM serves the warm-history path. The original plan was "LLM for everything"; this splits the system in two.                       |

---

## M3 — Latency and cost envelope

- **Assumption.** A single recommendation call fits in either an
  online-with-cache budget (≤ 5s) or a precompute-only budget
  (≤ 30s), at ≤ $0.02/call median.
- **Gate.** Median latency in one of the two buckets across the run;
  median estimated cost ≤ $0.02. Outside both ⇒ architecture pivot or
  stop.
- **Result.** _To be filled. Numbers come straight from the roll-up
  (`median latency`, `median cost/call`)._
- **Learning.** _To be filled. Side findings to watch: does latency
  scale superlinearly with prompt size (catalog padding)? Are output
  tokens ≈ 20 IDs × short string ⇒ small? How much of the input cost
  is the catalog block (candidate for prompt caching — see "nice if
  it holds")?_
- **Pivot.**

  | Result                          | Pivot                                                                                                                                            |
  |---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
  | ≤ 5s median, ≤ $0.02            | Online serving feasible with a thin cache. Build path A.                                                                                          |
  | 5–30s median, ≤ $0.02           | Online infeasible. Plan around precompute + serve-from-cache. Refresh on event-trigger or daily cron. Significant architecture change vs. day-0. |
  | > 30s median or > $0.02         | Full pivot: smaller model retry, or LLM only for re-ranking a tiny head-of-list (k ≤ 50), or stop.                                               |
  | Cost dominated by catalog block | Add prompt caching to the plan. Was "nice if it holds"; becomes "must hold" for unit economics.                                                  |

  ⟂ Day-0 expectation, to be overwritten: a 200-item catalog + 50
  events at Sonnet pricing is roughly low-thousands of input tokens
  and ~200 output tokens — order $0.005–$0.02. Latency at this size
  on Sonnet is typically a few seconds. **This is a hypothesis, not
  a finding.** Replace with measured numbers.

---

## M4 — End-to-end information architecture walkthrough

- **Assumption.** Walking the flow end-to-end (load history → resolve
  catalog → call LLM → parse → return ranking) on both a cold-start
  user and a long-history user surfaces no missing input, ambiguous
  decision, or undocumented state-handoff.
- **Gate.** Spike runs cleanly on F3 (3 events) and F1/F5 (≥ 50
  events) without ad-hoc fixes mid-run; cold-start and catalog-source
  decisions are written down here with the option chosen and why.
- **Result.** _To be filled after running. The act of running F3
  before F1 is the test — does anything need to change?_
- **Learning — already surfaced from writing the spike (this is the
  point of the IA walkthrough):_
  - **Cold-start has to be a separate path.** Asking the LLM to rank
    20 items from 3 events of history will ride mostly on category
    prior, which a popularity-by-category lookup does just as well
    for ~$0. The spike documents this as a fallback rule
    (`walkthrough_check`). Plan must include the routing logic.
  - **The LLM does not retrieve, it ranks.** The candidate catalog
    has to come from somewhere. Stuffing the entire product catalog
    into context is not viable beyond toy scale (S2). The plan
    needs a candidate-generation step in front of the LLM — even if
    that step is "items in the user's preferred categories from the
    last 30 days." Day-0 plan said "LLM takes history → returns
    items"; the IA walk says "candidate-gen → LLM ranks
    candidates → post-filter → return."
  - **Purchase exclusion belongs in code, not in the prompt.** The
    spike includes it in the system prompt as a tripwire (rule 4)
    so M1 can measure compliance, but the production design should
    apply it as a deterministic post-filter regardless. Don't trust
    a model to honor a hard business rule.
- **Pivot.** Plan changes from "LLM is the recommender" to
  "candidate-gen → LLM ranker → deterministic filter, with a
  non-LLM cold-start branch." Concrete, even before any number is
  measured. This is exactly the kind of finding the IA walkthrough
  exists to surface on day 0.

---

## Should-hold observations (logged, not gated)

- **S1 determinism.** Run with `REPEAT=2` on at least one fixture.
  If the two rankings differ materially, document the diff
  (Jaccard@20, Kendall tau on top-5). Caching keys then need to
  include the model and a seed, or accept ranking drift.
- **S2 catalog scale.** The spike uses 200 items. Estimate the
  catalog size at the actual candidate-gen output and decide
  whether the assumption "catalog fits in prompt" still holds at
  that scale.
- **S3 history size.** Token-count a real 50-event payload from
  production logs. If significantly larger than the synthetic
  fixtures, M3 numbers may not transfer.

## Decision

See `decision.md`. Default until the spike runs: **conditional build
behind the spike's gates** — proceed to plan a "candidate-gen →
LLM ranker → deterministic filter" architecture, with the cold-start
branch baked in, **conditional on the spike's M1, M2, and M3 gates
passing when run**. The IA walkthrough has already pivoted the
architecture once; that pivot stands regardless of M1/M2/M3 outcomes.
