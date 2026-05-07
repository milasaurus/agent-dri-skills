"""
Metrics for the spike.

We measure exactly what the decision needs:
  - hit_rate_at_k: did any of the held-out next-clicks land in top-k?
  - ndcg_at_k:     graded position quality of the held-out next-clicks
  - mrr:           reciprocal rank of the first held-out next-click
  - id_validity:   share of returned lists that contain k unique candidate IDs
  - kendall_tau:   ranking stability across repeated runs of the same input
"""

from __future__ import annotations

import math
from typing import Iterable


def hit_rate_at_k(ranked: list[str], relevant: Iterable[str], k: int = 20) -> float:
    relevant_set = set(relevant)
    top_k = set(ranked[:k])
    return 1.0 if (top_k & relevant_set) else 0.0


def ndcg_at_k(ranked: list[str], relevant: Iterable[str], k: int = 20) -> float:
    relevant_set = set(relevant)
    dcg = 0.0
    for i, item in enumerate(ranked[:k]):
        if item in relevant_set:
            # Binary relevance, log2(i+2) discount (i is 0-indexed)
            dcg += 1.0 / math.log2(i + 2)
    # Ideal: all relevant items at top
    n_rel = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_rel))
    return (dcg / idcg) if idcg > 0 else 0.0


def mrr(ranked: list[str], relevant: Iterable[str]) -> float:
    relevant_set = set(relevant)
    for i, item in enumerate(ranked):
        if item in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def id_validity(ranked: list[str], candidates: Iterable[str], k: int = 20) -> dict:
    """Did the ranker return k unique IDs, all of which are in the candidate set?"""
    candidate_set = set(candidates)
    top_k = ranked[:k]
    in_catalog = [item for item in top_k if item in candidate_set]
    unique = set(top_k)
    return {
        "returned_count": len(top_k),
        "unique_count": len(unique),
        "in_catalog_count": len(in_catalog),
        "is_valid": len(top_k) == k and len(unique) == k and len(in_catalog) == k,
    }


def kendall_tau(rank_a: list[str], rank_b: list[str]) -> float:
    """
    Kendall's tau between two rankings of the same items.
    Items only in one of the two are dropped before scoring.
    Returns a value in [-1, 1]. 1 == identical order, 0 == random, -1 == reversed.
    """
    common = [item for item in rank_a if item in set(rank_b)]
    if len(common) < 2:
        return 0.0
    pos_b = {item: i for i, item in enumerate(rank_b)}
    pos_a = {item: i for i, item in enumerate(rank_a)}

    concordant = 0
    discordant = 0
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a_i, a_j = pos_a[common[i]], pos_a[common[j]]
            b_i, b_j = pos_b[common[i]], pos_b[common[j]]
            sign_a = (a_i - a_j)
            sign_b = (b_i - b_j)
            product = sign_a * sign_b
            if product > 0:
                concordant += 1
            elif product < 0:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else 0.0
