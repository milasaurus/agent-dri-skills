"""Run a trusted, per-case judge command and score its categorical predictions."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

DECISIONS = ("pass", "fail")
VERDICTS = (*DECISIONS, "abstain")


def load_cases(path):
    cases = []
    seen = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("input"), dict):
            raise ValueError(f"Line {number}: expected an object with an input object.")
        key = row.get("id")
        if not isinstance(key, str) or not key.strip() or key in seen:
            raise ValueError(f"Line {number}: expected a unique, nonempty string ID.")
        if "label" in row and row["label"] not in VERDICTS:
            raise ValueError(f"Line {number}: unknown human label.")
        seen.add(key)
        cases.append(row)
    if not cases:
        raise ValueError("The dataset is empty.")
    return cases


def predict(command, inputs, timeout):
    try:
        result = subprocess.run(command, input=json.dumps(inputs), capture_output=True,
                                text=True, timeout=timeout, check=True)
        parsed = json.loads(result.stdout)
        if not isinstance(parsed, dict) or parsed.get("verdict") not in VERDICTS:
            raise ValueError("Missing or invalid verdict.")
        evidence = parsed.get("evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Missing evidence string.")
        return {"verdict": parsed["verdict"], "evidence": evidence}
    except subprocess.TimeoutExpired:
        return {"error": "Judge timed out."}
    except subprocess.CalledProcessError as exc:
        return {"error": f"Judge exited with status {exc.returncode}."}
    except (ValueError, OSError) as exc:
        return {"error": str(exc)}


def summarize(rows):
    labeled = [row for row in rows if "label" in row]
    decided = [row for row in labeled if row["label"] in DECISIONS
               and row.get("verdict") in DECISIONS]
    agreed = sum(row["label"] == row["verdict"] for row in decided)
    return {
        "total": len(rows),
        "labeled": len(labeled),
        "unlabeled": len(rows) - len(labeled),
        "errors": sum("error" in row for row in rows),
        "abstentions": sum(row.get("verdict") == "abstain" for row in rows),
        "human_binary_labels": sum(row["label"] in DECISIONS for row in labeled),
        "binary_decisions_on_human_binary_labels": len(decided),
        "agreement_on_paired_binary_decisions": agreed / len(decided) if decided else None,
        "false_passes": sum(row["label"] == "fail" and row["verdict"] == "pass" for row in decided),
        "false_fails": sum(row["label"] == "pass" and row["verdict"] == "fail" for row in decided),
        "decisions_where_human_abstained": sum(row["label"] == "abstain"
                                              and row.get("verdict") in DECISIONS for row in labeled),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("--preview", action="store_true", help="Show the first judge input and exit.")
    parser.add_argument("--timeout", type=int, default=30, help="Seconds per case (default 30).")
    parser.add_argument("--judge", nargs=argparse.REMAINDER, help="Trusted executable and its arguments.")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        cases = load_cases(args.cases)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.preview:
        print(json.dumps(cases[0]["input"], indent=2))
        return 0
    if not args.judge:
        parser.error("provide --judge COMMAND [ARG ...] or --preview")
    rows = []
    for case in cases:
        row = {"id": case["id"], **predict(args.judge, case["input"], args.timeout)}
        if "label" in case:
            row["label"] = case["label"]
        print(json.dumps(row), flush=True)
        rows.append(row)
    summary = summarize(rows)
    print(json.dumps({"summary": summary}))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
