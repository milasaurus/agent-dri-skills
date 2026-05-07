# Snowflake MCP + LLM SQL rewriter — assumptions

## Project frame

**What ships.** An MCP server Claude can connect to that exposes a
small set of tools over a read-only Snowflake warehouse. When Claude
issues a query, the server intercepts expensive plans (joins above a
cost threshold), asks an LLM to inspect the EXPLAIN output and propose
a cheaper rewrite, validates the rewrite is semantically equivalent,
and (with the user's consent) runs the rewrite instead.

**Who it serves.** Internal analysts and engineers who use Claude as a
front door to the warehouse and don't want to hand-tune SQL but also
don't want to pay for full table scans they didn't notice.

**Core hypothesis (one falsifiable sentence).** An LLM, given an
EXPLAIN plan and the original SQL, can produce a rewrite that (a)
returns the same result set on a held-out fixture and (b) reduces
Snowflake-reported plan cost by at least 30% on at least 3 of 5
deliberately-expensive queries.

If that hypothesis fails, the project's narrative ("we save you money
on accidentally-expensive joins") collapses — there is no point
shipping the MCP plumbing.

## Assumptions

Categorized **must-hold** / **should-hold** / **nice-if-it-holds**.
Must-hold items are the only ones the spike exercises end-to-end.

### Must-hold (project-killers if false)

#### M1. The MCP server can speak the protocol Claude expects, expose Snowflake-shaped tools, and round-trip a real query.

- **Why it kills the project if false.** Without a working MCP
  contract, there is nothing to extend. The rewriter is moot if Claude
  can't reach the warehouse through us in the first place.
- **What's actually uncertain.** The team has not shipped on MCP
  before. Two specific shapes are unknown: (1) does an MCP tool
  result fit a Snowflake row set without serialization gymnastics —
  decimals, timestamps, NULLs — and (2) how do we expose the
  rewrite-confirmation step (a tool that prompts the user mid-flow,
  vs. two separate tools).
- **Gate.** With `mcp` (the Python SDK) running over stdio, a synthetic
  client can call a `run_query` tool, get back rows for 5 hand-picked
  Snowflake-shaped fixtures (incl. NULLs, NUMERIC, TIMESTAMP_TZ,
  VARIANT/JSON), and the IA for the rewrite-confirmation handoff is
  walked end-to-end in the spike's CLI without any "and then magic
  happens" steps.

#### M2. Snowflake's EXPLAIN output is structured enough that an LLM can identify the expensive operator and propose a rewrite.

- **Why it kills the project if false.** The whole rewriter loop
  depends on the LLM having signal to act on. If EXPLAIN comes back as
  unstructured prose, or if the cost numbers aren't there, the LLM is
  guessing.
- **What's actually uncertain.** Snowflake has multiple EXPLAIN modes
  (`EXPLAIN`, `EXPLAIN USING TEXT`, `EXPLAIN USING JSON`,
  `EXPLAIN USING TABULAR`). We don't know which one carries
  per-operator partition counts and bytes-scanned in a form the LLM
  can reason about, and whether the JSON shape is stable enough to
  feed in raw.
- **Gate.** For 5 hand-picked expensive queries (cross-joins,
  unfiltered fact-table scans, function-on-key joins,
  too-late-filter, missing cluster pruning), the LLM, given EXPLAIN
  output + the SQL, names the dominant expensive operator correctly
  in 4 of 5 cases. ("Correctly" = the operator I would name as a
  human reviewer; pre-recorded answer key in the spike.)

#### M3. The LLM-proposed rewrite is semantically equivalent to the original on a held-out fixture and meaningfully cheaper.

- **Why it kills the project if false.** A rewriter that returns
  different rows is worse than no rewriter — it silently corrupts
  analysis. A rewriter that returns the same rows but doesn't actually
  save anything is a tax. Either failure mode kills the pitch.
- **What's actually uncertain.** Whether off-the-shelf Claude (no
  fine-tuning, no schema-aware indexing, just EXPLAIN + SQL + a
  one-shot system prompt) clears both bars at once. Many LLM-SQL
  papers show one or the other; the join-rewrite literature is thin.
- **Gate.** On 5 hand-picked expensive queries with golden result
  sets, the rewrite (a) returns a row set equal to the golden set
  modulo ordering for ≥4/5 cases AND (b) reports a Snowflake plan
  cost reduction of ≥30% (estimated bytes scanned, partitions
  scanned, or `EXPLAIN`'s `bytes` field — whichever proves
  load-bearing) for ≥3/5 of the equivalent rewrites.

#### M4. The end-to-end IA — *Claude calls run_query → server detects expensive plan → server asks user to approve a rewrite → server runs the chosen plan* — is walkable without a missing step.

- **Why it kills the project if false.** The rewriter is a
  user-in-the-loop feature: somebody has to say "yes, run the cheaper
  version." If we can't describe that handoff in flat text inside the
  spike, we will not be able to describe it in MCP either, and the
  product becomes "trust the LLM to silently rewrite your SQL," which
  is a different (worse) product.
- **What's actually uncertain.** Whether the consent step lives inside
  one tool call (server returns a structured "proposed_rewrite" object
  Claude has to confirm) or across two (`propose_rewrite` then
  `run_approved_rewrite`). The choice changes the MCP surface.
- **Gate.** The spike's CLI walks the full flow with `input()` prompts
  standing in for Claude/the user, including the consent step, on
  all 5 fixtures, with no `# TODO: figure out how this hands off`
  comments left behind. The single-tool vs two-tool decision is made
  on the basis of which one the spike proves natural, not on
  speculation.

### Should-hold (architecture changes if false, project survives)

- **S1. EXPLAIN can be obtained without warehouse credit charges
  beyond compile-time.** Snowflake docs say `EXPLAIN` doesn't run the
  query; verify on real bill. If false, we may need to gate
  EXPLAIN-fetching behind a cost budget. Logged as risk; not spiked.
- **S2. End-to-end latency budget.** EXPLAIN + Claude + rewrite-EXPLAIN
  + run should add <8s of overhead vs. running the original query
  blind. Logged. Measured opportunistically during the spike but not
  gated — failure here changes UX (sync vs async progress), not
  viability.
- **S3. JSON EXPLAIN output for production-shaped queries fits in
  Claude's context window with room for the SQL and rewrite.** We
  expect yes for queries up to ~15 joins; a multi-hundred-table
  warehouse view might blow the budget. Logged.
- **S4. Snowflake's role-based access control composes cleanly with a
  service account that the MCP server uses.** Standard pattern; not
  spiked.

### Nice-if-it-holds (don't spike)

- **N1.** The LLM can also suggest cluster keys / search optimization
  / materialized views, not just rewrites.
- **N2.** Multi-warehouse routing (run on a cheap warehouse for small
  queries, scale up for big ones).
- **N3.** A rewrite-cache so identical queries skip the LLM call.
- **N4.** Pretty diff rendering of original vs. rewritten SQL in the
  Claude transcript.

## Time-box

One day. Two if M2 (EXPLAIN parseability) returns surprises that
require trying multiple EXPLAIN modes. If we are still spiking on day
3, reset and decide between (a) narrowing to a single query class or
(b) escalating the EXPLAIN-shape question to a docs/Snowflake support
question rather than empirics.
