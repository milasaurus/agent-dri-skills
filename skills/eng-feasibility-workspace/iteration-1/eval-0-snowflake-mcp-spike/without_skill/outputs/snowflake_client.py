"""Thin Snowflake wrapper for the spike.

Intentionally minimal. Production will need:
  - Connection pooling
  - Per-user auth (OAuth or key-pair) instead of one service account
  - Statement timeouts via session params, not just client-side
  - Retry/backoff on transient network errors
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import snowflake.connector


@dataclass
class ExplainPlan:
    raw: dict[str, Any]
    estimated_bytes_scanned: int
    estimated_partitions: int
    has_join: bool

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "ExplainPlan":
        # Snowflake's EXPLAIN USING JSON returns a tree; we pull the root operator.
        # Shape varies by query; this extraction is best-effort and is one of the
        # things the spike is meant to surface as fragile.
        steps = payload.get("GlobalStats", {})
        return cls(
            raw=payload,
            estimated_bytes_scanned=int(steps.get("bytesAssigned", 0)),
            estimated_partitions=int(steps.get("partitionsAssigned", 0)),
            has_join=_walk_for_op(payload, "Join"),
        )


def _walk_for_op(node: Any, op_name: str) -> bool:
    if isinstance(node, dict):
        if node.get("Operation") == op_name:
            return True
        return any(_walk_for_op(v, op_name) for v in node.values())
    if isinstance(node, list):
        return any(_walk_for_op(v, op_name) for v in node)
    return False


class SnowflakeClient:
    def __init__(self) -> None:
        self._conn = None

    def _connect(self):
        if self._conn is not None:
            return self._conn
        self._conn = snowflake.connector.connect(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            role=os.environ.get("SNOWFLAKE_ROLE"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
            database=os.environ.get("SNOWFLAKE_DATABASE"),
            schema=os.environ.get("SNOWFLAKE_SCHEMA"),
            client_session_keep_alive=False,
        )
        return self._conn

    def explain(self, sql: str) -> ExplainPlan:
        cur = self._connect().cursor()
        try:
            cur.execute(f"EXPLAIN USING JSON {sql}")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("EXPLAIN returned no rows")
            payload = json.loads(row[0])
            return ExplainPlan.from_json(payload)
        finally:
            cur.close()

    def execute(self, sql: str, *, timeout_seconds: int = 60) -> list[dict[str, Any]]:
        cur = self._connect().cursor()
        try:
            cur.execute(f"ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = {timeout_seconds}")
            cur.execute(sql)
            cols = [c[0] for c in cur.description] if cur.description else []
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        finally:
            cur.close()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
