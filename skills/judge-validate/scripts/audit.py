"""Audit saved binary decisions against a JSONL case roster, optionally with one unchanged rerun."""
import argparse
from collections import Counter
import json
from pathlib import Path

BINARY = {"pass", "fail"}
STATUSES = BINARY | {"abstain", "error"}


def read_rows(path, predictions=False, selected=None):
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
            if selected is not None and key in selected:
                selected[key] = {"verdict": status, "explanation": row.get("evidence"),
                                 "error": row.get("error")}
        else:
            label = row.get("label")
            if label is not None and (not isinstance(label, str) or label not in BINARY | {"abstain"}):
                raise ValueError(f"{key}: unknown reference label.")
            rows[key] = label
            if selected is not None and key in selected:
                selected[key] = {"input": row.get("input_ref") or row.get("input"),
                                 "label": label, "explanation": row.get("label_explanation")}
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
    parser.add_argument("--review-cases", nargs="+", metavar="ID",
                        help="Include the inputs and explanations for these case IDs.")
    args = parser.parse_args()
    try:
        reference_details = dict.fromkeys(args.review_cases or [])
        roster = read_rows(args.roster, selected=reference_details)
        unknown = reference_details.keys() - roster.keys()
        if unknown:
            raise ValueError(f"Unknown review case IDs: {sorted(unknown)}")
        if not roster:
            raise ValueError("Empty roster.")
        paths = [args.predictions] + ([args.repeat] if args.repeat else [])
        runs = []
        reports = []
        for path in paths:
            predictions = dict.fromkeys(reference_details)
            run = read_rows(path, predictions=True, selected=predictions)
            runs.append(run)
            outside = run.keys() - roster.keys()
            if outside:
                raise ValueError(f"Predictions outside the intended roster: {sorted(outside)}")
            report = summarize(roster, run)
            if reference_details:
                report["review_cases"] = [
                    {"id": key, "input": ref["input"], "reference_label": ref["label"],
                     "reference_explanation": ref["explanation"], "judge": predictions[key]}
                    for key, ref in reference_details.items()
                ]
            reports.append(report)
        result = {"runs": reports}
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
