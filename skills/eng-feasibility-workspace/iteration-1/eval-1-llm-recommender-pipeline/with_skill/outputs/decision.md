# Decision — LLM-as-recommender feasibility

## TL;DR

**Spike, don't just build.** The original framing — "should we just
start building?" — would commit weeks of engineering to a plan whose
foundation has not been tested end-to-end. A one-day single-file spike
against the real Anthropic API answers the four load-bearing questions
cheaply.

The spike artifacts in this directory are ready to run as soon as a
key is available. The day-0 IA walkthrough already produced one
architectural pivot (see below) before any API call.

## Decision class (per the skill)

**Pivot architecture — conditional on running the spike.**

- The original plan ("LLM takes 50 events → returns 20 IDs") is
  insufficient. The IA walkthrough surfaced three structural changes
  before any model call:
  1. A **candidate-generation step** is required in front of the LLM.
     The LLM ranks; it does not retrieve. Anything beyond a few
     thousand candidate items cannot fit in context cleanly.
  2. **Cold-start needs a separate path**, not the LLM. Three events
     of history don't carry enough signal to justify a multi-second
     model call. A category-popularity lookup serves that bucket
     better at ~$0.
  3. **Purchase exclusion (and similar hard business rules) belongs
     in deterministic code**, not in the system prompt. Use the prompt
     to measure compliance during the spike; rely on a post-filter in
     production.

- Whether the resulting architecture is worth shipping at all depends
  on the spike's measured results for M1 (output shape), M2 (ranking
  quality), and M3 (latency / cost). The spike has explicit gates and
  conditional pivots in `tradeoffs.md` for every plausible outcome.

## Why not "just build"

- "LLM ranks well from raw event JSON + catalog" is a behavior bet, not
  a documentation question. There is no SDK changelog that answers it.
- "LLM emits exactly 20 valid IDs from a supplied catalog" is the kind
  of constraint models silently violate (truncation, hallucinated IDs,
  markdown fences). Discovering a 5% bad-output rate in week 4 of a
  build is a refactor; discovering it on day 0 is a system-prompt tweak
  or a model swap.
- A 10× wrong guess on per-call latency or cost invalidates the entire
  serving architecture. Online serving and precompute serving are very
  different systems.
- The IA walk surfaced three architecture changes for free, before any
  code that depends on the prior architecture was written.

## Why not "stop"

Nothing in the day-0 analysis says the project is impossible. There is
a plausible path: candidate-gen narrows the catalog to a few hundred
items, the LLM ranks, a post-filter enforces hard rules, cold-start
falls back to a non-LLM path. Each of the four must-hold gates has a
realistic chance of passing on a current production-grade model. The
spike is the cheapest way to find out.

## What ships next

1. Engineer with credentials runs `spike/spike.py` across all 5
   fixtures, plus one `REPEAT=2` run for the determinism check (S1).
2. Pastes the roll-up numbers into the four "Result" sections of
   `tradeoffs.md` and reads the top-5 of each fixture for the
   human-judgment leg of M2.
3. Reads the matching row in each pivot table; updates the headline
   finding; commits the result.
4. Either (a) writes the build plan around the new architecture
   (candidate-gen → LLM ranker → filter, cold-start branch), or
   (b) takes the pivot the gates dictate.

## Files in this directory

- `assumptions.md` — must-hold / should-hold / nice-if-it-holds with
  falsifiable gates.
- `spike/spike.py` — single-file runnable spike. Real Anthropic SDK,
  no mocks, prints everything, walks the IA flow.
- `spike/README.md` — how to run, what it tests, what it does not.
- `tradeoffs.md` — durable record. Gates set; results pending the run;
  conditional pivots written for every plausible outcome.
- `decision.md` — this file.
