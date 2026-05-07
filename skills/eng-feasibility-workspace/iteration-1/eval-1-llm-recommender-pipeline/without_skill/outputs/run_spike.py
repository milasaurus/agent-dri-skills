"""
Spike orchestrator.

Runs the popularity baseline and the LLM ranker over the eval set, computes
the metrics that matter for the decision, and prints one table.

This is the day-0 file. On day 1, swap `load_eval_set` for real data and run.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field

import baseline
import llm_recommender
from eval_dataset import EvalExample, load_eval_set
from metrics import hit_rate_at_k, id_validity, kendall_tau, mrr, ndcg_at_k


K = 20

# Rough cost estimate; adjust to actual provider rates before reporting.
COST_PER_M_INPUT_TOKENS = 0.80   # $/1M input tokens (placeholder)
COST_PER_M_OUTPUT_TOKENS = 4.00  # $/1M output tokens (placeholder)


@dataclass
class RankerStats:
    name: str
    hit_rates: list[float] = field(default_factory=list)
    ndcgs: list[float] = field(default_factory=list)
    mrrs: list[float] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    valid_count: int = 0
    total_count: int = 0
    parse_failures: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    taus: list[float] = field(default_factory=list)

    def add(
        self,
        ranked: list[str],
        example: EvalExample,
        *,
        latency_ms: float = 0.0,
        is_valid: bool = True,
        parse_ok: bool = True,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        self.hit_rates.append(hit_rate_at_k(ranked, example.next_clicks, K))
        self.ndcgs.append(ndcg_at_k(ranked, example.next_clicks, K))
        self.mrrs.append(mrr(ranked, example.next_clicks))
        self.latencies_ms.append(latency_ms)
        self.total_count += 1
        if is_valid:
            self.valid_count += 1
        if not parse_ok:
            self.parse_failures += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def summary(self) -> dict:
        def _p95(xs: list[float]) -> float:
            if not xs:
                return 0.0
            xs_sorted = sorted(xs)
            idx = max(0, int(round(0.95 * (len(xs_sorted) - 1))))
            return xs_sorted[idx]

        cost_per_call = (
            self.input_tokens / 1_000_000 * COST_PER_M_INPUT_TOKENS
            + self.output_tokens / 1_000_000 * COST_PER_M_OUTPUT_TOKENS
        )
        per_1k = (cost_per_call / max(self.total_count, 1)) * 1000

        return {
            "name": self.name,
            "n": self.total_count,
            "hit@20": statistics.fmean(self.hit_rates) if self.hit_rates else 0.0,
            "ndcg@20": statistics.fmean(self.ndcgs) if self.ndcgs else 0.0,
            "mrr": statistics.fmean(self.mrrs) if self.mrrs else 0.0,
            "p95_ms": _p95(self.latencies_ms),
            "$/1k": per_1k,
            "id_valid_pct": 100.0 * self.valid_count / max(self.total_count, 1),
            "parse_fail_pct": 100.0 * self.parse_failures / max(self.total_count, 1),
            "tau_mean": statistics.fmean(self.taus) if self.taus else float("nan"),
        }


def _print_table(rows: list[dict]) -> None:
    cols = ["name", "n", "hit@20", "ndcg@20", "mrr", "p95_ms", "$/1k", "id_valid_pct", "parse_fail_pct", "tau_mean"]
    widths = {c: max(len(c), max(len(_fmt(r[c])) for r in rows)) for c in cols}
    header = "  ".join(c.ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))
    for r in rows:
        print("  ".join(_fmt(r[c]).ljust(widths[c]) for c in cols))


def _fmt(v) -> str:
    if isinstance(v, float):
        if v != v:  # nan
            return "n/a"
        if abs(v) >= 100:
            return f"{v:.1f}"
        return f"{v:.4f}"
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-users", type=int, default=20, help="eval set size")
    ap.add_argument("--repeats", type=int, default=2, help="repeat runs per user for stability (>=2 for tau)")
    ap.add_argument("--dry-run", action="store_true", help="no API calls; uses canned responses")
    ap.add_argument("--model", default="claude-3-5-haiku-latest")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output-json", default="spike_results.json", help="where to write the result blob")
    args = ap.parse_args()

    examples = load_eval_set(n_users=args.n_users, seed=args.seed)
    print(f"Loaded {len(examples)} eval examples (synthetic; swap with real data on day 1).", file=sys.stderr)

    pop_stats = RankerStats(name="popularity")
    llm_stats = RankerStats(name="llm-recommender")

    for ex in examples:
        # Baseline — single deterministic run
        ranked = baseline.rank(ex, k=K)
        validity = id_validity(ranked, ex.candidates, k=K)
        pop_stats.add(
            ranked,
            ex,
            latency_ms=0.5,  # baseline is essentially free
            is_valid=validity["is_valid"],
        )

        # LLM — repeat runs to measure stability
        repeat_rankings: list[list[str]] = []
        for _ in range(args.repeats):
            result = llm_recommender.rank(ex, k=K, model=args.model, dry_run=args.dry_run)
            validity = id_validity(result.ranked, ex.candidates, k=K)
            llm_stats.add(
                result.ranked,
                ex,
                latency_ms=result.latency_ms,
                is_valid=validity["is_valid"],
                parse_ok=result.parse_ok,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )
            repeat_rankings.append(result.ranked)

        # Stability across repeats: average tau across all pairs
        if len(repeat_rankings) >= 2:
            pair_taus = []
            for i in range(len(repeat_rankings)):
                for j in range(i + 1, len(repeat_rankings)):
                    pair_taus.append(kendall_tau(repeat_rankings[i], repeat_rankings[j]))
            if pair_taus:
                llm_stats.taus.append(statistics.fmean(pair_taus))

    rows = [pop_stats.summary(), llm_stats.summary()]
    print()
    _print_table(rows)
    print()

    # Decision summary — explicit so the spike output is self-explanatory.
    pop = rows[0]
    llm = rows[1]
    decisions = []
    decisions.append(("quality_beats_baseline", llm["ndcg@20"] > pop["ndcg@20"] or llm["hit@20"] > pop["hit@20"]))
    decisions.append(("id_validity_>=_95pct", llm["id_valid_pct"] >= 95.0))
    decisions.append(("parse_fail_<_5pct", llm["parse_fail_pct"] < 5.0))
    decisions.append(("tau_>=_0.7", (llm["tau_mean"] == llm["tau_mean"]) and llm["tau_mean"] >= 0.7))

    print("Decision criteria:")
    for name, ok in decisions:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    all_pass = all(ok for _, ok in decisions)
    print()
    print("Verdict:", "GREENLIGHT (all gates pass)" if all_pass else "DO NOT BUILD YET — see failed gates above")

    # Persist for the day-1 writeup.
    with open(args.output_json, "w") as f:
        json.dump(
            {
                "ts": time.time(),
                "args": vars(args),
                "rows": rows,
                "decisions": dict(decisions),
                "verdict": "greenlight" if all_pass else "no-go",
            },
            f,
            indent=2,
        )

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
