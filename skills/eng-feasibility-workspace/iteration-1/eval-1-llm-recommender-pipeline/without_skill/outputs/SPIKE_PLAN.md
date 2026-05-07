# Spike: LLM-as-recommender feasibility

## Decision being de-risked
We are considering replacing the current recommendation pipeline with an LLM
that takes the last 50 user events as JSON and returns a ranked list of 20
item IDs. Before committing engineers to that build, we want a 1–2 day spike
that tells us whether this is even worth pursuing.

## Load-bearing assumptions
This project breaks if any of these are false. We test them in priority order
and **stop early** if an upstream one fails.

1. **Quality** — On a frozen eval set sampled from real sessions, the LLM's
   top-20 beats a popularity baseline on hit-rate@20 and NDCG@20 by a margin
   we'd actually ship. (If it loses to popularity, nothing else matters.)
2. **ID validity** — The model returns 20 unique IDs that all exist in the
   catalog, ≥ X% of the time without retries. Hallucinated IDs are the most
   likely silent failure mode for this design.
3. **Latency & cost** — p95 end-to-end latency under our recs SLO (assume
   400 ms for the spike target; adjust to real SLO), and cost-per-1k-recs
   inside the budget the product team will accept.
4. **Stability** — Same user history, run 3x, produces rankings whose
   Kendall's tau ≥ 0.7. Otherwise A/B testing and debugging become a mess.

## Out of scope for the spike
- Production eval harness
- Feature store / online serving
- Vendor selection (we test one provider; if it works, we benchmark others)
- Re-ranking, candidate generation, or hybrid architectures
- Personalization beyond the 50-event window

## Kill criteria (any one => stop)
- Quality is below the popularity baseline.
- ID-validity rate < 90% without constrained decoding (and constrained decoding
  isn't available with the chosen provider).
- p95 latency > 2x our SLO with no obvious path to close the gap.
- Per-1k-recs cost > 10x the current pipeline with no path to close the gap.

## Decision criteria (all must be true => greenlight)
- Quality beats baseline on at least one of NDCG@20 or hit-rate@20 by a
  margin we'd ship.
- ID validity ≥ 95% (with whatever post-processing we'll ship).
- p95 latency within SLO budget (or a clear plan to get there: caching,
  smaller model, batching).
- Cost per 1k recs is within 3x of current pipeline AND product accepts it.
- Kendall's tau across repeat runs ≥ 0.7.

## What this spike is NOT
A production system. Code is intentionally single-process, single-file per
concern, no service plumbing. If results are positive, we throw the spike
away and design the real thing.

## Time budget
Day 0 — write spike, agree on eval set, agree on baseline. (This file + the
code in this directory.)
Day 1 — run against ~200 real user sessions, compute metrics, write report.
Day 2 (only if needed) — iterate prompt or try a smaller model.

## Files in this spike
- `SPIKE_PLAN.md` — this file
- `eval_dataset.py` — synthetic fixture; swap in a real-session sample on day 1
- `baseline.py` — popularity baseline ranker
- `llm_recommender.py` — the LLM ranker under test (real API call, dry-run safe)
- `metrics.py` — hit-rate@k, NDCG@k, MRR, Kendall's tau, validity rate
- `run_spike.py` — orchestrator: runs both rankers on the eval set, prints results
- `requirements.txt` — minimal deps
- `README.md` — how to run

## How to read the result
The spike prints a single table. We are looking for:

```
                  hit@20   ndcg@20   mrr   p95_ms   $/1k   id_valid%   tau
popularity        ...      ...       ...   ...      ...    100.0       1.00
llm-recommender   ...      ...       ...   ...      ...    ...         ...
```

If the LLM row is worse on quality, we stop. If quality wins but latency or
cost is off, we have a scoped follow-up question (smaller model? cache?
batch?) instead of a vague "should we build this."
