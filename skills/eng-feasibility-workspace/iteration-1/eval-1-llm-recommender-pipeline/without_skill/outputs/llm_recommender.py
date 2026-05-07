"""
LLM ranker under test.

This is the core of the spike. It:
  - Builds a tight prompt: the user history (last 50 events) and the candidate
    set, asking for exactly 20 ranked IDs from the candidates.
  - Calls the provider (Anthropic by default).
  - Parses + validates the response. Hallucinated IDs and malformed JSON are
    expected failure modes; we measure them rather than retry-until-success,
    because the rate is itself a signal we need.
  - Records latency and token counts.

Dry-run mode returns a deterministic canned response so the spike is runnable
end-to-end without any API key. The canned response is intentionally imperfect
— it includes one hallucinated ID — so the validation path is exercised.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from eval_dataset import EvalExample


SYSTEM_PROMPT = """\
You are a recommendation ranker. Given a user's recent activity history and a
set of candidate item IDs, return the 20 candidate item IDs that the user is
most likely to engage with next, ranked from most likely to least likely.

Hard constraints:
- Return exactly 20 item IDs.
- Every ID must come from the provided candidate list. Do not invent IDs.
- Each ID must appear at most once.
- Output ONLY a JSON object of the form {"ranked_item_ids": ["item_xxxx", ...]}.
  No prose, no markdown, no code fences.
"""


def _user_message(example: EvalExample, k: int) -> str:
    history_compact = [
        {"t": e["ts"], "id": e["item_id"], "type": e["event_type"]}
        for e in example.history
    ]
    return (
        f"User: {example.user_id}\n"
        f"History (last {len(example.history)} events, oldest first):\n"
        f"{json.dumps(history_compact)}\n\n"
        f"Candidate item IDs ({len(example.candidates)}):\n"
        f"{json.dumps(example.candidates)}\n\n"
        f"Return the top {k} ranked IDs as JSON."
    )


@dataclass
class LLMResult:
    ranked: list[str]
    raw_text: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    parse_ok: bool = True
    parse_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse(raw: str) -> tuple[list[str], bool, str | None]:
    try:
        # Be lenient about leading/trailing whitespace; reject markdown fences.
        text = raw.strip()
        if text.startswith("```"):
            # Strip a single fenced block if the model added one despite instructions.
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        obj = json.loads(text)
        ids = obj.get("ranked_item_ids")
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            return [], False, "ranked_item_ids missing or not a list of strings"
        return ids, True, None
    except json.JSONDecodeError as e:
        return [], False, f"JSONDecodeError: {e}"


def rank(
    example: EvalExample,
    k: int = 20,
    *,
    model: str = "claude-3-5-haiku-latest",
    dry_run: bool = False,
) -> LLMResult:
    """
    Run the LLM ranker against one eval example.

    `dry_run=True` returns a canned response with a built-in error case
    (one hallucinated ID), so we can see the validation path work without
    spending API credits.
    """
    if dry_run:
        return _dry_run_rank(example, k)

    # Real call — provider SDK is imported lazily so dry-run has no dep.
    from anthropic import Anthropic  # type: ignore

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    started = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _user_message(example, k)}],
    )
    latency_ms = (time.perf_counter() - started) * 1000.0

    raw = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    ranked, ok, err = _parse(raw)
    return LLMResult(
        ranked=ranked,
        raw_text=raw,
        latency_ms=latency_ms,
        input_tokens=getattr(response.usage, "input_tokens", 0),
        output_tokens=getattr(response.usage, "output_tokens", 0),
        parse_ok=ok,
        parse_error=err,
        metadata={"model": model, "stop_reason": response.stop_reason},
    )


def _dry_run_rank(example: EvalExample, k: int) -> LLMResult:
    """
    Canned response that mimics what an LLM might return.

    We deliberately:
      - Pick mostly from candidates (so quality is plausible),
      - Include ONE hallucinated ID (to exercise validity tracking),
      - Add a small constant latency.

    Strategy: take the most-recent items from the user's history that ARE in
    the candidate set; pad with random candidates; replace one slot with a
    fake ID.
    """
    candidates = example.candidates
    candidate_set = set(candidates)
    seen: list[str] = []
    for event in reversed(example.history):
        item_id = event["item_id"]
        if item_id in candidate_set and item_id not in seen:
            seen.append(item_id)
        if len(seen) >= k:
            break
    # Pad with the front of the candidate list
    for c in candidates:
        if len(seen) >= k:
            break
        if c not in seen:
            seen.append(c)
    # Inject one hallucinated ID to exercise validation
    if len(seen) >= 5:
        seen[4] = "item_9999_fake"
    seen = seen[:k]

    raw = json.dumps({"ranked_item_ids": seen})
    return LLMResult(
        ranked=seen,
        raw_text=raw,
        latency_ms=42.0,
        input_tokens=1500,
        output_tokens=200,
        parse_ok=True,
        parse_error=None,
        metadata={"model": "dry-run", "stop_reason": "end_turn"},
    )
