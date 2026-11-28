"""Score one case from its findings and approved [prediction ID, reference ID] edges."""
import argparse
from collections import deque
import json
from pathlib import Path


def item_ids(items):
    if not isinstance(items, list):
        raise ValueError("Expected an explicit list of findings.")
    ids = []
    seen = set()
    for item in items:
        key = item.get("id") if isinstance(item, dict) else None
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ValueError("Each finding on a side needs a unique, nonempty string ID.")
        ids.append(key)
        seen.add(key)
    return ids


def assign(edges):
    """Grow a maximum matching by rerouting earlier matches along alternating paths."""
    owner = {}
    partner = {}
    for start in edges:
        queue = deque([start])
        reached_by = {}
        while queue:
            pred = queue.popleft()
            for ref in edges[pred]:
                if ref in reached_by:
                    continue
                reached_by[ref] = pred
                if ref in owner:
                    queue.append(owner[ref])
                    continue
                # Walk back to the starting prediction and flip this path.
                while ref is not None:
                    pred = reached_by[ref]
                    previous = partner.get(pred)
                    owner[ref] = pred
                    partner[pred] = ref
                    ref = previous
                break
            else:
                continue
            break
    return partner


def score(case):
    if not isinstance(case, dict):
        raise ValueError("Expected a case object.")
    preds = item_ids(case.get("predictions"))
    refs = item_ids(case.get("references"))
    ref_ids = set(refs)
    edges = {key: [] for key in preds}
    eligible = case.get("eligible_pairs")
    if not isinstance(eligible, list):
        raise ValueError("Supply the eligible pairs, including an explicit empty list.")
    for pair in eligible:
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(x, str) for x in pair):
            raise ValueError("Each eligible pair must contain two string IDs.")
        pred, ref = pair
        if pred not in edges or ref not in ref_ids:
            raise ValueError(f"Unknown ID in pair {pair!r}.")
        if ref not in edges[pred]:
            edges[pred].append(ref)

    partner = assign(edges)
    matched = set(partner.values())
    extras = [p for p in preds if p not in partner]
    missed = [r for r in refs if r not in matched]
    hits = len(partner)
    total = len(preds) + len(refs)
    return {
        "pairs": [[p, partner[p]] for p in preds if p in partner],
        "extra_predictions": extras,
        "extra_with_eligible_references": {p: edges[p] for p in extras if edges[p]},
        "missed_references": missed,
        "tp": hits, "fp": len(extras), "fn": len(missed),
        "precision": hits / len(preds) if preds else None,
        "recall": hits / len(refs) if refs else None,
        "f1": 2 * hits / total if total else None,
        "both_empty": total == 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    args = parser.parse_args()
    try:
        result = score(json.loads(args.case.read_text(encoding="utf-8")))
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
