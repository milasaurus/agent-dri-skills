#!/usr/bin/env python3
"""
gitstatus: read recent git activity and produce a one-paragraph status update.

Usage:
    python gitstatus.py                        # last 7 days, current user, all branches they've committed on
    python gitstatus.py --days 14
    python gitstatus.py --author you@org.com
    python gitstatus.py --dry-run              # print the payload that would be sent to Claude, don't call the API
    python gitstatus.py --repo /path/to/repo

Requires:
    - git on PATH
    - ANTHROPIC_API_KEY env var (unless --dry-run)
    - `pip install anthropic`
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Iterable


# A unit-separator-delimited format keeps us safe from commit messages that
# contain anything we'd otherwise use as a delimiter (newlines, tabs, pipes).
_GIT_LOG_FORMAT = "%H%x1f%an%x1f%ae%x1f%aI%x1f%s%x1f%b"
_RECORD_SEP = "\x1e"  # between commits
_FIELD_SEP = "\x1f"   # between fields


@dataclass
class Commit:
    sha: str
    author_name: str
    author_email: str
    authored_at: str   # ISO 8601
    subject: str
    body: str
    branches: list[str]
    files_changed: int
    insertions: int
    deletions: int


def _run(cmd: list[str], cwd: str) -> str:
    result = subprocess.run(
        cmd, cwd=cwd, check=True, capture_output=True, text=True
    )
    return result.stdout


def _current_user_email(repo: str) -> str:
    return _run(["git", "config", "user.email"], cwd=repo).strip()


def _branches_with_author(repo: str, author: str, since_iso: str) -> list[str]:
    """Branches (local + remote) that have at least one commit by `author` since `since_iso`."""
    out = _run(
        [
            "git", "for-each-ref",
            "--format=%(refname)",
            "refs/heads/", "refs/remotes/",
        ],
        cwd=repo,
    )
    branches = [line.strip() for line in out.splitlines() if line.strip()]
    # Skip remote HEAD pointers like refs/remotes/origin/HEAD.
    branches = [b for b in branches if not b.endswith("/HEAD")]

    matched = []
    for ref in branches:
        try:
            log = _run(
                [
                    "git", "log", ref,
                    f"--since={since_iso}",
                    f"--author={author}",
                    "--pretty=format:%H",
                    "--no-merges",
                ],
                cwd=repo,
            )
        except subprocess.CalledProcessError:
            continue
        if log.strip():
            matched.append(ref)
    return matched


def _commits_on_ref(repo: str, ref: str, author: str, since_iso: str) -> list[dict]:
    raw = _run(
        [
            "git", "log", ref,
            f"--since={since_iso}",
            f"--author={author}",
            f"--pretty=format:{_GIT_LOG_FORMAT}{_RECORD_SEP}",
            "--no-merges",
            "--shortstat",
        ],
        cwd=repo,
    )
    return _parse_log_with_shortstat(raw)


def _parse_log_with_shortstat(raw: str) -> list[dict]:
    """
    `git log --shortstat` output for one commit looks like:

        <H><US><an><US><ae><US><aI><US><subject><US><body><RS>
         3 files changed, 12 insertions(+), 4 deletions(-)

    The shortstat line is appended after the record separator. We split on the
    record separator first, then for each chunk we split off the trailing stats.
    """
    commits = []
    for chunk in raw.split(_RECORD_SEP):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        # The first line(s) are the formatted commit; the last non-empty line
        # is the shortstat (if any).
        lines = chunk.split("\n")
        # Find the formatted record (it'll have field separators in it).
        formatted = next((l for l in lines if _FIELD_SEP in l), None)
        if not formatted:
            continue
        sha, an, ae, aI, subject, *body_parts = formatted.split(_FIELD_SEP)
        body = _FIELD_SEP.join(body_parts).strip()

        stats_line = next(
            (l for l in reversed(lines) if "changed" in l and ("insertion" in l or "deletion" in l)),
            "",
        )
        files_changed, insertions, deletions = _parse_shortstat(stats_line)

        commits.append({
            "sha": sha,
            "author_name": an,
            "author_email": ae,
            "authored_at": aI,
            "subject": subject,
            "body": body,
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
        })
    return commits


def _parse_shortstat(line: str) -> tuple[int, int, int]:
    files_changed = insertions = deletions = 0
    for part in line.split(","):
        part = part.strip()
        if "file" in part:
            files_changed = int(part.split()[0])
        elif "insertion" in part:
            insertions = int(part.split()[0])
        elif "deletion" in part:
            deletions = int(part.split()[0])
    return files_changed, insertions, deletions


def collect_commits(repo: str, author: str, days: int) -> list[Commit]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since.isoformat()

    refs = _branches_with_author(repo, author, since_iso)
    by_sha: dict[str, Commit] = {}

    for ref in refs:
        # Strip refs/heads/ or refs/remotes/origin/ for display.
        pretty_ref = ref.replace("refs/heads/", "").replace("refs/remotes/", "")
        for raw in _commits_on_ref(repo, ref, author, since_iso):
            sha = raw["sha"]
            if sha in by_sha:
                if pretty_ref not in by_sha[sha].branches:
                    by_sha[sha].branches.append(pretty_ref)
                continue
            by_sha[sha] = Commit(
                sha=sha,
                author_name=raw["author_name"],
                author_email=raw["author_email"],
                authored_at=raw["authored_at"],
                subject=raw["subject"],
                body=raw["body"],
                branches=[pretty_ref],
                files_changed=raw["files_changed"],
                insertions=raw["insertions"],
                deletions=raw["deletions"],
            )

    commits = list(by_sha.values())
    commits.sort(key=lambda c: c.authored_at, reverse=True)
    return commits


def build_payload(commits: Iterable[Commit], author: str, days: int) -> dict:
    return {
        "author": author,
        "window_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_count": len(list(commits)) if not isinstance(commits, list) else len(commits),
        "commits": [asdict(c) for c in commits],
    }


SYSTEM_PROMPT = """You write short, human-sounding engineering status updates.

You will receive a JSON payload describing one developer's git commits over a
recent window. Write ONE paragraph (3-5 sentences) summarizing what they
worked on. Group related commits. Use plain language. Mention concrete
artifacts (files, features, fixes) when they're informative, but don't list
SHAs or stats. Don't editorialize about effort or quality. Don't start with
"This week" or "In the last N days" - just describe the work.

If the payload is empty, say so briefly.
"""


def call_claude(payload: dict, model: str = "claude-sonnet-4-5") -> str:
    # Imported lazily so --dry-run works without the SDK installed.
    from anthropic import Anthropic

    client = Anthropic()  # picks up ANTHROPIC_API_KEY from env
    message = client.messages.create(
        model=model,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": json.dumps(payload, indent=2),
            }
        ],
    )
    # Concatenate any text blocks in the response.
    parts = [b.text for b in message.content if getattr(b, "type", None) == "text"]
    return "".join(parts).strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.getcwd(), help="Path to git repo (default: cwd)")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default: 7)")
    parser.add_argument("--author", default=None, help="Author email (default: git config user.email)")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, skip the Claude call")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Anthropic model id")
    parser.add_argument("--payload-out", default=None, help="Also write the payload JSON to this path")
    args = parser.parse_args(argv)

    author = args.author or _current_user_email(args.repo)
    if not author:
        print("Could not determine author. Pass --author or set git config user.email.", file=sys.stderr)
        return 2

    commits = collect_commits(args.repo, author, args.days)
    payload = build_payload(commits, author, args.days)

    if args.payload_out:
        with open(args.payload_out, "w") as f:
            json.dump(payload, f, indent=2)

    if args.dry_run:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not commits:
        print(f"No commits by {author} in the last {args.days} days.")
        return 0

    paragraph = call_claude(payload, model=args.model)
    print(paragraph)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
