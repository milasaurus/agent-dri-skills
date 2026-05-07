"""LLM-driven SQL rewrite loop.

Given a SQL statement and its Snowflake EXPLAIN plan, ask Claude to propose a
semantically-equivalent rewrite that should be cheaper. The LLM's output is
always treated as untrusted — equivalence.py is what makes this safe.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from anthropic import Anthropic

from snowflake_client import ExplainPlan


REWRITER_SYSTEM_PROMPT = """\
You are a Snowflake query optimizer. You receive a SQL query and its EXPLAIN
plan. Propose a rewrite that returns the IDENTICAL result set but should scan
fewer bytes or partitions.

Hard rules:
  1. The rewrite must be semantically equivalent — same columns, same rows,
     same ordering semantics.
  2. Do not invent columns, tables, or filters that aren't in the original.
  3. If you can't confidently improve the query, return the original verbatim
     and explain why in the rationale.
  4. Output strict JSON: {"rewritten_sql": "...", "rationale": "...",
     "expected_savings": "low" | "medium" | "high"}.
  5. No DDL, no DML. SELECT only.

Common Snowflake-specific moves to consider:
  - Push filters below joins (predicate pushdown the planner missed).
  - Replace SELECT * with explicit columns when downstream uses few.
  - Convert correlated subqueries to JOINs or QUALIFY clauses.
  - Add cluster-key-aligned filters when the EXPLAIN shows full table scans.
  - Convert OR-on-different-columns to UNION ALL when it enables pruning.
"""


@dataclass
class RewriteProposal:
    original_sql: str
    rewritten_sql: str
    rationale: str
    expected_savings: str  # "low" | "medium" | "high"
    skipped: bool = False


class Rewriter:
    def __init__(self, *, client: Anthropic | None = None, model: str | None = None) -> None:
        self._client = client or Anthropic()
        self._model = model or os.environ.get("REWRITER_MODEL", "claude-opus-4-5")

    def maybe_rewrite(self, sql: str, plan: ExplainPlan) -> RewriteProposal:
        threshold = int(os.environ.get("REWRITER_COST_THRESHOLD_BYTES", "1073741824"))
        if plan.estimated_bytes_scanned < threshold or not plan.has_join:
            return RewriteProposal(
                original_sql=sql,
                rewritten_sql=sql,
                rationale=(
                    f"Skipped: plan estimates {plan.estimated_bytes_scanned} bytes "
                    f"(threshold {threshold}) or no join present."
                ),
                expected_savings="low",
                skipped=True,
            )
        return self._call_llm(sql, plan)

    def _call_llm(self, sql: str, plan: ExplainPlan) -> RewriteProposal:
        user_msg = json.dumps(
            {
                "original_sql": sql,
                "explain_plan": plan.raw,
                "plan_summary": {
                    "bytes_scanned": plan.estimated_bytes_scanned,
                    "partitions": plan.estimated_partitions,
                },
            },
            indent=2,
        )
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=REWRITER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        parsed = _extract_json(text)
        return RewriteProposal(
            original_sql=sql,
            rewritten_sql=parsed["rewritten_sql"],
            rationale=parsed.get("rationale", ""),
            expected_savings=parsed.get("expected_savings", "low"),
            skipped=False,
        )


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict:
    """Tolerate the LLM wrapping JSON in prose or fences."""
    match = _JSON_BLOCK.search(text)
    if not match:
        raise ValueError(f"Rewriter output did not contain JSON: {text!r}")
    return json.loads(match.group(0))
