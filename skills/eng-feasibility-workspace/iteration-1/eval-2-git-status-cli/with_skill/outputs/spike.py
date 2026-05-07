#!/usr/bin/env python3
"""
Spike: git-history -> Claude -> 1-paragraph status update.

Walks the real user flow end-to-end:

    [pick repo / author] -> [harvest git log] -> [show raw log to user]
        -> [call Claude] -> [show paragraph] -> [user judges: paste? edit? bullets?]

Single file by design. Real Anthropic API call (no mock). Hardcoded
config at the top; CLI args override. Prints inputs, intermediate
values, timings, and token counts so we can fill tradeoffs.md as
we run.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python spike.py                              # uses defaults
    python spike.py --repo ~/code/foo --author "Mila Wilson"
    python spike.py --days 7 --model claude-sonnet-4-5

Requirements:
    pip install anthropic
    git on PATH
"""

import argparse
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------
# Hardcoded inputs (override via CLI). Spike-style: tweak in place.
# ---------------------------------------------------------------
DEFAULT_REPO = os.path.expanduser("~/Dev/agent-dri-skills")
DEFAULT_AUTHOR = None  # None -> use `git config user.name`
DEFAULT_DAYS = 7
DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_COMMITS_TO_SEND = 80  # safety bound; trim if a dev had a wild week


# ---------------------------------------------------------------
# Step 1: harvest git history.
# ---------------------------------------------------------------
def run_git(repo: str, args: list[str]) -> str:
    out = subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def resolve_author(repo: str, author: str | None) -> str:
    if author:
        return author
    return run_git(repo, ["config", "user.name"]).strip()


def harvest_commits(repo: str, author: str, days: int) -> tuple[str, dict]:
    """
    Pull commits authored by `author` in the last `days` days, across
    *all branches the local repo knows about* (--all). Skip merges and
    dedup by patch-id so squash-merges into main don't double-count.

    Returns (formatted_log_text, stats_dict).
    """
    # --all: every ref, including remotes; that's how we get "branches
    # the dev has committed on" without enumerating them by name.
    # --no-merges: merge commits are noise for a status update.
    # cherry-mark via patch-id dedup happens below.
    # Format design (debugged in the spike — see tradeoffs.md F1):
    #   record separator: 0x1e
    #   field separator inside the metadata line: 0x1f
    #   body has its own marker so we can strip it before parsing files
    # `git log --name-only` appends the changed file list AFTER the
    # pretty body, separated by a blank line. That is what makes
    # parsing "metadata then files" tractable — but only if the
    # metadata is single-line. Hence 0x1f instead of \t/space, and
    # body wrapped in <BODY>...</BODY> so newlines in it don't fool us.
    raw = run_git(
        repo,
        [
            "log",
            "--all",
            "--no-merges",
            f"--since={days}.days.ago",
            f"--author={author}",
            "--pretty=format:%H%x1f%h%x1f%ad%x1f%D%x1f%s%x1f<BODY>%b</BODY>%x1e",
            "--date=short",
            "--name-only",
        ],
    )

    # Records are separated by 0x1e (record separator).
    raw_records = [r.strip() for r in raw.split("\x1e") if r.strip()]

    # Dedup by patch-id (catches squash-merge duplicates between
    # feature branch and main).
    seen_patch_ids: set[str] = set()
    deduped: list[dict] = []
    bot_signals = ("dependabot", "renovate", "github-actions")
    bot_skipped = 0
    dup_skipped = 0

    for rec in raw_records:
        # Split metadata from files. Files are everything after the
        # closing </BODY> marker, separated from it by a newline.
        body_close = rec.find("</BODY>")
        if body_close == -1:
            continue
        meta_chunk = rec[: body_close + len("</BODY>")]
        files_chunk = rec[body_close + len("</BODY>") :].strip()

        parts = meta_chunk.split("\x1f")
        if len(parts) < 6:
            continue
        full_hash, short, date, refs, subject, body_wrapped = parts[:6]
        body = body_wrapped.removeprefix("<BODY>").removesuffix("</BODY>").strip()
        files = files_chunk

        # Skip obvious bot commits even if author filter let them through.
        if any(b in subject.lower() for b in bot_signals):
            bot_skipped += 1
            continue

        # patch-id dedup
        try:
            pid_out = subprocess.run(
                ["git", "-C", repo, "show", full_hash],
                capture_output=True, text=True, check=True,
            )
            pid = subprocess.run(
                ["git", "patch-id", "--stable"],
                input=pid_out.stdout, capture_output=True, text=True, check=True,
            ).stdout.split()
            patch_id = pid[0] if pid else full_hash
        except subprocess.CalledProcessError:
            patch_id = full_hash

        if patch_id in seen_patch_ids:
            dup_skipped += 1
            continue
        seen_patch_ids.add(patch_id)

        deduped.append({
            "hash": short,
            "date": date,
            "refs": refs,
            "subject": subject,
            "body": body.strip(),
            "files": [f for f in files.split("\n") if f.strip()],
        })

    if len(deduped) > MAX_COMMITS_TO_SEND:
        truncated = len(deduped) - MAX_COMMITS_TO_SEND
        deduped = deduped[:MAX_COMMITS_TO_SEND]
    else:
        truncated = 0

    # Format for the model. Keep it terse but include refs so the
    # model can group by branch if it chooses.
    lines = []
    for c in deduped:
        line = f"{c['date']}  [{c['hash']}]  ({c['refs'] or 'no-ref'})  {c['subject']}"
        if c["body"]:
            line += f"\n    body: {c['body'][:200]}"
        if c["files"]:
            line += f"\n    files: {', '.join(c['files'][:8])}"
            if len(c["files"]) > 8:
                line += f" (+{len(c['files']) - 8} more)"
        lines.append(line)

    formatted = "\n".join(lines)
    stats = {
        "raw_records": len(raw_records),
        "after_dedup": len(deduped),
        "bot_skipped": bot_skipped,
        "dup_skipped": dup_skipped,
        "truncated": truncated,
    }
    return formatted, stats


# ---------------------------------------------------------------
# Step 2: ask Claude for a paragraph.
# ---------------------------------------------------------------
SYSTEM_PROMPT = """\
You are summarizing a developer's recent git activity into a single
paragraph they could paste into a standup channel.

Rules:
- Output ONE paragraph. No bullet list. No headers. No preamble.
- Concrete: name the actual features, fixes, and areas touched —
  pull from commit subjects, file paths, and refs.
- Group by theme, not by commit. If a branch clearly maps to one
  effort, describe the effort, not the commits.
- Do not invent work, tickets, teammates, or outcomes. If the log
  is sparse, say so plainly.
- Use first person, past tense, plain prose. No emoji. No marketing.
- 60-110 words is the target. Hard cap at 130.
"""

USER_TEMPLATE = """\
Here is my git log for the last {days} days across all branches I've
committed on. Generate a single-paragraph status update I can paste
into standup.

Author: {author}
Repo: {repo}
Commits (after filtering merges, bots, and squash-dup):

{log}
"""


def call_claude(model: str, repo: str, author: str, days: int, log: str) -> tuple[str, dict]:
    # Imported lazily so `python spike.py --help` works without the SDK.
    try:
        from anthropic import Anthropic
    except ImportError:
        sys.exit("Install the SDK first: pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "ANTHROPIC_API_KEY not set. The spike is wired for the real API; "
            "set the key and re-run. (No mock path on purpose.)"
        )

    client = Anthropic()
    user_msg = USER_TEMPLATE.format(days=days, author=author, repo=repo, log=log)

    t0 = time.time()
    resp = client.messages.create(
        model=model,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    elapsed = time.time() - t0

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    meta = {
        "elapsed_s": round(elapsed, 2),
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "model": resp.model,
        "stop_reason": resp.stop_reason,
    }
    return text.strip(), meta


# ---------------------------------------------------------------
# Step 3: walk the user flow. This is where IA problems surface.
# ---------------------------------------------------------------
def walk_user_flow(paragraph: str, stats: dict, meta: dict) -> None:
    """
    Stand in for the real CLI UX. The point of running this is *not*
    to validate the model — it's to feel whether a single paragraph
    is the right shape.
    """
    print()
    print("=" * 72)
    print("PARAGRAPH (this is what would print in the real CLI):")
    print("=" * 72)
    print(paragraph)
    print()
    print("=" * 72)
    print("META")
    print("=" * 72)
    for k, v in {**stats, **meta}.items():
        print(f"  {k}: {v}")

    print()
    print("=" * 72)
    print("USER-FLOW JUDGMENT (answer honestly, this fills tradeoffs.md):")
    print("=" * 72)
    questions = [
        "1) Would you paste this into standup with at most one small edit? (y/n/edit)",
        "2) Does it cover the week's actually-important work? (y/n)",
        "3) Is the level of detail right for standup? (y/too-thin/too-thick)",
        "4) Did it hallucinate anything (work, teammates, tickets)? (y/n + what)",
        "5) Would you want a different shape — bullets, per-branch, daily? (no/bullets/per-branch/daily)",
    ]
    for q in questions:
        try:
            ans = input(f"{q}\n> ").strip()
        except EOFError:
            ans = "(skipped — no tty)"
        print(f"   recorded: {ans}")
    print()
    print("Copy these answers into tradeoffs.md under the relevant assumption.")


# ---------------------------------------------------------------
# Entry point.
# ---------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="Spike: git history -> Claude paragraph")
    p.add_argument("--repo", default=DEFAULT_REPO)
    p.add_argument("--author", default=DEFAULT_AUTHOR)
    p.add_argument("--days", type=int, default=DEFAULT_DAYS)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--no-prompt", action="store_true",
                   help="Skip the user-flow questions (for batch runs).")
    args = p.parse_args()

    repo = os.path.abspath(os.path.expanduser(args.repo))
    if not os.path.isdir(os.path.join(repo, ".git")):
        sys.exit(f"Not a git repo: {repo}")

    author = resolve_author(repo, args.author)

    print(f"repo:   {repo}")
    print(f"author: {author}")
    print(f"days:   {args.days}")
    print(f"model:  {args.model}")
    print()

    print("--- harvesting commits ---")
    log, stats = harvest_commits(repo, author, args.days)
    print(f"stats: {stats}")
    if not log:
        sys.exit("No commits found. Try a wider window or check --author.")
    print()
    print("--- raw log fed to model (truncated to first 60 lines for display) ---")
    for ln in log.splitlines()[:60]:
        print(ln)
    if len(log.splitlines()) > 60:
        print(f"... (+{len(log.splitlines()) - 60} more lines)")
    print()

    print("--- calling Claude ---")
    paragraph, meta = call_claude(args.model, repo, author, args.days, log)

    if args.no_prompt:
        print(paragraph)
        print(f"meta: {meta}")
        return

    walk_user_flow(paragraph, stats, meta)


if __name__ == "__main__":
    main()
