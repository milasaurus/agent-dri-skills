#!/usr/bin/env bash
# Smoke-test the git-collection half of the spike (no API key needed).
# Runs against the repo passed as $1, defaulting to this skill repo.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${1:-$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "Repo:   $REPO"
echo "Author: $(git -C "$REPO" config user.email)"
echo "Window: 7 days"
echo

python3 "$HERE/gitstatus.py" --repo "$REPO" --dry-run --payload-out "$HERE/sample_payload.json"

echo
echo "Wrote payload to $HERE/sample_payload.json"
echo "When ANTHROPIC_API_KEY is set, run:"
echo "    python3 $HERE/gitstatus.py --repo $REPO"
