# Decision — Git Status CLI

## Should we have spiked at all?

Yes — barely.

The skill's "do not use when…" criteria almost ruled this out:
the project is small, the Anthropic SDK and `git log` are both
well documented, and a senior engineer could plausibly skip
straight to a build. But two of the project's load-bearing
questions are not answerable from the docs:

1. **Will Claude actually produce a paragraph the dev wants to
   paste?** Behavior bet on the model. Docs can't answer this.
2. **Does a single paragraph hang together as the user-facing
   shape?** IA bet — exactly what the skill says spikes catch
   cheapest.

A 90-minute spike was the right size. Half a day would have
been over-investment; "just build" would have shipped two
real bugs (see F1 and F2 in `tradeoffs.md`).

## Decision: **build, with one architecture pivot**

### What carries forward verbatim

- The harvester (`harvest_commits` in `spike.py`): `--all`
  filters by author across every ref the local repo knows;
  `--no-merges` + bot-substring + `git patch-id --stable`
  dedup is the right noise filter; the `\x1f` + `<BODY>...</BODY>`
  pretty format is the safe parser shape.
- The single Anthropic call shape and system prompt (one
  paragraph, no preamble, 60-110 words, no invention).
- The user-flow walkthrough (`walk_user_flow`) becomes the
  first internal eval harness — the same five questions are
  the v1 acceptance test.

### What pivots

- **Drop the per-branch grouping pretense.** The original idea
  implied output grouped by the branches the dev had committed
  on. In real repos, `%D` is empty for most commits because
  squash-merge + branch-delete strips that signal. The model
  cannot group by something the data doesn't carry. Lean into
  *theme*-grouped paragraphs instead — what Claude is actually
  good at given subjects + file paths.
- **Add a `--verbose` flag that prints the harvested log** before
  the paragraph. Gives the dev a one-glance hallucination check
  without building a separate verifier.

### What's deferred

- M1's gate evaluation — runnable now; needs a key + 5 hand-picked
  repos. Adds ~1 hour the moment the key arrives.
- Cross-repo summaries, streaming, monorepo perf — v2 at earliest.

## Build sizing

- v1 spec: ~1 day. The spike already wrote ~75% of the code
  worth keeping; production work is CLI ergonomics
  (`--days`, `--repo` defaults, `--verbose`, exit codes), a
  proper `pyproject.toml`, and a small README.
- v1 acceptance: the five user-flow questions in
  `walk_user_flow`, run on five real repos, ≥4/5 pass.

## What would have flipped this to "stop" or "pivot narrative"

- If F2 had shown that the dev *needed* per-branch grouping to
  make sense of the output, and `%D` couldn't supply it, the
  pivot would have been heavier (reflog parsing, GitHub API
  cross-reference). That would push v1 from ~1 day to ~1 week
  and is the kind of finding that should change the project
  brief, not just the code.
- If M1 had failed on first runs (paragraph too generic /
  hallucinated), pivot narrative: reframe as "Claude-assisted
  draft" with explicit edit affordances rather than
  paste-and-go.
