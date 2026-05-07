# Assumptions — Git Status CLI

## Project frame

- **What it is.** A CLI a developer runs locally that reads their
  recent git history (last 7 days, current branch + all branches
  they've committed on) and prints a 1-paragraph status update
  written by Claude.
- **Who it serves.** An individual engineer who needs to write a
  daily/weekly standup update and would rather paste-and-edit
  than write from scratch.
- **What ships.** One installable script (`gitstatus`) that
  reads `$ANTHROPIC_API_KEY`, runs `git log`, calls Claude,
  prints a paragraph.

## Core hypothesis (falsifiable)

> Given a developer's last-7-day git log across the branches
> they've authored on, Claude can produce a single paragraph
> that the developer would paste into Slack/standup with at
> most one small edit, in under ~10 seconds, and for less than
> a cent per run.

## Must-hold assumptions (spike these)

### M1. Behavior — Claude can turn raw `git log` into a useful 1-paragraph status update.
- **Why load-bearing.** If the paragraph is generic, hallucinated,
  or so terse it adds no value, the project does not exist —
  the dev will keep writing standups by hand.
- **Gate.** Across 5 hand-picked sample git logs (mine over the
  last few weeks, plus 2-3 from teammates / public repos), at
  least 4/5 outputs are judged "would paste with at most one
  small edit" by the author of the commits. No hallucinated work
  (claims a commit did something it didn't), no
  invented teammates, no invented tickets.

### M2. Information architecture / user flow — a single paragraph is actually the right shape for "what I did this week."
- **Why load-bearing.** This is the IA bet the skill warns about.
  If a paragraph compresses too much detail (5 PRs across 3
  branches → "worked on various features"), the dev will want
  bullets, or per-branch grouping, or grouped-by-day. We need to
  *walk the flow* (run it, read the output, ask "would I send
  this?") to know.
- **Gate.** On the same 5 samples, the author can answer yes to
  *all three*: (a) "does this paragraph cover the week's
  actually-important work?", (b) "is the level of detail right
  for standup — neither one-liner nor wall-of-text?", (c) "if I
  saw a teammate post this, would I know what they actually
  did?" If any of (a)/(b)/(c) flips to "I want bullets / I want
  grouping / I want more detail per branch" on ≥3 of 5 samples,
  the IA is wrong and we pivot the output shape (bullets per
  branch, or per-PR, or daily).

### M3. Data shape — `git log` across "branches the dev has committed on" returns the right slice without too much noise.
- **Why load-bearing.** Easy to assume, easy to get wrong.
  `git log --author=me --since=7.days --all` returns commits on
  *any ref the local repo has fetched*, including merge commits,
  squashed-into-main duplicates, and stale branches. If 50% of
  the lines we feed the model are noise (re-merges, automated
  bumps), M1 will fail for the wrong reason.
- **Gate.** On a real working repo (mine), the harvested commits
  match what the dev would honestly claim as "work I did this
  week," with ≤20% noise rate (merge commits, bot commits, dup
  squashes counted as noise). If noise is high, we filter
  (`--no-merges`, dedup by patch-id, drop bot authors) inside the
  spike before pivoting the architecture.

## Should-hold assumptions (note as risks; test only if cheap)

- **S1. Latency.** Single Claude call returns in <10s.
  *Anthropic SLA + a few-thousand-token input → very likely. Log
  the timing in the spike; don't gate on it.*
- **S2. Cost.** <$0.01 per run with Sonnet. *7 days of commits is
  small input; near-certain. Log token counts.*
- **S3. Cross-repo.** Most devs work in one repo at a time for a
  given standup; we can punt multi-repo to v2. *Note as a
  product question, not a spike question.*

## Nice-if-it-holds (do not spike)

- N1. Output is markdown-rendered nicely in Slack.
- N2. CLI runs without flags (sensible defaults).
- N3. Streaming output for snappier feel.

## Time-box

Half a day. The spike is one file, ~150 lines, and the
hand-picked inputs are repos the engineer already has on disk.
If by lunch we don't have outputs to judge, reset — likely M3
(data shape) is harder than expected and the architecture
needs a rethink before more code.
