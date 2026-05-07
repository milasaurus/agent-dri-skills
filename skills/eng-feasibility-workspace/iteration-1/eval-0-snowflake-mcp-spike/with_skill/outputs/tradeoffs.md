# tradeoffs — snowflake-mcp-rewriter spike

This is the durable record of what each must-hold assumption tested,
what the spike found, and what changes in the build because of that
finding. Sits next to `spike.py`. Updated *as the spike runs*, not
polished at the end.

> **Status as of day-0.** The spike has been written but **has not
> been executed against real services** — this environment has no
> Snowflake or Anthropic credentials. The Result/Learning/Pivot rows
> below are scaffolded with their gate up front; fill them in on the
> first real run. The decision at the bottom is conditional on those
> results.

---

## M1 — MCP server round-trips a Snowflake query

| Field | Value |
| --- | --- |
| **Assumption** | The MCP Python SDK can host two tools (`run_query`, `explain_query`) over stdio, return Snowflake row sets as `TextContent`, and serialize Snowflake-shaped values (NUMERIC, TIMESTAMP_TZ, NULL, VARIANT, BINARY) without bespoke encoders. |
| **Gate** | A synthetic MCP client (Inspector or a hand-rolled stdio client) calls `run_query` against 5 hand-picked fixtures incl. NUMERIC / TIMESTAMP_TZ / NULL / VARIANT, and gets back valid JSON with values that round-trip to Python primitives without exceptions. |
| **Result** | _PENDING_ — `python spike.py --mcp-server`, then connect the MCP Inspector and call each fixture. Record the wire-format observed for each special-type column. |
| **Learning** | _PENDING_ — likely shape: which Snowflake types need a custom serializer (Decimals are the obvious one — already handled), whether `TextContent` is the right return shape vs. `EmbeddedResource`, whether the SDK gives us a clean place to surface "the user must approve this rewrite" (M4 IA question). |
| **Pivot** | _PENDING_ — if Decimals/timestamps/VARIANT round-trip cleanly: no change required, build the production server with the spike's tool surface as-is. If serialization is finicky: introduce a tiny `serialize_row()` helper and document the type matrix. If the IA handoff for consent is awkward in MCP: consider the two-tool split (`propose_rewrite` + `run_approved_rewrite`) instead of a single `run_query` that returns a proposal mid-flight. |

---

## M2 — Snowflake EXPLAIN is structured enough for the LLM

| Field | Value |
| --- | --- |
| **Assumption** | `EXPLAIN USING JSON` returns per-operator costs (bytes scanned, partitions assigned, row counts) in a stable enough shape that an LLM, given the JSON + the SQL, can correctly name the dominant expensive operator for our 5 fixtures. |
| **Gate** | LLM identifies the dominant operator correctly (matches the answer key in `FIXTURES` in `spike.py`) on **≥4 of 5** fixtures. |
| **Result** | _PENDING_ — `python spike.py --no-interactive` and read the SUMMARY block. |
| **Learning** | _PENDING_ — concretely: which top-level keys does the JSON actually have? `GlobalStats` is what `plan_cost_metric()` assumes; if the real shape is `Operations[].ExpressionProperties.bytes` instead, the cost metric needs to be derived per-step. If a fixture's EXPLAIN is missing cost numbers entirely (e.g. for queries that haven't been compiled before), that is a finding — Claude will be guessing on cold-cache plans. |
| **Pivot** | _PENDING_ — if M2 passes cleanly: no change. If 4/5 lands but the LLM is unstable on which sub-key it reads from: tighten the system prompt with one or two few-shot examples of the JSON-EXPLAIN shape. If <4/5: **pivot architecture** — pre-process the EXPLAIN into a small operator-cost summary (top-3 by `bytesAssigned`) before sending to the LLM, since the bottleneck is parseability, not reasoning. |

---

## M3 — LLM rewrite is equivalent and meaningfully cheaper

| Field | Value |
| --- | --- |
| **Assumption** | Vanilla Claude (no fine-tuning, no warehouse-stats injection) can produce a SQL rewrite that returns the same row set as the original on a held-out fixture AND reduces `bytesAssigned` by ≥30%, on a useful fraction of expensive queries. |
| **Gate** | On the 5 fixtures: rewrite returns equivalent rows (`rows_equal_unordered`) on **≥4/5**, AND ≥30% cost reduction on **≥3/5** of those equivalent rewrites. |
| **Result** | _PENDING_ — driven by the same SUMMARY block; specifically the per-fixture `m3=...` and `savings=...` lines. |
| **Learning** | _PENDING_ — the high-signal sub-questions: (a) does the LLM ever silently change semantics (drop a NULL handling, add an implicit DISTINCT)? (b) are the wins concentrated in one query class — e.g. only the predicate-pushdown cases — leaving cross-joins and OR-joins unaddressed? (c) does it occasionally propose a "rewrite" that is the same query? |
| **Pivot** | _PENDING_ — if M3 clears: build, but ship with an explicit "the rewriter declines if it's not confident" path; the spike already supports `rewrite: null`. If only the predicate-pushdown class wins: **pivot narrative** — sell the product as "Claude catches your forgotten WHERE filters" rather than "general join rewriter," and gate the LLM behind a query-class classifier. If equivalence fails repeatedly: **stop**, or pivot to a *suggestion-only* mode that surfaces the rewrite to a human without auto-running it. |

---

## M4 — End-to-end IA is walkable without missing steps

| Field | Value |
| --- | --- |
| **Assumption** | The flow *Claude calls run_query → server detects expensive plan → server proposes a rewrite → user approves → server runs the chosen plan* can be described in flat text and walked across all 5 fixtures without `# TODO: figure out how this hands off` gaps. |
| **Gate** | Spike's interactive walk-through completes for all 5 fixtures with the consent prompt reading naturally each time, and the writer of the spike can answer: "is this one MCP tool with a confirmation field, or two MCP tools (propose then run)?" with a defensible answer on the basis of what they just walked. |
| **Result** | _PENDING_ — `python spike.py` (interactive). The decision lives in your head after walking it; record it here verbatim. |
| **Learning** | _PENDING_ — likely IA discoveries: (a) does the user ever want to see EXPLAIN for the *original* query before deciding? (b) what should happen if they decline the rewrite — run the original anyway, or abort? (c) where do retries / "regenerate the rewrite" live in MCP? Each of these is cheap to spot in `input()` and expensive to spot in production. |
| **Pivot** | _PENDING_ — most likely: a clarification on the MCP tool surface. Single tool `run_query(sql, allow_rewrite=True)` that returns a proposal-bearing response Claude must echo back is one shape; `propose_rewrite(sql)` + `run_approved_rewrite(rewrite_id)` is the other. Pick on the basis of what the walk-through felt like, not what reads cleanest in a design doc. Document the decision and the rejected alternative inline. |

---

## Should-hold risks (logged, not gated)

| ID | Risk | Mitigation |
| --- | --- | --- |
| S1 | EXPLAIN may incur warehouse-credit cost for very complex queries on a cold cache. | After first run, check the Snowflake usage view; if non-trivial, gate EXPLAIN behind a session-level cost cap. |
| S2 | Added latency (EXPLAIN + LLM + EXPLAIN + run) may break the "feels interactive" budget. | Time it during the spike. If >8s overhead, design a streaming progress channel into the MCP response shape. |
| S3 | Wide views or many-join queries may produce JSON EXPLAIN larger than the model's context budget when combined with the SQL and rewrite room. | The spike caps EXPLAIN payload at 60K chars; production needs a smarter summarizer for large plans. |
| S4 | Service-account RBAC may not compose cleanly with end-user identity. | Out-of-band — handled by infra, not the spike. |

---

## Side findings (fill in as you run)

Use this section for anything the gates don't cover — undocumented
EXPLAIN fields, SDK surprises, latency outliers, places the LLM
confidently lied. These are often more valuable than the gate result;
record them eagerly.

- (none yet — the spike has not been executed against real services)

---

## Decision

See `decision.md` next to this file. The decision logic is:

| M1 | M2 | M3 | M4 | Decision |
| --- | --- | --- | --- | --- |
| pass | pass | pass | pass | **Build** |
| pass | pass | partial (M3 wins on a single query class) | pass | **Pivot narrative** — ship as "forgotten-filter detector," not "general rewriter" |
| pass | fail | — | — | **Pivot architecture** — pre-summarize EXPLAIN before LLM ingestion |
| pass | pass | fail (equivalence breaks) | — | **Stop** auto-rewrite path; consider suggestion-only mode |
| fail | — | — | — | **Stop** — without MCP, there is no product |
| — | — | — | fail | **Pivot architecture** — re-shape the MCP tool surface based on what the walk-through proved natural, then re-spike M4 only |

This table is the spike's value: it lets us route the build off a
small empirical fact set, not a debate.
