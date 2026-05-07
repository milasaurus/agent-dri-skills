"""
Popularity baseline. This is the bar the LLM has to clear.

If the LLM cannot beat "rank candidates by how often they appear in the user's
own history (with simple recency weighting), break ties by global popularity",
the spike has answered the question and we stop.

Intentionally simple — no embeddings, no co-occurrence matrix. The point is
that this is the floor.
"""

from __future__ import annotations

from collections import Counter

from eval_dataset import EvalExample


def rank(example: EvalExample, k: int = 20) -> list[str]:
    """Rank candidates by recency-weighted history frequency."""
    history = example.history
    candidates = set(example.candidates)

    score: dict[str, float] = {}
    n = len(history)
    for idx, event in enumerate(history):
        item_id = event["item_id"]
        if item_id not in candidates:
            continue
        # Linear recency: most recent event weighs ~1, oldest ~1/n
        weight = (idx + 1) / n
        if event["event_type"] == "purchase":
            weight *= 3.0
        elif event["event_type"] == "add_to_cart":
            weight *= 2.0
        score[item_id] = score.get(item_id, 0.0) + weight

    # Tie-breaker: arbitrary but deterministic
    ranked = sorted(
        example.candidates,
        key=lambda c: (-score.get(c, 0.0), c),
    )
    return ranked[:k]
