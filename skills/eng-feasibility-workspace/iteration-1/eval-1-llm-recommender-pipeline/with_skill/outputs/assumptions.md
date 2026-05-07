# Assumptions — LLM-as-recommender spike

## Frame

- **Project.** Replace the existing recommendation pipeline with an LLM
  that ingests a user's last 50 events (as JSON) and returns a ranked
  list of 20 item IDs.
- **Who it serves.** End users on whatever surface the existing
  recommender powers (home feed, "for you," etc.).
- **What ships.** A service endpoint that, given a user history, returns
  a ranked top-20 list usable by the same downstream consumers as the
  current pipeline.
- **Core hypothesis (one falsifiable sentence).** An off-the-shelf LLM,
  prompted with a user's last 50 events as JSON and the catalog of valid
  item IDs, will reliably emit a parseable ranked list of 20 valid IDs
  whose top-of-list quality is at least comparable to the current
  recommender, within a latency-and-cost envelope a serving system can
  carry (with caching).

## Should we spike?

**Yes.** Every load-bearing claim is a behavior bet against a model — none
of them can be answered by reading docs. Specifically:

- "The LLM ranks well" is not in any SDK changelog. It has to be
  measured.
- "The LLM emits valid IDs from our catalog" is the kind of constraint
  models silently violate (hallucinated IDs, truncated lists, prose
  preamble around the JSON). This is a known failure mode and has to be
  measured on real prompts at real list sizes.
- Per-request latency and cost at this prompt size determine the entire
  serving architecture (online call vs. precompute vs. cache layer). A
  factor-of-10 wrong guess here invalidates the whole plan.
- The information-architecture question — where this slots into the
  pipeline, what happens with <50 events, where the candidate catalog
  comes from, how staleness is bounded — is the kind of thing that
  refactors the build mid-flight if surfaced late.

A one-day single-file spike against the real LLM API, on real (or
realistic) user histories from production, answers all four cheaply.
Skipping it would commit weeks to a plan whose foundation is unverified.

## Must hold (project does not exist if false — spike these)

### M1. Output shape reliability

**Assumption.** Given the system prompt + a user history + the catalog
of valid IDs, the LLM returns exactly 20 distinct IDs, all drawn from
the catalog, in a parseable structure, with no preamble.

**Gate.** ≥ 9/10 hand-picked user histories produce a parseable response
where the list has length 20, all entries are unique, and all entries
are members of the supplied catalog. Zero is not a passing score for
"all entries valid" — a single hallucinated ID per call destroys
downstream joins.

### M2. Ranking quality vs. baseline

**Assumption.** The LLM's top-20 has at least comparable top-of-list
relevance to the existing recommender on the same user histories.

**Gate.** On 10 hand-picked histories, the LLM's top-5 overlaps the
existing recommender's top-20 by mean ≥ 2/5 (i.e. ≥ 40% recall@5 vs.
the production system) AND a human reviewer (the engineer running the
spike) judges the LLM's top-5 "plausible or better than baseline" on
≥ 7/10 cases. Both halves must hold; the overlap metric guards against
cherry-picked vibes, the human judgment guards against the LLM merely
mimicking the existing system.

> Why a human-in-the-loop gate: there is no offline ground truth on
> day 0. The point of this gate is not to certify quality for launch —
> it's to detect "obviously not in the running" failures (e.g.
> recommends popular generics regardless of history, ignores recency,
> recommends items the user just bought). A real eval comes later if
> the spike passes.

### M3. Latency and cost envelope

**Assumption.** A single recommendation call completes in a budget the
serving layer can absorb (online or via cache + async pre-compute) at a
unit cost the business can carry.

**Gate.** Median end-to-end latency across the 10 histories is
≤ 5 seconds (online-with-cache feasible) OR ≤ 30 seconds (precompute-only
feasible). Median per-call cost is ≤ $0.02 at the chosen model. Outside
both buckets ⇒ architecture pivot or stop. Numbers are starting points
to be tightened against real serving requirements once measured.

### M4. End-to-end information architecture walkthrough

**Assumption.** When the engineer walks the full flow in the spike —
load history → resolve catalog → call LLM → parse → emit ranked list —
no required input, decision, or state-handoff is missing. Cold-start
(< 50 events) and catalog-staleness branches both have a defined
behavior the engineer can articulate at the end of the walkthrough.

**Gate.** The spike runs end-to-end on at least one short-history user
(≤ 5 events) and one long-history user (≥ 50 events) without ad-hoc
fixes mid-run. The cold-start and catalog-source decisions are written
down in `tradeoffs.md` with the option chosen and why.

## Should hold (architecture changes if false — log as risks; test only if cheap)

- **S1. Determinism is acceptable at temperature 0.** If the same
  history produces materially different rankings across calls, caching
  semantics get harder. Cheap to check inside the spike (call twice,
  diff). Logged in tradeoffs even if not formally gated.
- **S2. The catalog fits in the prompt.** If the candidate catalog is
  millions of items, it cannot be stuffed into context — there's a
  retrieval/candidate-generation step in front. The spike assumes a
  bounded candidate pool (≤ a few thousand items, e.g. user-segment or
  recency-filtered). If reality is "the whole catalog," this becomes a
  must-hold and the spike has to add a candidate-gen step.
- **S3. Event JSON is small enough.** 50 events of typical event JSON
  fit in context with room for the catalog and the system prompt. Quick
  arithmetic during the spike.

## Nice if it holds (don't spike)

- Streaming responses cut perceived latency.
- Structured-output / JSON-mode reduces parse failures further.
- A single model serves all surfaces (vs. specializing).
- Prompt caching is available for the system prompt + catalog block.

## Time-box

One engineering day. End of day, either the four gates have measured
results in `tradeoffs.md` and a build/pivot/stop decision, or we reset
based on what's been learned. Do not extend silently.
