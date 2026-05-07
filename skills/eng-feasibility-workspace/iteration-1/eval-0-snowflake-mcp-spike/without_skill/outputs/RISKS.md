# Risks & open questions before committing to build

This memo is the actual deliverable of the spike. The code in this folder
demonstrates the loop is *constructible*; the items below are why I'd push
back on going straight to a production-server scope.

## 1. Equivalence is the product, not the rewriter

The rewrite loop took half a day to wire up. The equivalence harness is the
hard part, and the version in `equivalence.py` is **not strong enough for
production**:

- Sample-based row hashing is probabilistic. An LLM rewrite that drops a
  filter affecting 0.1% of rows can pass a 1k-row sample easily.
- The `LIMIT N` wrapper imposes a `ORDER BY 1` that may not be deterministic
  when column 1 has duplicates. Two semantically-equivalent queries can hash
  differently here.
- `WHERE 1=0` schema check uses Python type names as a proxy for SQL types.
  This collapses `NUMBER(10,2)` and `NUMBER(38,0)` into both being `Decimal`,
  which we should not consider equivalent.

**Better approaches to evaluate before building**:
- Snowflake's `RESULT_SCAN` + `HASH_AGG` over the full result set, run in the
  background. Costs warehouse credits but is the only way to get certainty.
- Run both queries in a transaction and `EXCEPT` them both ways. Cheap to
  describe, expensive to run on large outputs.
- A pinned eval set of (original, expected_rewrite, gold_result_hash) triples
  — graded weekly, not per-call.

I would not let this feature execute the rewrite path on a production
warehouse without one of the above.

## 2. Latency budget

A "fast" Claude call is ~1–3s. Snowflake `EXPLAIN` is ~100–500ms. The naive
flow is:
  EXPLAIN (500ms) -> Claude (2s) -> equivalence EXPLAIN x2 (1s) ->
  equivalence sample x2 (queryable) -> EXPLAIN of rewrite (500ms) -> execute.

That's a floor of ~4–5s before any data comes back, and the equivalence
sample queries themselves cost real warehouse time. For interactive analyst
flows this is borderline acceptable; for any agentic loop (Claude calling
the tool 10x in a session) it's not.

**Mitigation candidates**: cache (sql_hash, plan_hash) → rewrite proposal;
only run equivalence once per (original, rewritten) pair ever, not per call.

## 3. Cost of the safety net

The equivalence sample queries scan real data. If the rewriter triggers
on a 6 GiB query (our threshold), the sample queries will scan ~tens of MiB
each — cheap, but real. At sustained load this is non-trivial.

**Open question**: do we want to bill the equivalence checks against the
rewriter's "savings" budget? If a rewrite saves 4 GiB but the safety net
costs 200 MiB, net savings is 3.8 GiB. Fine. If a rewrite saves 4 GiB but
the safety net costs 5 GiB because the sample query has its own hidden
join, we've made things worse.

## 4. Scope of `EXPLAIN USING JSON` parsing

`snowflake_client.ExplainPlan.from_json` walks the plan tree heuristically.
Snowflake doesn't document the JSON schema as stable across versions; the
extraction in `_walk_for_op` will silently miss new operator names. The
`bytesAssigned` / `partitionsAssigned` extraction is also approximate —
those fields show up at multiple levels of the plan and we're only reading
the global stats.

**Recommendation**: do not ship without a regression test suite of captured
EXPLAIN plans across Snowflake versions, or pin the warehouse version.

## 5. Authn/Authz model

Spike uses one service account. Production needs to:
- Run queries *as the calling user* so RBAC + row-access policies apply.
  Otherwise the MCP server becomes a confused-deputy that exfiltrates data
  from tables the user can't access directly.
- Decide whether the rewriter sees the SQL (it does — it's in the prompt)
  and whether that's allowed under data-classification policy. If the SQL
  contains literal PII filters, that PII goes to Anthropic.

The auth design is at least a week of work that the spike doesn't touch.

## 6. Failure modes when the LLM "helps too much"

Observed in similar systems: the model returns a rewrite that adds a
`DISTINCT` because the rationale text says "ensure no dupes," even though
the original query was fine without it. AST normalize won't catch this; row
sample might catch it but only if the original happened to have duplicate
rows in the sample.

**Mitigation**: the prompt explicitly forbids it ("do not invent filters")
and the `expected_savings: low` path should prefer the original. We should
also blocklist `DISTINCT`, `LIMIT`, `ORDER BY` *additions* in a sqlglot diff
pass — flag any additive change for human review.

## 7. What I'd build instead, if I were grading the proposal

A Snowflake MCP server *without* the rewriter is straightforward and high
value — analysts already want this. Ship that in week 1.

The rewriter as a **separate** offline tool that takes a query history,
proposes rewrites, and submits them as PRs against a dbt repo (where they'd
be reviewed by humans and tested by CI) is a much safer first version of
this idea. The "rewrite at query time" version is week 6+, after we have
real telemetry on which queries even matter.

## 8. What this spike successfully de-risked

- MCP tool surface fits cleanly. Two tools is enough.
- `EXPLAIN USING JSON` is parseable in practice for common queries.
- The cost-threshold gate prevents the rewriter from being called on cheap
  queries — important for both latency and Anthropic spend.
- AST-level equivalence catches the trivial cases for free.

## 9. Recommendation

**Yellow light.** Ship the read-only MCP server (no rewriter) in 1–2 weeks.
Run a 4-week parallel investigation on the equivalence problem with a real
eval set before scoping the rewriter as a production feature. Revisit this
memo once that data exists.
