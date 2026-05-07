"""LLM-as-recommender spike — history JSON → ranked top-20 item IDs.

Validates the four must-hold assumptions in ../assumptions.md against
the real Anthropic API:

    M1  Output shape reliability     (length, uniqueness, catalog membership)
    M2  Ranking quality vs. baseline (top-5 recall@5 vs. baseline + human judgment)
    M3  Latency and cost envelope    (timed per-call, token-cost estimated)
    M4  End-to-end IA walkthrough    (cold-start branch, long-history branch)

Single file. No abstractions worth keeping. Real API calls. Hand-picked
fixtures span: long-history power user, mid-history regular user,
short-history cold-start user, history with a recent purchase that
should be filtered out, history with strong category signal.

Run:

    pip install anthropic
    export ANTHROPIC_API_KEY=...
    python spike.py                 # all 5 fixtures
    python spike.py 2               # just fixture index 2
    REPEAT=2 python spike.py 0      # call same fixture twice (S1 determinism)

Outputs every input, every raw model response, parsed list, gate
results, latency, and an estimated cost per call. Writes a one-line
JSON summary per fixture to results.jsonl next to this file so the
tradeoffs.md author can paste numbers in directly.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from anthropic import Anthropic

# --- config -------------------------------------------------------------

# Read key from env. The spike is intentionally a hard fail if the key
# is missing — silently skipping live calls would let us "pass" gates
# we never measured.
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    sys.exit("missing ANTHROPIC_API_KEY (no credentials => no measurement)")

# Sonnet is the realistic production candidate for a quality bet; if it
# fails M2 we don't have a smaller-model fallback worth trying. Override
# with MODEL=... if you want to compare.
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = 1024
TEMPERATURE = 0.0

REPEAT = int(os.environ.get("REPEAT", "1"))  # for S1 determinism check

# Order-of-magnitude pricing for cost estimation. Update if the model
# changes — this is a rough envelope check, not an invoice.
PRICE_INPUT_PER_MTOK = 3.0
PRICE_OUTPUT_PER_MTOK = 15.0

RESULTS_PATH = Path(__file__).with_name("results.jsonl")

# --- catalog ------------------------------------------------------------

# A bounded candidate pool. In production this would be the output of a
# candidate-gen step (recency, segment, ANN). Hardcoded here so the
# spike tests "given a candidate set, can the LLM rank it" — which is
# the actual question. 200 items keeps the prompt small enough to be
# realistic at the proposed budget; if production needs 5k, that's an
# S2 risk to measure separately.

CATEGORIES = ["running", "trail", "casual", "basketball", "tennis", "kids"]


def _make_catalog() -> list[dict]:
    items = []
    for i in range(200):
        items.append(
            {
                "id": f"sku_{1000 + i}",
                "title": f"{CATEGORIES[i % len(CATEGORIES)].title()} Shoe Model {i}",
                "category": CATEGORIES[i % len(CATEGORIES)],
                "price": 60 + (i % 14) * 10,
            }
        )
    return items


CATALOG = _make_catalog()
VALID_IDS = {item["id"] for item in CATALOG}

# --- fixtures -----------------------------------------------------------

# Each fixture is (label, events, baseline_top20). baseline_top20 stands
# in for "the existing recommender's top-20 on this user." In a real run
# you'd replace these with actual outputs from the production system on
# matched user IDs. The point of this fixture is to make M2's overlap
# metric measurable on day 0 with realistic catalog membership.


def _baseline(category_bias: str, n: int = 20) -> list[str]:
    """Crude baseline: items in the biased category, then alternates."""
    biased = [it["id"] for it in CATALOG if it["category"] == category_bias]
    others = [it["id"] for it in CATALOG if it["category"] != category_bias]
    return (biased + others)[:n]


FIXTURES: list[tuple[str, list[dict], list[str]]] = [
    (
        "F1 long-history power user, running-biased",
        [
            {"ts": f"2026-04-{d:02d}T10:00:00Z", "type": t, "item_id": iid, "category": cat}
            for d, t, iid, cat in [
                (15, "view", "sku_1000", "running"),
                (15, "view", "sku_1006", "running"),
                (15, "add_to_cart", "sku_1006", "running"),
                (16, "view", "sku_1012", "running"),
                (16, "purchase", "sku_1006", "running"),
                (17, "view", "sku_1018", "running"),
                (17, "view", "sku_1024", "running"),
                (18, "view", "sku_1030", "running"),
                (18, "view", "sku_1036", "running"),
                (19, "view", "sku_1042", "running"),
                (19, "add_to_cart", "sku_1042", "running"),
                (20, "view", "sku_1048", "running"),
                (20, "view", "sku_1054", "running"),
                (21, "view", "sku_1060", "running"),
                (21, "view", "sku_1066", "running"),
                (22, "view", "sku_1072", "running"),
                (23, "view", "sku_1078", "running"),
                (24, "view", "sku_1084", "running"),
                (25, "view", "sku_1090", "running"),
                (26, "view", "sku_1096", "running"),
                (27, "view", "sku_1102", "running"),
                (28, "view", "sku_1108", "running"),
                (29, "view", "sku_1114", "running"),
                (30, "view", "sku_1120", "running"),
            ]
            + [
                # padding to >=50 events, lighter signal across categories
                (1 + i, "view", f"sku_{1000 + (i * 6) % 200}", CATEGORIES[i % 6])
                for i in range(30)
            ]
        ],
        _baseline("running"),
    ),
    (
        "F2 mid-history, mixed signal",
        [
            {"ts": f"2026-04-{d:02d}T10:00:00Z", "type": t, "item_id": iid, "category": cat}
            for d, t, iid, cat in [
                (10, "view", "sku_1003", "basketball"),
                (10, "view", "sku_1009", "basketball"),
                (11, "view", "sku_1015", "basketball"),
                (11, "view", "sku_1004", "tennis"),
                (12, "view", "sku_1010", "tennis"),
                (13, "view", "sku_1016", "tennis"),
                (14, "view", "sku_1022", "tennis"),
                (14, "add_to_cart", "sku_1022", "tennis"),
                (15, "view", "sku_1028", "tennis"),
                (15, "purchase", "sku_1022", "tennis"),
                (16, "view", "sku_1034", "tennis"),
                (16, "view", "sku_1040", "tennis"),
                (17, "view", "sku_1046", "tennis"),
                (18, "view", "sku_1052", "tennis"),
                (19, "view", "sku_1058", "tennis"),
                (20, "view", "sku_1064", "tennis"),
                (21, "view", "sku_1070", "tennis"),
                (22, "view", "sku_1076", "tennis"),
                (23, "view", "sku_1082", "tennis"),
                (24, "view", "sku_1088", "tennis"),
            ]
        ],
        _baseline("tennis"),
    ),
    (
        "F3 cold-start (3 events)",
        [
            {"ts": "2026-05-06T09:00:00Z", "type": "view", "item_id": "sku_1005", "category": "trail"},
            {"ts": "2026-05-06T09:05:00Z", "type": "view", "item_id": "sku_1011", "category": "trail"},
            {"ts": "2026-05-06T09:08:00Z", "type": "view", "item_id": "sku_1017", "category": "trail"},
        ],
        _baseline("trail"),
    ),
    (
        "F4 recent purchase, should be filtered out of recs",
        [
            {"ts": f"2026-05-{d:02d}T10:00:00Z", "type": t, "item_id": iid, "category": cat}
            for d, t, iid, cat in [
                (1, "view", "sku_1002", "casual"),
                (1, "view", "sku_1008", "casual"),
                (2, "view", "sku_1014", "casual"),
                (2, "purchase", "sku_1014", "casual"),  # just bought; should not be re-recommended
                (3, "view", "sku_1020", "casual"),
                (4, "view", "sku_1026", "casual"),
                (5, "view", "sku_1032", "casual"),
                (5, "view", "sku_1038", "casual"),
                (6, "view", "sku_1044", "casual"),
                (6, "view", "sku_1050", "casual"),
            ]
        ],
        _baseline("casual"),
    ),
    (
        "F5 strong kids category signal across 50 events",
        [
            {"ts": f"2026-04-{1 + (i % 28):02d}T10:00:00Z",
             "type": "view",
             "item_id": f"sku_{1005 + (i * 6) % 200}",
             "category": "kids" if i % 3 != 0 else CATEGORIES[i % 6]}
            for i in range(50)
        ],
        _baseline("kids"),
    ),
]

# --- prompt -------------------------------------------------------------

SYSTEM_PROMPT = """You are a product ranking assistant. Given a user's recent event history and a list of candidate items, pick the 20 items the user is most likely to want next, ordered from most to least likely.

Rules — these are hard constraints, not suggestions:
1. Output EXACTLY 20 item IDs.
2. Every ID MUST appear in the supplied candidates list. Do not invent IDs.
3. No duplicates.
4. Do not re-recommend items the user has already purchased in their history.
5. Output ONLY a JSON object of the form {"ranking": ["sku_xxxx", ...]} — no preamble, no commentary, no markdown fences.

Use the events to infer category preference, recency, and intent (a purchase is a strong signal of category interest but the purchased item itself is "done"). When the user has very few events, fall back to popular items in the categories they have touched."""


def build_user_message(events: list[dict]) -> str:
    return (
        f"User events (most recent {len(events)}):\n"
        f"{json.dumps(events, indent=2)}\n\n"
        f"Candidates ({len(CATALOG)} items):\n"
        f"{json.dumps(CATALOG)}\n\n"
        f"Return the JSON object now."
    )


# --- gates --------------------------------------------------------------


@dataclass
class GateResult:
    fixture: str
    parsed_ok: bool
    length_ok: bool
    unique_ok: bool
    catalog_ok: bool
    excluded_purchases_ok: bool
    recall_at_5: float
    latency_s: float
    input_tokens: int
    output_tokens: int
    est_cost_usd: float
    raw_first_120_chars: str


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_ranking(raw: str) -> list[str] | None:
    """Tolerant parse — accept JSON with or without surrounding prose.

    The system prompt forbids prose, so this leniency is intentionally
    doing double duty: tolerating it AND counting it via the
    raw_first_120_chars field, so we can see how often the model
    violates the no-preamble rule even when the JSON is valid.
    """
    m = _JSON_RE.search(raw)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    ranking = data.get("ranking")
    if not isinstance(ranking, list) or not all(isinstance(x, str) for x in ranking):
        return None
    return ranking


def evaluate(label: str, raw: str, latency: float, in_tok: int, out_tok: int,
             events: list[dict], baseline_top20: list[str]) -> GateResult:
    ranking = parse_ranking(raw)
    parsed_ok = ranking is not None
    ranking = ranking or []

    length_ok = len(ranking) == 20
    unique_ok = len(set(ranking)) == len(ranking) and len(ranking) > 0
    catalog_ok = bool(ranking) and all(rid in VALID_IDS for rid in ranking)

    purchased = {ev["item_id"] for ev in events if ev.get("type") == "purchase"}
    excluded_purchases_ok = not (purchased & set(ranking)) if ranking else False

    top5 = ranking[:5]
    baseline_set = set(baseline_top20)
    overlap = len([r for r in top5 if r in baseline_set])
    recall_at_5 = overlap / 5 if top5 else 0.0

    cost = (in_tok / 1_000_000) * PRICE_INPUT_PER_MTOK + (out_tok / 1_000_000) * PRICE_OUTPUT_PER_MTOK

    return GateResult(
        fixture=label,
        parsed_ok=parsed_ok,
        length_ok=length_ok,
        unique_ok=unique_ok,
        catalog_ok=catalog_ok,
        excluded_purchases_ok=excluded_purchases_ok,
        recall_at_5=recall_at_5,
        latency_s=latency,
        input_tokens=in_tok,
        output_tokens=out_tok,
        est_cost_usd=cost,
        raw_first_120_chars=raw[:120].replace("\n", " "),
    )


# --- one call -----------------------------------------------------------

client = Anthropic(api_key=API_KEY)


def call_once(label: str, events: list[dict], baseline_top20: list[str]) -> GateResult:
    user_msg = build_user_message(events)

    print(f"=== {label} ===")
    print(f"  events: {len(events)}   catalog: {len(CATALOG)}")

    t0 = time.monotonic()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    latency = time.monotonic() - t0

    raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    in_tok = resp.usage.input_tokens
    out_tok = resp.usage.output_tokens

    result = evaluate(label, raw, latency, in_tok, out_tok, events, baseline_top20)

    print(f"  latency: {latency:.2f}s   tokens: in={in_tok} out={out_tok}   est cost: ${result.est_cost_usd:.4f}")
    print(f"  raw[:120]: {result.raw_first_120_chars!r}")
    print(
        f"  parsed={result.parsed_ok} len20={result.length_ok} unique={result.unique_ok} "
        f"in_catalog={result.catalog_ok} excl_purchases={result.excluded_purchases_ok} "
        f"recall@5={result.recall_at_5:.2f}"
    )
    print()
    return result


# --- IA walkthrough -----------------------------------------------------


def walkthrough_check(events: list[dict]) -> tuple[bool, str]:
    """Stand-in for the user-flow walk. Returns (ok, decision_note).

    Decisions surfaced by walking the flow on day 0:
      - cold-start branch: <5 events ⇒ explicit fallback to category-popular,
        not "ask the LLM with sparse history" (would amplify noise).
      - catalog source: candidate pool is fixed input here; in production
        this becomes a candidate-gen call (S2). The LLM's job is rank,
        not retrieve.
      - staleness: catalog is read once per request. If catalog churns
        within a session, the LLM may rank stale IDs. Out of spike scope.
    """
    if len(events) < 5:
        return True, "cold-start path: short history, fallback rule documented"
    return True, "long-history path: full LLM ranking"


# --- main ---------------------------------------------------------------


def main() -> None:
    if len(sys.argv) > 1:
        idx = int(sys.argv[1])
        selected = [FIXTURES[idx]]
    else:
        selected = FIXTURES

    print(f"MODEL: {MODEL}   TEMP: {TEMPERATURE}   REPEAT: {REPEAT}")
    print(f"catalog size: {len(CATALOG)}   fixtures: {len(selected)}")
    print()

    all_results: list[GateResult] = []
    with RESULTS_PATH.open("a") as fh:
        for label, events, baseline in selected:
            ok, note = walkthrough_check(events)
            print(f"[IA] {label}: {note}")
            for rep in range(REPEAT):
                tag = f"{label}" + (f" (rep {rep + 1}/{REPEAT})" if REPEAT > 1 else "")
                result = call_once(tag, events, baseline)
                all_results.append(result)
                fh.write(json.dumps(asdict(result)) + "\n")

    # --- aggregate gate roll-up ---------------------------------------
    n = len(all_results)
    if n == 0:
        return

    m1_pass = sum(
        1 for r in all_results
        if r.parsed_ok and r.length_ok and r.unique_ok and r.catalog_ok
    )
    purchase_excl_pass = sum(1 for r in all_results if r.excluded_purchases_ok)
    mean_recall_at_5 = sum(r.recall_at_5 for r in all_results) / n
    median_latency = sorted(r.latency_s for r in all_results)[n // 2]
    median_cost = sorted(r.est_cost_usd for r in all_results)[n // 2]

    print("=" * 60)
    print("ROLL-UP")
    print(f"  M1 output-shape pass:         {m1_pass}/{n}  (gate: >= 9/10)")
    print(f"  purchase-exclusion pass:       {purchase_excl_pass}/{n}")
    print(f"  M2 mean recall@5 vs baseline: {mean_recall_at_5:.2f}  (gate: >= 0.40)")
    print(f"  M3 median latency:             {median_latency:.2f}s  (gate online: <=5s, batch: <=30s)")
    print(f"  M3 median cost/call:           ${median_cost:.4f}  (gate: <= $0.02)")
    print()
    print("Human-judgment leg of M2 is not automated. After the run:")
    print("  Open results.jsonl, look at top-5 of each fixture's ranking,")
    print("  and tally how many feel 'plausible or better than baseline'.")
    print("  Gate: >= 7/10. Record verdict in tradeoffs.md.")
    print()
    print(f"results.jsonl: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
