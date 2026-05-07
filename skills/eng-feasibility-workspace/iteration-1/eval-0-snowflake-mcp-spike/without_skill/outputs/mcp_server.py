"""MCP server skeleton for Snowflake + LLM rewrite.

Exposes two tools:
  - query_warehouse(sql, max_rows): runs a SELECT, optionally rewriting via the
    LLM if the EXPLAIN plan looks expensive.
  - explain_only(sql): returns the EXPLAIN plan + a rewrite proposal without
    executing either query. Useful for "why is this slow?" analyst flows.

Stdio transport — wire this into Claude Desktop via mcp.json or test with
`npx @modelcontextprotocol/inspector python mcp_server.py`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import sqlglot
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from sqlglot import exp

from equivalence import check_equivalence
from rewriter import Rewriter
from snowflake_client import SnowflakeClient

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("snowflake-mcp")

server = Server("snowflake-mcp-spike")
_sf = SnowflakeClient()
_rewriter = Rewriter()


def _is_select(sql: str) -> bool:
    try:
        tree = sqlglot.parse_one(sql, read="snowflake")
    except sqlglot.errors.ParseError:
        return False
    # Accept SELECT, CTE-led queries, and set ops; reject DDL/DML.
    return isinstance(tree, (exp.Select, exp.With, exp.Union, exp.Intersect, exp.Except))


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="query_warehouse",
            description=(
                "Run a SELECT against the configured Snowflake warehouse. "
                "If the planner estimates the query will scan more than the "
                "configured threshold and contains a join, an LLM-proposed "
                "rewrite is generated and validated for equivalence; the "
                "cheaper of the two is executed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SELECT statement."},
                    "max_rows": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Cap on returned rows.",
                    },
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="explain_only",
            description=(
                "Return the Snowflake EXPLAIN plan and an LLM rewrite proposal "
                "without executing the query. Use this to debug expensive queries."
            ),
            inputSchema={
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    sql = arguments["sql"]
    if not _is_select(sql):
        return [TextContent(type="text", text="Refused: only SELECT/CTE queries are allowed.")]

    if name == "explain_only":
        return await _explain_only(sql)
    if name == "query_warehouse":
        max_rows = int(arguments.get("max_rows", 1000))
        return await _query_warehouse(sql, max_rows)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def _explain_only(sql: str) -> list[TextContent]:
    plan = await asyncio.to_thread(_sf.explain, sql)
    proposal = await asyncio.to_thread(_rewriter.maybe_rewrite, sql, plan)
    body = {
        "plan_summary": {
            "estimated_bytes_scanned": plan.estimated_bytes_scanned,
            "estimated_partitions": plan.estimated_partitions,
            "has_join": plan.has_join,
        },
        "proposal": {
            "skipped": proposal.skipped,
            "rewritten_sql": proposal.rewritten_sql,
            "rationale": proposal.rationale,
            "expected_savings": proposal.expected_savings,
        },
    }
    return [TextContent(type="text", text=json.dumps(body, indent=2))]


async def _query_warehouse(sql: str, max_rows: int) -> list[TextContent]:
    timeout = int(os.environ.get("QUERY_TIMEOUT_SECONDS", "60"))

    plan = await asyncio.to_thread(_sf.explain, sql)
    proposal = await asyncio.to_thread(_rewriter.maybe_rewrite, sql, plan)

    sql_to_run = sql
    rewrite_used = False
    equivalence_note = "rewrite skipped"

    if not proposal.skipped and proposal.rewritten_sql.strip() != sql.strip():
        eq = await asyncio.to_thread(
            check_equivalence,
            sql,
            proposal.rewritten_sql,
            runner=lambda q: _sf.execute(q, timeout_seconds=timeout),
        )
        equivalence_note = f"layer={eq.layer} equivalent={eq.equivalent} detail={eq.detail}"
        if eq.equivalent:
            # Only swap if the EXPLAIN of the rewrite actually scans less.
            new_plan = await asyncio.to_thread(_sf.explain, proposal.rewritten_sql)
            if new_plan.estimated_bytes_scanned < plan.estimated_bytes_scanned:
                sql_to_run = proposal.rewritten_sql
                rewrite_used = True
            else:
                equivalence_note += " (rewrite was equivalent but not cheaper; ignored)"
        else:
            log.warning("Rejected non-equivalent rewrite: %s", eq.detail)

    final_sql = f"SELECT * FROM ({sql_to_run}) LIMIT {max_rows}"
    rows = await asyncio.to_thread(_sf.execute, final_sql, timeout_seconds=timeout)

    body = {
        "rewrite_used": rewrite_used,
        "equivalence": equivalence_note,
        "row_count": len(rows),
        "rows": rows,
    }
    return [TextContent(type="text", text=json.dumps(body, indent=2, default=str))]


async def main() -> None:
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
