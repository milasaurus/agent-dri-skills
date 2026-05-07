# Snowflake MCP + LLM SQL Rewriter — Day-0 Spike

## What this spike is

A throwaway prototype to de-risk the production server before we commit headcount. It is **not** the production server. The goal is to answer four questions:

1. Can an MCP server expose a `query_warehouse` tool to Claude in a shape that's actually useful?
2. Can an LLM look at a Snowflake `EXPLAIN` plan and propose a semantically-equivalent rewrite that's measurably cheaper?
3. How do we prove the rewrite is equivalent (vs. silently returning wrong rows)?
4. What are the operational risks we'd hit on day 30 in prod?

Question 3 is the load-bearing one. If we can't cheaply prove equivalence, the whole feature is unsafe and we should not build the production version.

## What's in here

| File | Purpose |
|---|---|
| `mcp_server.py` | Runnable MCP server skeleton with two tools. Stdio transport. |
| `rewriter.py` | The rewrite loop: takes an EXPLAIN plan + SQL, calls Claude, returns a candidate rewrite + rationale. |
| `equivalence.py` | Three-layer equivalence check: parse-tree normalization, sample-based row-hash comparison, and a `WHERE 1=0` schema check. |
| `snowflake_client.py` | Thin Snowflake connector wrapper. Real code, gated on env vars. |
| `fixtures/expensive_join.sql` | Synthetic 4-table join that triggers the rewrite path. |
| `fixtures/explain_plan.json` | Captured Snowflake `EXPLAIN USING JSON` output for the above. Used so `test_rewriter.py` runs offline. |
| `fixtures/rewritten_expected.sql` | What a good rewrite looks like, for the harness to grade against. |
| `test_rewriter.py` | Offline test for the rewrite loop. Mocks Anthropic + Snowflake. |
| `pyproject.toml` | Deps. |
| `.env.example` | The credentials surface. |
| `RISKS.md` | What I'd flag before committing to build. **Read this before scoping.** |

## Run it (if creds were present)

```bash
uv sync
cp .env.example .env  # fill in creds
# Run the MCP server (stdio); wire it into Claude Desktop or test with mcp inspector
uv run python mcp_server.py
# Or just exercise the rewriter offline against the fixture:
uv run pytest test_rewriter.py -v
```

## What this spike does NOT cover

- AuthN/AuthZ — assumes a single warehouse-level service account. Real prod needs per-user OAuth or row-level policies.
- Caching — every call hits Snowflake fresh. Result-set caching and EXPLAIN-plan caching are obvious wins, deferred.
- Cost accounting — we'd need to attribute warehouse credits per MCP call.
- Streaming results — current shape returns the full result set in one MCP response. Fine for analyst queries, breaks for anything > a few MB.
- The rewriter only handles SELECT. DDL/DML are explicitly rejected.

## Headline finding

See `RISKS.md`. The short version: the rewrite loop works on the toy fixture, but **equivalence proof is the real product**, not the rewriter itself. Budget accordingly.
