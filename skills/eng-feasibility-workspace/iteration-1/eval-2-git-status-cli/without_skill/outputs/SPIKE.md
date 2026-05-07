# Day 0 spike: `gitstatus` CLI

## What we're testing
A CLI that reads a developer's recent git activity and asks Claude to write a one-paragraph status update.

## Load-bearing assumptions (in priority order)
1. **Git data is rich enough.** `git log` across all branches the user has authored on, in the last 7 days, gives Claude enough signal to write a useful paragraph. If the data is too thin (just commit subjects) or too noisy (full diffs blow the context window), the idea is dead.
2. **The "who am I" lookup is reliable.** We need a stable way to identify "this developer's commits" across branches. `git config user.email` is the obvious anchor, but on shared machines or rebased history it's not always right.
3. **The Claude call produces a paragraph that sounds like a human, not a changelog.** This is mostly a prompt-engineering problem and is the *only* thing we need an API key to validate.
4. **Latency and cost are fine for an interactive CLI.** One Sonnet call on ~2-5KB of input. Should be sub-3s and sub-$0.01. Worth confirming once, not designing around.

## What the spike validates today (no key needed)
- Git collection: walk branches, filter by author, last N days, dedupe commits that appear on multiple branches.
- Shape of the prompt input: a compact JSON payload with `{branch, sha, date, subject, body, files_changed, insertions, deletions}` per commit.
- The prompt itself, written but not yet executed.

## What needs the key (deferred)
- Actually calling Claude and seeing the paragraph.
- Tuning the prompt for tone (status update vs. changelog vs. brag doc).
- Deciding whether to include diffs, file lists, or just subjects.

## What I'd cut from the spike
- No config file. Flags are enough.
- No caching. One run, one call.
- No multi-developer support. Single `user.email`.
- No GitHub/Linear integration. Just git.
- No tests beyond the smoke script. This is a spike.

## Open questions for after the spike
- Do we want PR titles/descriptions in the input? That requires a GitHub token and changes the auth story.
- Should it post to Slack directly, or just print to stdout? Stdout for the spike; piping to `slack-cli` is trivial later.
- How do we handle merge commits and squash-merges where authorship gets rewritten? Probably filter `--no-merges` and accept the loss.

## Files in this spike
- `gitstatus.py` — the CLI, single file, runnable when `ANTHROPIC_API_KEY` is set.
- `requirements.txt` — `anthropic` only.
- `smoke_test.sh` — runs the git-collection half against the current repo and dumps the JSON payload that *would* be sent to Claude. Usable today.
- `sample_payload.json` — output of `smoke_test.sh` against this repo, captured day 0.
- `SPIKE.md` — this file.
