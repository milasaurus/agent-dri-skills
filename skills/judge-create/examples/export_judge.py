"""Example adapter. Read a single export case and grade the final artifact."""
from collections import Counter
import json
import sys


def grade(case):
    requested = case["requested_ids"]
    exported = case.get("exported_ids")
    if exported is None:
        return "abstain", "The final export is unavailable."
    for ids in (requested, exported):
        if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
            raise ValueError("Expected lists of record IDs")
    if len(set(requested)) != len(requested):
        raise ValueError("Requested record IDs must be unique")
    wanted, actual = Counter(requested), Counter(exported)
    missing, extra = list((wanted - actual).elements()), list((actual - wanted).elements())
    if missing or extra:
        return "fail", f"Missing occurrences: {missing}. Excess occurrences: {extra}."
    return "pass", f"All {len(wanted)} requested records occur exactly once."


if __name__ == "__main__":
    verdict, evidence = grade(json.load(sys.stdin))
    print(json.dumps({"verdict": verdict, "evidence": evidence}))
