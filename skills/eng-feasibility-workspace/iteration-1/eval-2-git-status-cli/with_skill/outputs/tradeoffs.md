# Tradeoffs — Git Status CLI Spike

Run context: spike harness exercised end-to-end against the
`agent-dri-skills` repo (this repo) with `days=90` to pull 20
real commits. Anthropic call **not executed** in this session
(no API key in the environment, on purpose — the spike is
wired for the real API and fails loudly if the key is absent;
no mock path was added). M1's row is therefore **deferred**
with a clear continuation plan, not "passed by inspection."
M2 and M3 produced real findings on day 0 from the harvest
walkthrough alone.

## Strongest finding first

**The `--pretty=format:…%b` + `--name-only` combination is a
parsing trap.** The first run silently collapsed 20 commits into
1 because newlines inside commit bodies were eaten by the
record-splitter. The spike would have shipped a model that
summarized 1 commit per week if we hadn't run the harvester
on real data. That alone justifies the spike — see F1 below.

---

## Must-hold assumptions

### M1 — Claude can turn raw `git log` into a useful 1-paragraph status update

| Field | Value |
|---|---|
| **Assumption** | Across 5 hand-picked git logs, Claude returns a paragraph the dev would paste with at most one small edit. No hallucinated work. |
| **Gate** | ≥4/5 "would paste with ≤1 edit"; 0/5 hallucinations. |
| **Result** | **Deferred — no API key in environment.** Spike is runnable; gate is unchanged; the walk-the-flow harness is in place (`walk_user_flow()` prompts the dev for all five gate questions per run). |
| **Learning** | The user-flow scaffolding works — `walk_user_flow` prints inputs/outputs/timings/tokens and prompts the dev for the five gate questions inline. That means when the key is added, the gate evaluation is a 5-run loop, not a write-the-eval-script side quest. |
| **Pivot** | None yet. Re-open this row on the first real run. If hallucination shows up, the pivot is to constrain the prompt with explicit "only mention work present in the provided log" instruction and add a post-check that every claimed feature/file appears in the log text. |

### M2 — A single paragraph is the right shape (IA / user-flow bet)

| Field | Value |
|---|---|
| **Assumption** | A 1-paragraph summary feels useful as a daily-standup substitute and groups multi-branch work in a way the dev recognizes. |
| **Gate** | On 5 samples: (a) covers important work, (b) right level of detail, (c) recognizable to a teammate — yes on all three for ≥4/5. If "I want bullets / per-branch / daily" wins on ≥3/5, IA is wrong. |
| **Result** | **Partial finding even before the API call: the "group by branch" affordance is largely fictional in real repos.** See F2. |
| **Learning** | `git log --pretty=...%D...` returns the refs a commit is *currently* the tip of, not the branch it was developed on. On a developer who merges via squash + branch-delete (the common GitHub flow), almost every commit comes back with `%D` empty. In our test run, **0 of 19 commits had a branch ref attached.** The model literally cannot "group by branch" because the data doesn't carry that signal. |
| **Pivot** | **Architecture pivot — likely.** Two options: (1) Drop the per-branch IA pretense; lean into the paragraph summarizing *themes* (the model is good at this from subjects + file paths). (2) Reconstruct branch context via `git reflog` of `HEAD` + local branch names + remote tracking refs, which is fiddly and only partly works. **Recommendation: ship option 1.** This also makes M2's gate cleaner: if the paragraph is good *without* explicit branch grouping, the IA is simpler than originally framed. If users keep asking "what branch was this on?" we add that in v2. |

### M3 — `git log` gives the right slice without too much noise

| Field | Value |
|---|---|
| **Assumption** | Harvested commits match what the dev would honestly claim as "this week's work," with ≤20% noise. |
| **Gate** | On a real working repo, ≤20% of harvested commits are merge/bot/squash-dup noise after filters. |
| **Result** | **Pass on this repo.** 20 raw → 19 deduped after `--no-merges` + bot filter + patch-id dedup. 0 bot commits, 1 patch-id duplicate (a re-applied commit, correctly removed). Noise rate ≈5%. The `MAX_COMMITS_TO_SEND=80` safety bound did not trigger. |
| **Learning** | Two unexpected findings: (i) `--all` does the right thing implicitly — we don't need to enumerate "branches the dev has committed on" by name; the author filter on `--all` is the spec. (ii) `git patch-id --stable` dedup catches squash-merges between feature branches and main, which `--no-merges` alone does not. This is the right primitive. |
| **Pivot** | **No architecture change** — but two small adds for the build: (a) Detect `chore(deps):` / `bump:` / version-only commits as additional bot-ish noise, since `dependabot` substring isn't always in the subject. (b) Surface the `stats` dict to the user in `--verbose` mode so they can sanity-check what was sent to the model — this is the cheapest hallucination guardrail. |

---

## Findings (side observations from running the spike)

These are spike outputs that aren't a gate result but reshape
the build plan.

### F1 — `--pretty=format:…%b` + `--name-only` silently corrupts records

- **What.** First parser used `\t` as field separator and `\n.partition` to split metadata from the file list. Commit bodies (`%b`) contain newlines and tabs, so 20 raw records collapsed to 1.
- **Evidence.** Stats from first run: `{raw_records: 20, after_dedup: 1}`. Stats after fix: `{raw_records: 20, after_dedup: 19}`.
- **Fix.** Switched to `\x1f` field separator inside the metadata, wrapped body in `<BODY>…</BODY>` so the parser can find a stable boundary before the `--name-only` file list.
- **So-what.** Without the spike, the build would have shipped a tool that always summarized one commit. The "real services, not mocks" rule earned its keep here — the bug only appears against actual git output.

### F2 — `%D` is empty for most commits in modern GitHub flows

- **What.** Of 19 deduped commits in the test repo, 0 had a non-empty `%D` ref decoration.
- **Why.** `%D` is the refs the commit *is currently the tip of*. After squash-merge + branch-delete (the default GitHub PR flow), the commit is no longer at the tip of any branch — it's just a node on `main`'s history.
- **So-what.** Drives the M2 pivot: the project should not promise "grouped by branch" in its UX or prompt. The paragraph should group by theme, which is what Claude is good at and what the data supports.

### F3 — Patch-id dedup is necessary but slow

- **What.** `git patch-id --stable` runs one subprocess per commit. On 20 commits this is fine; on a 7-day window for an active dev (~30 commits), it's still <1s. On a 30-day window or a monorepo, it's noticeable.
- **So-what.** Acceptable for the v1 build at the proposed 7-day default. Note as a should-hold for any future "monthly summary" mode.

---

## Should-hold (logged as risks)

- **S1 latency.** Not measured (no API call this session). Anthropic's published p50 makes <10s near-certain for ~5KB inputs. The spike prints `elapsed_s` and `input_tokens` so it self-measures on the first real run.
- **S2 cost.** Token count for the 19-commit log was ~1,200 chars ≈ 350 tokens of input. At Sonnet 4.5 input pricing, well under $0.001/run. Not a risk.
- **S3 cross-repo.** Out of scope for v1; one-repo-per-invocation is the right shape.

---

## Decision

**Build, with one architecture pivot.**

- M1 is deferred to first real run; the spike is runnable end-to-end the moment a key is provided, and the user-flow harness is in place to evaluate the gate on 5 samples.
- M2 found a real IA problem (`%D`-based branch grouping is fictional). Pivot: don't promise per-branch grouping; let the model group by theme. This is a *simpler* shipping plan than the original sketch.
- M3 passed; the data-shape primitives (`--all` + `--no-merges` + bot-substring + `patch-id` dedup) are correct.
- F1 caught a real parser bug that would have shipped without the spike.

The build can start. Concrete next steps before the v1:

1. Run the spike against ≥5 real repos with the API key, fill M1 row, run the user-flow questions for each.
2. If M1 passes, lift `harvest_commits` and `call_claude` more or less verbatim into the production CLI; they're already small and dependency-light.
3. Add the F2-driven prompt change ("group by theme; do not invent branch names") and the F1-driven parser format to the v1 spec.
4. Defer per-branch grouping, monorepo support, and streaming output to v2.
