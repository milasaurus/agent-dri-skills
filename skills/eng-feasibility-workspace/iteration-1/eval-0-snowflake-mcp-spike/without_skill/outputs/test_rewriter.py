"""Offline tests for the rewrite + equivalence loop.

These run without credentials by mocking the Anthropic client and the
Snowflake runner. They prove the loop is wired correctly, not that the LLM
will actually produce good rewrites in prod — that needs a real eval harness
(see RISKS.md).
"""

from __future__ import annotations

import json
import pathlib
from unittest.mock import MagicMock

import pytest

from equivalence import check_equivalence
from rewriter import REWRITER_SYSTEM_PROMPT, RewriteProposal, Rewriter, _extract_json
from snowflake_client import ExplainPlan

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def expensive_plan() -> ExplainPlan:
    payload = json.loads((FIXTURES / "explain_plan.json").read_text())
    return ExplainPlan.from_json(payload)


@pytest.fixture
def original_sql() -> str:
    return (FIXTURES / "expensive_join.sql").read_text()


@pytest.fixture
def expected_rewrite() -> str:
    return (FIXTURES / "rewritten_expected.sql").read_text()


def _fake_anthropic(rewritten_sql: str) -> MagicMock:
    block = MagicMock(type="text")
    block.text = json.dumps(
        {
            "rewritten_sql": rewritten_sql,
            "rationale": "Pushed date filter into line_items; explicit projection.",
            "expected_savings": "high",
        }
    )
    response = MagicMock(content=[block])
    client = MagicMock()
    client.messages.create.return_value = response
    return client


def test_skips_when_below_threshold(monkeypatch, original_sql):
    monkeypatch.setenv("REWRITER_COST_THRESHOLD_BYTES", "10995116277760")  # 10 TiB
    plan = ExplainPlan(raw={}, estimated_bytes_scanned=1024, estimated_partitions=1, has_join=True)
    rewriter = Rewriter(client=_fake_anthropic("ignored"))
    result = rewriter.maybe_rewrite(original_sql, plan)
    assert result.skipped is True
    assert result.rewritten_sql == original_sql


def test_calls_llm_when_above_threshold(expensive_plan, original_sql, expected_rewrite, monkeypatch):
    monkeypatch.setenv("REWRITER_COST_THRESHOLD_BYTES", "1073741824")  # 1 GiB
    client = _fake_anthropic(expected_rewrite)
    rewriter = Rewriter(client=client)
    result = rewriter.maybe_rewrite(original_sql, expensive_plan)
    assert result.skipped is False
    assert "line_items" in result.rewritten_sql
    # Confirm the prompt actually told the model the rules.
    call = client.messages.create.call_args
    assert call.kwargs["system"] == REWRITER_SYSTEM_PROMPT


def test_extract_json_tolerates_prose():
    raw = 'Sure! Here is the rewrite:\n```json\n{"rewritten_sql": "SELECT 1", "rationale": "x", "expected_savings": "low"}\n```'
    parsed = _extract_json(raw)
    assert parsed["rewritten_sql"] == "SELECT 1"


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        _extract_json("no json here")


def test_equivalence_ast_layer_catches_alias_only_change():
    a = "SELECT id FROM t"
    b = "SELECT id AS id FROM t"
    runner = MagicMock(side_effect=AssertionError("AST layer should not need the runner"))
    result = check_equivalence(a, b, runner=runner)
    assert result.equivalent is True
    assert result.layer == "ast"


def test_equivalence_schema_layer_rejects_dropped_column():
    a = "SELECT id, name FROM t"
    b = "SELECT id FROM t"

    def runner(sql: str):
        if "id, name" in sql or "(SELECT id, name FROM t)" in sql:
            return [{"id": 1, "name": "x"}]
        return [{"id": 1}]

    result = check_equivalence(a, b, runner=runner)
    assert result.equivalent is False
    assert result.layer == "schema"


def test_equivalence_row_layer_catches_silent_filter_change():
    a = "SELECT id FROM t WHERE active = TRUE"
    b = "SELECT id FROM t"  # same schema, different rows

    rows_a = [{"id": 1}, {"id": 2}]
    rows_b = [{"id": 1}, {"id": 2}, {"id": 3}]

    def runner(sql: str):
        if "WHERE 1=0" in sql:
            return [{"id": 0}]  # schema probe; both queries project (id)
        if "active = TRUE" in sql:
            return rows_a
        return rows_b

    result = check_equivalence(a, b, runner=runner, sample_size=10)
    assert result.equivalent is False
    assert result.layer == "rows"


def test_equivalence_passes_when_rows_identical():
    a = "SELECT id FROM t"
    b = "SELECT t.id FROM t"  # AST differs after normalize? sqlglot may collapse it.

    def runner(sql: str):
        if "WHERE 1=0" in sql:
            return [{"id": 0}]
        return [{"id": 1}, {"id": 2}]

    result = check_equivalence(a, b, runner=runner, sample_size=10)
    assert result.equivalent is True
