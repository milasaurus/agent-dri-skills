"""Offline scoring pilot. Run with python3 ticket_update.py. No agent is called."""
import json

# Public trial input. Each run starts from these same ticket assignments.
TRIAL = {
    "request": "Assign tickets A and B to Jo. Leave every other assignment alone.",
    "initial": {"A": "Mei", "B": "Sam", "C": "Lou"},
}

# Scoring-only observations from five illustrative runs of the same task.
# An empty dict would mean the queue was inspected and found empty.
OBSERVATIONS = [
    ("completed", {"C": "Lou", "B": "Jo", "A": "Jo"}, "full"),
    ("partial", {"A": "Jo", "B": "Sam", "C": "Lou"}, "partial"),
    ("unavailable", None, "unresolved"),
    ("lost-target", {"A": "Jo", "C": "Lou"}, "fail"),
    ("collateral-edit", {"A": "Jo", "B": "Jo", "C": "Kim"}, "fail"),
]


def score(final):
    if final is None:
        return "unresolved", "No final queue snapshot."
    targets = {"A", "B"}
    if set(final) != set(TRIAL["initial"]):
        return "fail", "Tickets were added or deleted during an assignment change."
    untouched = {key: value for key, value in TRIAL["initial"].items() if key not in targets}
    actual_untouched = {key: value for key, value in final.items() if key not in targets}
    if actual_untouched != untouched:
        return "fail", "Unrequested tickets changed."
    updated = sorted(key for key in targets if final.get(key) == "Jo")
    if len(updated) == len(targets):
        return "full", "Both tickets are assigned and other records are intact."
    return ("partial" if updated else "fail"), f"Confirmed assignments: {updated}."


if __name__ == "__main__":
    for case, observed, expected in OBSERVATIONS:
        verdict, reason = score(observed)
        if verdict != expected:
            raise ValueError(f"{case}: expected {expected}, got {verdict}")
        print(json.dumps({"fixture": case, "verdict": verdict, "reason": reason}))
