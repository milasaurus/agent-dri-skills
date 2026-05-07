"""
Eval dataset for the LLM-recommender spike.

For day 0 we use a deterministic synthetic fixture so the spike runs end-to-end
without any data dependency. On day 1, replace `load_eval_set()` with a sample
of ~200 real user sessions from the warehouse.

Each eval example is:
    {
        "user_id":   str,
        "history":   [ {ts, item_id, event_type, ...}, ... ]   # last 50 events
        "candidates": [item_id, ...]                            # ~200 candidate items
        "next_clicks": [item_id, ...]                           # held-out future positives
    }

The eval is "given history and candidate set, rank top 20 from candidates;
how many of next_clicks land in the top-20 and where".
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


CATALOG_SIZE = 500
HISTORY_LEN = 50
CANDIDATE_SIZE = 200
NEXT_CLICKS_LEN = 5
EVENT_TYPES = ("view", "click", "add_to_cart", "purchase")


@dataclass
class EvalExample:
    user_id: str
    history: list[dict[str, Any]]
    candidates: list[str]
    next_clicks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "history": self.history,
            "candidates": self.candidates,
            "next_clicks": self.next_clicks,
        }


def _item_id(i: int) -> str:
    return f"item_{i:04d}"


def _make_user(rng: random.Random, user_idx: int) -> EvalExample:
    # Simulate a user with a "preferred cluster" of items they interact with.
    cluster_center = rng.randint(0, CATALOG_SIZE - 1)
    cluster_radius = 40

    def pick_in_cluster() -> int:
        offset = int(rng.gauss(0, cluster_radius / 2))
        return max(0, min(CATALOG_SIZE - 1, cluster_center + offset))

    history = []
    for t in range(HISTORY_LEN):
        history.append(
            {
                "ts": 1_700_000_000 + t * 60,
                "item_id": _item_id(pick_in_cluster()),
                "event_type": rng.choice(EVENT_TYPES),
            }
        )

    # Next clicks: also from the cluster (so a good ranker should outperform random)
    next_clicks = [_item_id(pick_in_cluster()) for _ in range(NEXT_CLICKS_LEN)]

    # Candidate set: the next_clicks plus a sampling from the catalog
    candidate_pool = set(next_clicks)
    while len(candidate_pool) < CANDIDATE_SIZE:
        candidate_pool.add(_item_id(rng.randint(0, CATALOG_SIZE - 1)))
    candidates = list(candidate_pool)
    rng.shuffle(candidates)

    return EvalExample(
        user_id=f"user_{user_idx:04d}",
        history=history,
        candidates=candidates,
        next_clicks=next_clicks,
    )


def load_eval_set(n_users: int = 50, seed: int = 42) -> list[EvalExample]:
    """Return n_users synthetic eval examples. Replace with real data on day 1."""
    rng = random.Random(seed)
    return [_make_user(rng, i) for i in range(n_users)]


def catalog_ids() -> list[str]:
    return [_item_id(i) for i in range(CATALOG_SIZE)]
