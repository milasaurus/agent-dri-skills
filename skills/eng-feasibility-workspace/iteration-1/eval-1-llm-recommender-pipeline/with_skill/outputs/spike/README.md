# spike

Single-file feasibility spike for the LLM-as-recommender bet. The
apparatus, not the experiment. The experiment is the four gates in
`../assumptions.md`; the result of running this is what gets pasted
into `../tradeoffs.md`.

## Run

```
pip install anthropic
export ANTHROPIC_API_KEY=...
python spike.py            # all 5 fixtures
python spike.py 2          # just fixture index 2 (cold-start)
REPEAT=2 python spike.py 0 # determinism check on fixture 0
MODEL=claude-haiku-4-5-20251001 python spike.py
```

No credentials in this environment, so the spike has not been run.
Once a key is provided, the script writes one JSON line per call to
`results.jsonl` and prints a roll-up against the assumption gates.

## What it tests

- M1 output shape (length / unique / valid IDs / no purchase re-recs)
- M2 ranking quality vs. a stand-in baseline + a manual top-5 review
- M3 latency + estimated cost per call
- M4 IA walkthrough across cold-start (F3) and long-history (F1, F5)
  branches

## What it does not test

- Real production baseline overlap — fixtures use a category-biased
  stand-in. Replace `_baseline()` with a snapshot from the production
  recommender on matched user IDs once that's available.
- Catalog at production scale — pinned at 200 items. If the real
  candidate pool is much larger, S2 in the assumptions becomes a
  must-hold and a candidate-gen step is needed in front of the LLM.
- Online serving behavior — no caching, no concurrency, no cold-cache
  vs. warm-cache split. The spike measures the call, not the system.
