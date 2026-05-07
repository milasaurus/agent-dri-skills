# LLM-recommender spike

A 1–2 day feasibility spike. See `SPIKE_PLAN.md` for the assumptions this
is testing and the kill criteria.

## Run it

```bash
pip install -r requirements.txt

# Dry run — no API key needed, uses a canned response so you can see the
# shape of every output and the report.
python run_spike.py --dry-run

# Real run — hits the provider. Defaults to Anthropic; pass --provider
# to switch. Reads ANTHROPIC_API_KEY from env.
export ANTHROPIC_API_KEY=...
python run_spike.py --n-users 50 --repeats 3
```

## Files

- `SPIKE_PLAN.md` — what we're testing, kill criteria, decision criteria
- `eval_dataset.py` — fixture eval set (replace with real-session sample)
- `baseline.py` — popularity ranker for the apples-to-apples comparison
- `llm_recommender.py` — the LLM ranker (real API call, dry-run safe)
- `metrics.py` — hit@k, NDCG@k, MRR, Kendall's tau, validity rate
- `run_spike.py` — orchestrates a single run and prints the result table

## Reading the result

`run_spike.py` prints one table. The popularity row is the bar. If the LLM
row doesn't clear it on quality, the spike has answered the question and we
stop. See `SPIKE_PLAN.md` for the full decision rubric.

## What this is NOT

Production code. No service, no retries-with-backoff strategy beyond the
bare minimum, no observability, no batching. The point is to learn, not to
ship.
