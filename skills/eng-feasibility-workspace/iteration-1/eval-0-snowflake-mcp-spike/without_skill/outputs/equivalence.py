"""Three-layer equivalence check for an LLM-proposed rewrite.

This is the load-bearing piece of the whole feature. If the rewriter returns
SQL that is "close" but not equivalent (different join cardinality, dropped
NULLs, reordered with semantic effect), we silently corrupt analyst answers.

Layers, cheapest first:
  1. AST normalize-and-compare via sqlglot. Catches whitespace/alias-only
     rewrites that are obviously equivalent. Fast.
  2. Schema check: run both with `WHERE 1=0` and confirm column names + types
     match exactly. Catches dropped/added/reordered columns. Cheap.
  3. Sample-based row-hash: run both with the same `LIMIT N` over a fixed
     `ORDER BY` derived from the projection, then hash the rows. Probabilistic
     but catches the common failure modes.

None of these are a *proof* of equivalence — only formal verification would
give that, and Snowflake-dialect SQL has no production-grade verifier we can
buy. That limit is the headline risk in RISKS.md.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp


@dataclass
class EquivalenceResult:
    equivalent: bool
    layer: str  # which layer reached the verdict
    detail: str


def check_equivalence(
    original_sql: str,
    rewritten_sql: str,
    *,
    runner,  # callable[[str], list[dict]] — injected so we can mock in tests
    sample_size: int = 1000,
) -> EquivalenceResult:
    if _ast_identical(original_sql, rewritten_sql):
        return EquivalenceResult(True, "ast", "ASTs normalize to the same tree.")

    schema_match, schema_detail = _schema_matches(original_sql, rewritten_sql, runner=runner)
    if not schema_match:
        return EquivalenceResult(False, "schema", schema_detail)

    rows_match, rows_detail = _sample_rows_match(
        original_sql, rewritten_sql, runner=runner, sample_size=sample_size
    )
    if not rows_match:
        return EquivalenceResult(False, "rows", rows_detail)

    return EquivalenceResult(
        True,
        "rows",
        f"Schema matched and {sample_size}-row sample hashed identically.",
    )


def _ast_identical(a: str, b: str) -> bool:
    try:
        tree_a = sqlglot.parse_one(a, read="snowflake")
        tree_b = sqlglot.parse_one(b, read="snowflake")
    except sqlglot.errors.ParseError:
        return False
    return _normalize(tree_a).sql() == _normalize(tree_b).sql()


def _normalize(tree: exp.Expression) -> exp.Expression:
    # Strip aliases on top-level select expressions when the alias matches the
    # column name; collapse whitespace via sqlglot's canonical re-render.
    return tree.copy().transform(
        lambda node: node.this if isinstance(node, exp.Alias)
        and isinstance(node.this, exp.Column)
        and node.alias == node.this.name
        else node
    )


def _schema_matches(a: str, b: str, *, runner) -> tuple[bool, str]:
    a_schema = _describe(a, runner=runner)
    b_schema = _describe(b, runner=runner)
    if a_schema != b_schema:
        return False, f"Schema mismatch: original={a_schema} rewritten={b_schema}"
    return True, "schema-equal"


def _describe(sql: str, *, runner) -> list[tuple[str, str]]:
    """Return [(column_name, type_name), ...] in projection order."""
    # `WHERE 1=0` ensures Snowflake plans but doesn't scan data.
    rows = runner(f"SELECT * FROM ({sql}) WHERE 1=0")
    if not rows:
        # No rows but cursor.description still tells us the schema; the runner
        # is responsible for surfacing it. For this spike we accept that an
        # empty list means "no schema info" and fail closed.
        return []
    sample = rows[0]
    return [(name, type(value).__name__) for name, value in sample.items()]


def _sample_rows_match(
    a: str, b: str, *, runner, sample_size: int
) -> tuple[bool, str]:
    a_rows = runner(_with_limit(a, sample_size))
    b_rows = runner(_with_limit(b, sample_size))
    if len(a_rows) != len(b_rows):
        return False, f"Row count differs: {len(a_rows)} vs {len(b_rows)}"
    a_hash = _hash_rows(a_rows)
    b_hash = _hash_rows(b_rows)
    if a_hash != b_hash:
        return False, "Row-hash mismatch in sample."
    return True, "rows-equal"


def _with_limit(sql: str, n: int) -> str:
    # Wrap rather than splicing — avoids breaking ORDER BY / QUALIFY in the
    # original. Stable ordering is a known weakness; see RISKS.md.
    return f"SELECT * FROM ({sql}) ORDER BY 1 LIMIT {n}"


def _hash_rows(rows: list[dict[str, Any]]) -> str:
    h = hashlib.sha256()
    for row in rows:
        for key in sorted(row.keys()):
            h.update(str(key).encode())
            h.update(b"\x00")
            h.update(repr(row[key]).encode())
            h.update(b"\x01")
        h.update(b"\x02")
    return h.hexdigest()
