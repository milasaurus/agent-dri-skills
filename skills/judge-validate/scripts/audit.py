"""Audit saved binary decisions against a JSONL case roster, optionally with one unchanged rerun."""
import argparse
from collections import Counter
import json
from pathlib import Path

BINARY = {"pass", "fail"}
STATUSES = BINARY | {"abstain", "error"}


def read_rows(path, predictions=False):
    rows = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: expected a JSON object.")
        if predictions and set(row) == {"summary"}:
            continue  # Footer from judge-create's runner.
        key = row.get("id")
        if not isinstance(key, str) or not key.strip() or key in rows:
            raise ValueError(f"{path}:{line_no}: missing or duplicate case ID.")
        if predictions:
            status = row.get("verdict")
            if "error" in row:
                if status is not None or not isinstance(row["error"], str) or not row["error"].strip():
                    raise ValueError(f"{key}: expected either a verdict or an error description.")
                status = "error"
            if not isinstance(status, str) or status not in STATUSES:
                raise ValueError(f"{key}: unknown prediction status.")
            rows[key] = status
        else:
            label = row.get("label")
            if label is not None and (not isinstance(label, str) or label not in BINARY | {"abstain"}):
                raise ValueError(f"{key}: unknown reference label.")
            rows[key] = label
    return rows


def summarize(roster, run):
    counts = Counter(run.get(key, "missing") for key in roster)
    confusion = {label: dict(Counter(run.get(key, "missing") for key, ref in roster.items()
                                     if ref == label)) for label in sorted(BINARY)}
    return {
        "assigned": len(roster), "prediction_status": dict(counts),
        "decided": counts["pass"] + counts["fail"],
        "unlabeled": sum(label is None for label in roster.values()),
        "reference_abstained": sum(label == "abstain" for label in roster.values()),
        "outcomes_by_reference_label": confusion,
        "false_pass_ids": [k for k, label in roster.items() if label == "fail" and run.get(k) == "pass"],
        "false_fail_ids": [k for k, label in roster.items() if label == "pass" and run.get(k) == "fail"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roster", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--repeat", type=Path)
    args = parser.parse_args()
    try:
        roster = read_rows(args.roster)
        if not roster:
            raise ValueError("Empty roster.")
        paths = [args.predictions] + ([args.repeat] if args.repeat else [])
        runs = [read_rows(path, predictions=True) for path in paths]
        for run in runs:
            outside = run.keys() - roster.keys()
            if outside:
                raise ValueError(f"Predictions outside the intended roster: {sorted(outside)}")
        result = {"runs": [summarize(roster, run) for run in runs]}
        if args.repeat:
            first, second = runs
            transitions = Counter()
            flips = []
            comparable = 0
            for key in roster:
                a, b = first.get(key, "missing"), second.get(key, "missing")
                transitions[f"{a} -> {b}"] += 1
                if a in BINARY and b in BINARY:
                    comparable += 1
                    if a != b:
                        flips.append(key)
            result["repeat"] = {"binary_pairs": comparable, "binary_flip_ids": flips,
                                "transitions": dict(transitions)}
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
