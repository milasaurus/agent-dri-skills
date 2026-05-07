"""snowflake-mcp-rewriter spike — does the LLM-rewrite loop work?

Validates the four must-hold assumptions in `assumptions.md`:

  M1. MCP server round-trips a Snowflake query under the protocol.
  M2. Snowflake EXPLAIN is structured enough for an LLM to act on.
  M3. LLM-proposed rewrite is semantically equivalent and cheaper.
  M4. The user-in-the-loop IA is walkable end-to-end.

This is the apparatus, not the product. One file on purpose.

Run:

    uv pip install snowflake-connector-python anthropic mcp
    export SNOWFLAKE_ACCOUNT=...
    export SNOWFLAKE_USER=...
    export SNOWFLAKE_PASSWORD=...        # or SNOWFLAKE_PRIVATE_KEY_PATH
    export SNOWFLAKE_WAREHOUSE=...
    export SNOWFLAKE_DATABASE=...
    export SNOWFLAKE_SCHEMA=...
    export ANTHROPIC_API_KEY=...
    python spike.py                      # interactive walk-through
    python spike.py --case 2             # one-shot on fixture #2
    python spike.py --mcp-server         # run as an MCP server over stdio
                                         # (sanity check for M1)

This script does NOT run if the env vars above are missing — that is
intentional. The spike is real services or nothing; mocks would
defeat the point. See `tradeoffs.md` for what each run validated.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

# We import the SDKs at the top, but tolerate them being missing so
# the file can be syntax-checked / read in environments without
# credentials. The actual run paths below will fail fast if the SDKs
# aren't installed.
try:
    import snowflake.connector  # type: ignore[import-untyped]
except ImportError:
    snowflake = None  # type: ignore[assignment]

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore[assignment,misc]

try:
    # mcp.server.stdio is the official Python MCP SDK transport.
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.server.stdio import stdio_server  # type: ignore[import-untyped]
    from mcp.types import TextContent, Tool  # type: ignore[import-untyped]
except ImportError:
    Server = None  # type: ignore[assignment,misc]


ANTHROPIC_MODEL = os.environ.get(
    "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"
)

# ---------------------------------------------------------------------------
# Hand-picked fixtures. Each is a deliberately-expensive Snowflake query
# against the standard SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 schema, which every
# Snowflake account has read access to by default — that is on purpose
# so this file is portable across accounts.
#
# Each fixture comes with my own answer key (the operator I would name
# as the dominant expense) so the M2 gate is checkable without a human
# in the loop on rerun.
# ---------------------------------------------------------------------------


@dataclass
class Fixture:
    name: str
    sql: str
    # The operator I'd flag as dominant if I read the EXPLAIN myself.
    # Used as the answer key for M2.
    expected_dominant_operator: str
    # Free-text hint about what makes this expensive. Not used by the
    # LLM — purely for the spike's print output.
    note: str


FIXTURES: list[Fixture] = [
    Fixture(
        name="cross_join_no_predicate",
        sql=(
            "SELECT n.n_name, r.r_name "
            "FROM snowflake_sample_data.tpch_sf1.nation n, "
            "     snowflake_sample_data.tpch_sf1.region r "
            "WHERE n.n_regionkey + 0 = r.r_regionkey"
        ),
        expected_dominant_operator="Join",
        note="function on join key disables hash-join optimization",
    ),
    Fixture(
        name="unfiltered_fact_scan",
        sql=(
            "SELECT l_orderkey, SUM(l_extendedprice) "
            "FROM snowflake_sample_data.tpch_sf1.lineitem "
            "GROUP BY l_orderkey"
        ),
        expected_dominant_operator="TableScan",
        note="full lineitem scan; no date filter",
    ),
    Fixture(
        name="late_filter_after_join",
        sql=(
            "SELECT o.o_orderkey, c.c_name "
            "FROM snowflake_sample_data.tpch_sf1.orders o "
            "JOIN snowflake_sample_data.tpch_sf1.customer c "
            "  ON o.o_custkey = c.c_custkey "
            "WHERE o.o_orderdate >= '1998-01-01'"
        ),
        expected_dominant_operator="Join",
        note="filter could be pushed below the join",
    ),
    Fixture(
        name="select_star_then_count",
        sql=(
            "SELECT COUNT(*) FROM ("
            "  SELECT * FROM snowflake_sample_data.tpch_sf1.lineitem "
            "  WHERE l_shipdate BETWEEN '1995-01-01' AND '1995-12-31'"
            ") t"
        ),
        expected_dominant_operator="TableScan",
        note="materializes all columns just to count rows",
    ),
    Fixture(
        name="cartesian_via_or",
        sql=(
            "SELECT s.s_name, p.p_name "
            "FROM snowflake_sample_data.tpch_sf1.supplier s "
            "JOIN snowflake_sample_data.tpch_sf1.partsupp ps "
            "  ON s.s_suppkey = ps.ps_suppkey OR s.s_nationkey = ps.ps_partkey "
            "JOIN snowflake_sample_data.tpch_sf1.part p "
            "  ON ps.ps_partkey = p.p_partkey"
        ),
        expected_dominant_operator="Join",
        note="OR in join predicate forces cartesian-shaped expansion",
    ),
]


# ---------------------------------------------------------------------------
# Snowflake helpers — connect, EXPLAIN, run.
# ---------------------------------------------------------------------------


def _require_env(*keys: str) -> None:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        sys.exit(f"missing required env var(s): {', '.join(missing)}")


def connect_snowflake() -> Any:
    if snowflake is None:
        sys.exit("snowflake-connector-python not installed")
    _require_env("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_WAREHOUSE")
    if not (
        os.environ.get("SNOWFLAKE_PASSWORD")
        or os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    ):
        sys.exit("set SNOWFLAKE_PASSWORD or SNOWFLAKE_PRIVATE_KEY_PATH")
    kwargs: dict[str, Any] = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ.get("SNOWFLAKE_DATABASE", "SNOWFLAKE_SAMPLE_DATA"),
        "schema": os.environ.get("SNOWFLAKE_SCHEMA", "TPCH_SF1"),
        # Force a session role if the user supplied one — keeps ACL
        # surprises out of the spike.
        "role": os.environ.get("SNOWFLAKE_ROLE"),
    }
    if os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH"):
        with open(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], "rb") as f:
            kwargs["private_key"] = f.read()
    else:
        kwargs["password"] = os.environ["SNOWFLAKE_PASSWORD"]
    return snowflake.connector.connect(**{k: v for k, v in kwargs.items() if v})


def explain_json(conn: Any, sql: str) -> dict:
    """Return Snowflake's JSON EXPLAIN for `sql`.

    We use `EXPLAIN USING JSON` because the JSON shape is what we want
    to feed to the LLM — the tabular form is for humans. M2 hinges on
    whether this output carries per-operator costs in a form the LLM
    can reason about. This helper exists so the spike can answer that
    empirically rather than from the docs.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"EXPLAIN USING JSON {sql}")
        row = cur.fetchone()
        # The JSON document is in the first (and only) column of the
        # first (and only) row, as a string. Probe shape by printing
        # the top-level keys the first time we see one.
        raw = row[0] if not isinstance(row, dict) else next(iter(row.values()))
        return json.loads(raw)
    finally:
        cur.close()


def run_query(conn: Any, sql: str, row_limit: int = 1000) -> list[tuple]:
    """Run `sql`, return rows. Coerces Decimals/datetimes to JSON-safe
    types so M1's serialization probe tells us something real.

    Note the LIMIT wrapping: the spike runs against expensive queries
    on purpose, but actually pulling the full result over the wire
    isn't what we're measuring. We want enough rows to compare set
    equality against a held-out golden, no more.
    """
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM ({sql}) LIMIT {row_limit}")
        return [_jsonable_row(r) for r in cur.fetchall()]
    finally:
        cur.close()


def _jsonable_row(row: tuple) -> tuple:
    """Coerce a Snowflake row into JSON-serializable values.

    This is here for M1: we need to know what shapes the MCP layer
    will see. If we can't serialize a Snowflake row to JSON, the MCP
    `TextContent` return path is blocked.
    """
    out = []
    for cell in row:
        if isinstance(cell, Decimal):
            out.append(str(cell))
        elif hasattr(cell, "isoformat"):
            out.append(cell.isoformat())
        elif isinstance(cell, (bytes, bytearray)):
            out.append(cell.hex())
        else:
            out.append(cell)
    return tuple(out)


def plan_cost_metric(explain: dict) -> float:
    """Pull a single cost number out of a JSON EXPLAIN.

    Snowflake's JSON EXPLAIN puts per-operator stats under
    `GlobalStats` / per-step `objects[i].partitionsAssigned` /
    `bytes`. We pick `bytesAssigned` as the headline cost metric
    (proxy for $$ scanned) and fall back to row count if absent.
    The shape is the unknown M2 has to confirm — so this function
    prints what it found the first time it's called.
    """
    gs = explain.get("GlobalStats", {}) or {}
    if "bytesAssigned" in gs:
        return float(gs["bytesAssigned"])
    if "partitionsAssigned" in gs:
        return float(gs["partitionsAssigned"])
    # Fall back to summing per-step bytes if GlobalStats is absent.
    total = 0.0
    for step in explain.get("Operations", []) or []:
        for op in step.get("Operations", []) or []:
            stats = op.get("ExpressionProperties", {}) or {}
            total += float(stats.get("bytes", 0) or 0)
    return total


# ---------------------------------------------------------------------------
# LLM rewriter.
# ---------------------------------------------------------------------------


REWRITE_SYSTEM = """You are a Snowflake SQL rewriter. Given a SQL query
and its JSON EXPLAIN plan, your job is to:

1. Identify the single dominant expensive operator in the plan
   (Join / TableScan / Filter / Aggregate / Sort / WindowFunction).
2. Propose a rewrite of the SQL that reduces the cost of that
   operator while returning the SAME result set (modulo row order).
3. Explain in one sentence why the rewrite is cheaper.

Hard rules:
- The rewrite must return the same columns, in the same order, with
  the same types, as the original.
- Do NOT change aggregation semantics. Do NOT add LIMIT. Do NOT drop
  filters or joins.
- If you can't find a safe rewrite, set "rewrite" to null and explain
  why.

Respond as a single JSON object with keys:
  dominant_operator: string,
  rationale:         string (one sentence),
  rewrite:           string | null   (the new SQL, or null)
"""


@dataclass
class RewriteProposal:
    dominant_operator: str
    rationale: str
    rewrite: str | None
    raw: str  # for debugging: the LLM's full text response


def propose_rewrite(client: Any, sql: str, explain: dict) -> RewriteProposal:
    """Ask Claude to propose a rewrite. Real call, no mocks.

    The system prompt above is the entire 'prompt engineering' the
    spike does. Production would do more (few-shot examples, schema
    context, table-stats hints), but the M3 gate is whether the
    *vanilla* version clears the bar. If it does, we know more
    investment is worth it; if it doesn't, we know more investment
    might rescue it but we're not guessing in the dark anymore.
    """
    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        system=REWRITE_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"SQL:\n{sql}\n\n"
                    f"JSON EXPLAIN:\n{json.dumps(explain, indent=2)[:60000]}"
                ),
            }
        ],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
    # Be permissive about JSON extraction — the spike is testing the
    # behavior, not the parsing.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return RewriteProposal("?", "no JSON in response", None, text)
    payload = json.loads(text[start : end + 1])
    return RewriteProposal(
        dominant_operator=payload.get("dominant_operator", "?"),
        rationale=payload.get("rationale", ""),
        rewrite=payload.get("rewrite"),
        raw=text,
    )


# ---------------------------------------------------------------------------
# Equivalence check (M3).
# ---------------------------------------------------------------------------


def rows_equal_unordered(a: list[tuple], b: list[tuple]) -> bool:
    """Set equality on rows, ignoring order. Tuples are hashable iff
    every cell is — _jsonable_row above guarantees that."""
    try:
        return sorted(a) == sorted(b)
    except TypeError:
        # If sorting fails (e.g. mixed None/str), compare as
        # multisets via repr — slow but correct on the small fixture
        # sizes we care about.
        return sorted(map(repr, a)) == sorted(map(repr, b))


# ---------------------------------------------------------------------------
# MCP server (M1 sanity probe).
#
# This is NOT the production server — it's a one-screen probe that
# proves the MCP wire protocol can carry a Snowflake row set. If `python
# spike.py --mcp-server` starts and a synthetic client (e.g. the
# Inspector) can call `run_query`, M1's "the protocol fits our shape"
# question is answered yes.
# ---------------------------------------------------------------------------


def serve_mcp() -> None:
    if Server is None:
        sys.exit("mcp SDK not installed; pip install mcp")
    import asyncio

    server = Server("snowflake-rewriter-spike")
    conn = connect_snowflake()

    @server.list_tools()  # type: ignore[misc]
    async def list_tools() -> list[Any]:
        return [
            Tool(
                name="run_query",
                description="Run a read-only SQL query against Snowflake.",
                inputSchema={
                    "type": "object",
                    "properties": {"sql": {"type": "string"}},
                    "required": ["sql"],
                },
            ),
            Tool(
                name="explain_query",
                description="Return Snowflake's JSON EXPLAIN for a query.",
                inputSchema={
                    "type": "object",
                    "properties": {"sql": {"type": "string"}},
                    "required": ["sql"],
                },
            ),
        ]

    @server.call_tool()  # type: ignore[misc]
    async def call_tool(name: str, arguments: dict) -> list[Any]:
        sql = arguments["sql"]
        if name == "run_query":
            rows = run_query(conn, sql, row_limit=50)
            return [TextContent(type="text", text=json.dumps(rows, default=str))]
        if name == "explain_query":
            return [
                TextContent(
                    type="text", text=json.dumps(explain_json(conn, sql), default=str)
                )
            ]
        raise ValueError(f"unknown tool: {name}")

    async def _run() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Walk-through: the IA probe.
#
# This is the part of the spike that surfaces M4 problems. Each step
# is a thing the user has to do or be told. If a step here reads as
# "and then magic happens," the IA has a hole.
# ---------------------------------------------------------------------------


def walk_one(conn: Any, claude: Any, fx: Fixture, *, interactive: bool) -> dict:
    print("=" * 72)
    print(f"Fixture: {fx.name}")
    print(f"Note:    {fx.note}")
    print("-" * 72)
    print(f"SQL:\n{fx.sql}\n")

    t0 = time.monotonic()
    explain = explain_json(conn, fx.sql)
    t_explain = time.monotonic() - t0
    cost_before = plan_cost_metric(explain)
    print(f"[{t_explain:.2f}s] EXPLAIN top-level keys: {list(explain.keys())}")
    print(f"        plan cost (bytesAssigned): {cost_before:,.0f}")

    t0 = time.monotonic()
    proposal = propose_rewrite(claude, fx.sql, explain)
    t_llm = time.monotonic() - t0
    print(f"[{t_llm:.2f}s] LLM dominant_operator: {proposal.dominant_operator!r}")
    print(f"        expected:              {fx.expected_dominant_operator!r}")
    print(f"        rationale: {proposal.rationale}")
    print()

    m2_pass = (
        proposal.dominant_operator.lower()
        == fx.expected_dominant_operator.lower()
    )

    if proposal.rewrite is None:
        print("LLM declined to rewrite. M3 is a fail for this fixture.")
        return {
            "fixture": fx.name,
            "m2_pass": m2_pass,
            "m3_pass": False,
            "cost_before": cost_before,
            "cost_after": None,
            "rows_equal": None,
            "savings_pct": None,
        }

    print(f"Proposed rewrite:\n{proposal.rewrite}\n")

    # User-in-the-loop step. THIS is the IA probe (M4): we are
    # standing in for what Claude+the user would do across MCP. If
    # this prompt reads naturally, the production handoff probably
    # will too. If it doesn't, we caught it on day 0.
    if interactive:
        ans = input("Run the rewrite? [y/N/o=run original instead] ").strip().lower()
    else:
        ans = "y"
    if ans == "o":
        print("(Skipping — user chose original.)")
        return {
            "fixture": fx.name,
            "m2_pass": m2_pass,
            "m3_pass": None,
            "cost_before": cost_before,
            "cost_after": None,
            "rows_equal": None,
            "savings_pct": None,
        }
    if ans not in ("y", "yes"):
        print("(Skipping — user said no.)")
        return {
            "fixture": fx.name,
            "m2_pass": m2_pass,
            "m3_pass": None,
            "cost_before": cost_before,
            "cost_after": None,
            "rows_equal": None,
            "savings_pct": None,
        }

    # Run both versions, compare result sets (M3 part 1) and plan
    # cost (M3 part 2).
    rows_orig = run_query(conn, fx.sql)
    rows_rewrite = run_query(conn, proposal.rewrite)
    rows_equal = rows_equal_unordered(rows_orig, rows_rewrite)
    explain_after = explain_json(conn, proposal.rewrite)
    cost_after = plan_cost_metric(explain_after)
    savings = (
        (cost_before - cost_after) / cost_before if cost_before > 0 else 0.0
    )

    print(f"rows equal (modulo order): {rows_equal}")
    print(f"plan cost before:          {cost_before:,.0f}")
    print(f"plan cost after:           {cost_after:,.0f}")
    print(f"savings:                   {savings:.0%}")

    return {
        "fixture": fx.name,
        "m2_pass": m2_pass,
        "m3_pass": rows_equal and savings >= 0.30,
        "cost_before": cost_before,
        "cost_after": cost_after,
        "rows_equal": rows_equal,
        "savings_pct": savings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, default=None, help="run a single fixture by index")
    parser.add_argument("--no-interactive", action="store_true", help="auto-approve rewrites")
    parser.add_argument("--mcp-server", action="store_true", help="run as an MCP stdio server (M1)")
    args = parser.parse_args()

    if args.mcp_server:
        serve_mcp()
        return

    if Anthropic is None:
        sys.exit("anthropic SDK not installed")
    _require_env("ANTHROPIC_API_KEY")

    conn = connect_snowflake()
    claude = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    cases = [FIXTURES[args.case]] if args.case is not None else FIXTURES
    results = [
        walk_one(conn, claude, fx, interactive=not args.no_interactive)
        for fx in cases
    ]

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    m2_hits = sum(1 for r in results if r["m2_pass"])
    m3_hits = sum(1 for r in results if r["m3_pass"])
    print(f"M2 (operator named correctly): {m2_hits}/{len(results)}  (gate: 4/5)")
    print(f"M3 (equivalent + ≥30% cheaper): {m3_hits}/{len(results)}  (gate: 3/5)")
    for r in results:
        print(f"  - {r['fixture']}: m2={r['m2_pass']}  m3={r['m3_pass']}  "
              f"savings={r['savings_pct']!r}")
    print()
    print("Now write findings into tradeoffs.md. Don't trust scrollback.")


if __name__ == "__main__":
    main()
