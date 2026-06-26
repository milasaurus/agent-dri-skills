---
name: code
description: Staff-level code review with two lenses — a simplification lens (when to clean up code that works) and a design-smell lens (correctness and architecture issues a cleanup pass misses — persisted-vs-derived state, soft-vs-hard enforcement, drifted invariants, contingent properties, single-source-of-truth violations). Prioritizes hot spots, leverage points, and alignment with the codebase's direction. Produces a clear disposition per candidate — simplify now, with conditions, encode as standard, leave it, defer, or needs more context.
trigger:
  - "A pull request or branch is ready for a staff-level code review."
  - "A team asks whether code that works is also clean enough to maintain."
  - "An engineer flags accumulated complexity and asks where to invest first."
  - "A change introduces a new field, mode, flag, or stored state and you want the design reviewed, not just the style."
archetypes:
  - staff-reviewer
  - tech-lead
  - reviewer
  - design-reviewer
---

## Overview

This skill encodes how a staff engineer evaluates code for
simplification — the judgment about when to leave code alone,
when to invest in cleanup, and which simplifications actually
pay off versus which are churn.

The default failure mode of an enthusiastic simplification pass
is over-simplification: a refactor that touches thirty files,
makes the diff unreviewable, and trades one shape of complexity
for another. Staff engineers do less, but the simplifications
they do make have outsized payoff. They prioritize hot spots,
leverage points, and alignment with the codebase's direction —
in that order — and they leave stable, readable code alone.

The skill is review-oriented. The output is a prioritized set
of recommendations with explicit dispositions, not a rewrite.

## When to Use

Use this skill when:

- a pull request has accumulated complexity and the reviewer or
  author wants to know what to clean up before merging,
- a code area has been the source of repeat bugs, oncall pages,
  or repeated review questions, and the team wants to know
  whether simplification would help,
- an engineer is about to invest in an unfamiliar area and
  wants a staff-level read on what is worth simplifying first,
- code review surfaces "this feels heavier than it should" but
  no specific change has been proposed yet.

Do not use this skill when:

- the code is on a hot path of imminent rewrite — simplifying
  disposable code is wasted effort,
- the code is performance-critical and a "simpler" version
  would be measurably slower (different lens: performance review),
- the request comes with no scope ("clean up the codebase") —
  push back and ask for a specific surface,
- the reviewer has not read the code carefully enough to apply
  Chesterton's Fence — go understand the code first.

## Staff Mental Model

Staff engineers do not simplify code they do not understand,
and they do not simplify code that is not going to change.
Two filters apply before any pattern matching:

1. **Will this code change again?** If a module is stable and
   nobody touches it, simplification is cosmetic. Spend the
   time on code that gets edited every sprint.
2. **Do I understand why it is written this way?** If you
   cannot answer, you are not ready to recommend changes.
   Read the call sites, check `git blame`, and confirm the
   tests cover the behavior.

Once both filters pass, prioritize simplification effort in this
order. This mirrors Will Larson's investment hierarchy for
technical quality, applied to a single review:

1. **Hot spots first.** Code currently causing bugs, slow PRs,
   repeated review questions, or oncall pages. Highest-confidence
   surface — the system is already telling you it needs help.
2. **Best practices.** Apply project conventions and
   well-established patterns: guard clauses, descriptive names,
   deletion of dead code. Low-controversy and mechanical.
3. **Leverage points.** Interfaces with many callers, error
   paths, stateful logic, control flow at module boundaries.
   High payoff per change — every consumer benefits.
4. **Vector alignment.** Pull simplifications in the direction
   the codebase is moving. If the team is migrating from
   pattern A to B, simplifications should reinforce B, not
   polish A.

**Escalate repetition to standards and automation.** When the
same simplification recommendation appears across multiple
files or PRs, the issue is not a per-file problem — it is a
team-alignment or tooling problem. Two staff-eng moves apply:

- **Establish clear standards.** Document what good code looks
  like in this codebase — naming, error handling, control-flow
  conventions, when to abstract. Encourage open discussion of
  borderline cases. A documented standard converts every future
  review of the same shape from "judgment call" to "alignment
  check," and gives engineers a stable reference instead of
  asking the same questions in every PR.
- **Automate checks.** Use linters, formatters, type checkers,
  and test patterns to catch a class of issues mechanically.
  Every issue caught manually that could be caught
  automatically is a process tax the team pays on every PR.
  If a review surfaces the same complaint three times across
  three files, the third instance is a signal to recommend a
  lint rule, not edit the third file.

Steps beyond a single review — measuring quality, standing up a
quality team, running a quality program — are organizational
work. Note when they are missing, but do not try to enact them
inside one simplification pass.

## Process

1. Scope and gate
   - Confirm the specific code surface in scope. Push back on
     requests with no boundary.
   - Confirm why the review is happening now — imminent feature
     work, repeat bug, onboarding. The reason shapes priority.
   - Check whether this code is likely to change in the next
     month. If not, the most valuable feedback may be "defer."
   - Check whether tests pin the current behavior. Without
     tests, every simplification carries higher regression risk
     and that should weight every disposition.

2. Identify hot spots
   - Use `git log --since="3 months ago"` to find files with
     high churn. Repeat-edit code is repeat-pain code.
   - Look for functions whose history is mostly bugfix commits.
     The code keeps breaking; simplification probably helps.
   - Look for review patterns — areas where the same kind of
     comment appears repeatedly across PRs. The shape of the
     code is generating the comment.
   - Look for explicit signals in the code itself: `// TODO
     cleanup`, `// HACK`, `// I know this is bad`, defensive
     comments by the author asking "is this OK?"
   - Hot spots get the first dispositions. Address them before
     anything cosmetic.

3. Apply best practices within scope
   - Scan for the structural patterns below. For each, ask
     whether the codebase already has a convention — if yes,
     align with it; if no, recommend the lower-controversy
     option.

   **Structural complexity**
   - Deep nesting (3+ levels): replace with guard clauses or
     extract helpers. Worth fixing on hot paths and entry
     points; leave alone in one-call-site internal helpers.
   - Long functions (50+ lines): split when they hold multiple
     responsibilities. Length alone is not a reason to split.
   - Nested ternaries: replace with if/else, switch, or a
     lookup. Always worth fixing — they are pure cognitive tax.
   - Boolean parameter flags (`doThing(true, false, true)`):
     replace with options objects or separate functions when
     the call site has two or more callers and the flags
     control divergent behavior.
   - Repeated conditionals: extract to a named predicate when
     the same check appears in three or more places.

   **Naming and readability**
   - Generic names (`data`, `result`, `temp`): rename to
     describe content, especially on interfaces and across
     function boundaries.
   - Abbreviated names (`usr`, `cfg`, `evt`): use full words
     unless the abbreviation is universal in the codebase
     (`id`, `url`, `api`).
   - Misleading names (a `get*` function that mutates state):
     always worth fixing — the name is lying.
   - Comments explaining "what" the code does: delete; rely on
     names. Comments explaining "why" (workaround, constraint,
     non-obvious invariant): keep.

   **Redundancy**
   - Duplicated logic of five or more lines in three or more
     places: extract.
   - Dead code: unreachable branches, unused variables,
     commented-out blocks. Confirm via search/grep that they
     are truly dead, then delete.
   - Wrapper that adds no value: inline. But pause if the
     wrapper gives a concept a name — names are value.
   - Premature pattern (factory-for-a-factory, strategy with
     one strategy): replace with the simple direct path.
     Re-add the pattern when a second case actually appears.

4. Address leverage points
   - Interfaces and public APIs: many callers, expensive to
     change later. A confusing parameter name here costs every
     consumer. Prioritize over five cosmetic cleanups.
   - Error paths: confused error handling causes oncall pain.
     Untangling these has multiplicative value across every
     incident. Look for swallowed exceptions, generic catches
     that hide intent, and inconsistent error shapes.
   - Stateful logic: unclear state transitions become bugs.
     Make states and transitions explicit — enums, named
     status fields, exhaustive switches. Bias toward making
     invalid states unrepresentable.
   - Control flow at module boundaries: the entry point sets
     the cognitive cost for every contributor. Spend more
     simplification budget here than on internal helpers.

5. Check vector alignment
   - Before recommending a simplification, ask: does it pull
     in the direction the codebase is moving?
   - If the team is migrating from class to function
     components, do not idiomize a class component.
   - If a deprecation is in flight, do not invest in cleaning
     up the deprecated surface — accept the rough edges.
   - If the codebase is moving toward typed configs, do not
     simplify by stuffing more into untyped dicts.
   - Simplifications that fight the direction of change are
     net-negative even if they are locally cleaner.

6. Apply Chesterton's Fence to every candidate
   - Understand why the code was written this way: `git blame`,
     commit message, surrounding tests.
   - Confirm the original reason no longer applies.
   - Confirm tests pin the behavior you are preserving.
   - If you cannot answer these, downgrade the candidate to
     "needs more context" rather than recommending a change.

7. Look for repetition
   - Before issuing dispositions, group candidates by pattern.
     Count how often each pattern appears across the surface
     in scope and across recent history.
   - If the same candidate type recurs in three or more
     places, ask whether the right answer is a documented
     standard or a lint rule rather than three individual
     simplifications.
   - Repeating "rename `data` to something specific" across
     ten files is a request for a naming convention, not ten
     reviews.
   - Repeating "this should use a guard clause" across many
     functions is a request for a lint rule.
   - Check what tooling already exists. If there is a linter
     or formatter, can the rule be added to it? If there is no
     linter, the recommendation is "add one."

8. Produce dispositions
   For each candidate, return one of:
   - **Simplify now** — clear payoff, low risk, in scope.
   - **Simplify with conditions** — payoff is real but
     specific things must hold (tests must exist, must split
     into a separate PR, must wait for the deprecation to
     land).
   - **Encode as standard or lint rule** — the pattern repeats
     often enough that a documented convention or an automated
     check is more valuable than fixing each instance. The
     simplification still happens, but as a tooling or
     documentation change rather than a per-file edit.
   - **Leave it** — Chesterton's Fence holds, payoff is
     cosmetic, or the code is stable and out of scope.
   - **Defer** — worth doing but belongs in a separate effort,
     not this PR.
   - **Needs more context** — cannot make a confident call
     without information you do not have.

   Each disposition names a specific surface (file, function,
   symbol — or, for systemic dispositions, the rule and where
   it should live), the simplification, the payoff, and the
   cost. Dispositions without a surface are observations, not
   reviews.

## Design-Smell Lens

The process above asks "is this code harder to read than it
needs to be?" This lens asks a different question: "is this
design *wrong* in a way that will generate bugs or lifecycle
pain?" Run it as a second pass over the same diff. It shares
the gating discipline — understand the code first (Chesterton's
Fence), stay in scope, and ground every claim in the source at
the exact revision under review.

The unit of value here is naming the *pattern-class* behind a
change, not the line. A finding that says "this stored field is
derivable from the mode, so it drags filtering, throttle, and
cleanup machinery" lands and transfers; "rename this variable"
does not. For each lens below, the trigger question is the tool.

1. **Persisted vs derived state.** Is this stored when it is a
   pure function of other state? Stored-derived data drags
   lifecycle machinery behind it — visibility filtering,
   dedup/throttle, cleanup on the inverse operation, and drift
   when the copy disagrees with its source. Trigger: "what has
   to happen when this is created, hidden, and undone?" The fix
   is usually to recompute it at use time and delete the
   machinery. Disposition: leverage point — often
   `Simplify with conditions`, since removing a persisted field
   touches every writer and reader.

2. **Affordance vs guarantee (soft vs hard enforcement).** A
   UI label, mode, or flag implies a constraint ("read-only",
   "admin-only", "frozen"). Is it enforced by *capability*
   (impossible to violate) or by *instruction/convention*
   (trusted to be honored)? Name the gap plainly: "looks
   locked, only asked-nicely locked." Trigger: "is this a
   security boundary or a UX affordance — and is that an
   explicit, reviewed choice?" Soft enforcement is a legitimate
   choice; an *unexamined* soft constraint masquerading as a
   guarantee is the bug. Disposition: `Needs more context` —
   surface the decision to the author; if it must be a
   guarantee, the gate belongs in code, not prose.

3. **Stated invariant vs actual code.** Comments and docstrings
   assert invariants ("these two lists stay in sync", "the
   schemas are identical across paths") that other code quietly
   depends on. Trigger: "is the claim true, and what relies on
   it?" Verify the assertion against the code, then find the
   consumers of the assumption. A load-bearing comment that has
   drifted from the code is a latent bug with a long fuse.

4. **Contingent vs guaranteed property.** A desirable property
   ("these never collide", "this is always cached") may hold
   only by default and collapse under failover, a config
   override, a retry, or an equivalent-but-different runtime
   path. Trigger: "under what conditions does this stop being
   true?" Keep the caveat attached to the claim instead of
   stating the happy path as if it were invariant.

5. **Second-order effects / lifecycle.** Good design feedback
   states what a change *enables or removes*, not just what it
   does. For any new field, entity, or mode, trace the full
   lifecycle: who writes it, who reads it, is the store shared
   between actors, does it have complete CRUD — and, most
   revealing, what happens on the *inverse* operation
   (toggle-back, delete, exit, downgrade)? The bug usually
   hides in the inverse that nobody implemented.

6. **Single source of truth.** Is the same fact represented in
   two places that can disagree — a column and a JSONB key, a
   cache and its origin, a frontend constant and a backend
   enum? The fact need not be *data*: a version pinned in code
   *and* in a lockfile, a dependency resolved at several call
   sites, a constant duplicated across config and code are the
   same smell. Trigger: "if these drift, who wins, and how would
   we notice?" Collapse to one authoritative home and derive (or
   resolve from) the rest. Disposition: leverage point.

7. **Quantify the trade-off.** When a design choice is defended
   or attacked with "it's expensive" / "it's faster" / "it
   breaks the cache", do not accept the hand-wave. Find the
   actual marginal cost and the breakpoint. Often the feared
   cost is already paid elsewhere (a model swap already
   cold-started the cache, so a per-mode change adds nothing)
   or is bounded to a rare path. A number turns an argument
   into a decision.

Operationalize the lens like the simplification pass: walk the
diff once per question (or fan out one reviewer per lens on a
large change), name the pattern-class for each finding, then
**adversarially verify before reporting** — re-read the cited
code at the revision under review, re-check line numbers after
any rebase or merge, and watch for stale paths (a renamed or
obsolete directory) and claims that no longer hold at the
current head. When comparing two review passes, separate a real
code change from rater variance; do not report a different
score as a regression.

Design-smell findings carry the same disposition vocabulary as
simplification candidates, plus a one-line recommendation — and
a recommendation, not an option survey. If you are weighing two
fixes, name the one you would pick and why.

### Forcing discipline — run the lens blind, then enumerate

The lens only earns its keep if it runs *before* the answers
exist. Two failure modes make a review worthless even when every
lens above is "known":

- **Reviewing with the answer key.** If you have the PR's later
  commits, the bot comments, or the review threads in front of
  you, you will reverse-derive findings from the fixes and
  present them as if you predicted them. That is not a review —
  it is a changelog. Produce your design-smell findings from the
  **first commit alone**, write them down, and only then read
  the iteration history to score yourself. If you cannot run
  blind (the fixes are already in the diff under review), say so
  explicitly and review the *first commit's* state, not HEAD.
- **Having the lens but not walking it.** Knowing "persisted vs
  derived" exists does not surface the persisted field — you
  have to walk the diff once per question and force a yes/no on
  each new entity. The lens is a checklist to *execute*, not a
  glossary to cite after the fact.
- **Not re-reviewing the fix.** A fix is a change, and changes
  carry the same smells you were hunting — a fix can introduce a
  fresh single-source violation or strand a consumer. When a
  recommendation lands, re-run the lens on the fix itself.
  Especially when it changes a *shared* resolution, contract, or
  dependency — where a value comes from, what a constant resolves
  to, which binary runs — enumerate **every** consumer of the
  thing you touched. The classic miss is the N+1 site: you update
  two of the three places that read it and the third now
  disagrees. The tell that you skipped this is a fix that changes
  how something resolves with no grep for its other call sites.

**Forcing enumeration for any new mode / flag / stored field.**
When a diff introduces a mode, flag, status, or stored field,
do not free-associate — mechanically answer all of these, and
each "no" or "two places" is a finding:

1. **Enumerate every representation of the fact.** UI state,
   localStorage, request flag, JSONB key, typed column, in-memory
   context field. List them. Every pair that can disagree is a
   single-source-of-truth finding (lens 6).
2. **Is it derived?** If it is a pure function of other state,
   is it being *stored*? If so, what machinery does the storage
   drag — visibility filters, provenance, throttle, cleanup?
   (lens 1)
3. **Trace the inverse.** Toggle-back, exit, delete, downgrade —
   is it implemented? (lens 5)
4. **Trace the legacy / rename path.** If this renames or
   replaces an existing representation, what happens to *in-flight*
   state still carrying the old one? Enumerate every reader and
   writer of the old name across every layer. A rename that only
   updates the new reader silently strands old state. (lens 5)
5. **Same-turn ordering.** If the value can change mid-request,
   is anything stamped from a *cached copy* of it before the
   value is re-resolved? (lens 4)
6. **Constraint type.** If the mode implies a constraint
   (read-only, frozen, admin), is it a capability or an
   instruction — and is that gap an explicit, reviewed choice?
   (lens 2)

**Two architectural moves to recommend by name.** A staff review
does not stop at "this smells" — it names the refactor. These two
recur often enough to keep in the holster:

- **Persist → derive-at-render-time.** When a derived artifact
  (a synthetic message, a denormalized flag, a computed banner)
  is being persisted, recommend recomputing it at the boundary
  where it is consumed. The payoff is not the field — it is the
  *deletion of the machinery the field dragged*: provenance
  carve-outs, visibility filters, dedup/throttle bookkeeping.
  This is usually the single highest-leverage simplification in
  a stateful change.
- **Untyped bag → typed column / field.** When a new semantic
  value is being stuffed into a JSONB blob, a `dict` of options,
  or a stringly-typed bag, recommend promoting it to a typed
  column (or field) with a migration and a *documented legacy
  fallback read* during the transition. One authoritative home,
  indexable, type-checked, with a bounded drift window.

Recommend these proactively on commit one — they are the moves
that turn a working PR into a well-designed one, and surfacing
them early saves the iteration round that discovers them the
hard way.

### Guard & test completeness — does the check deliver what it claims

A guard, assertion, or CI job that *looks* like it enforces a
property but only enforces a weaker one is worse than none — it
buys false confidence. Two classes recur and are easy to miss
because the code reads as if the job is done:

- **Open-set assertion claiming to "lock."** A test whose
  docstring says "lock in the public surface" / "this can never
  grow" but asserts with a *subset/contains* check
  (`expected.issubset(actual)`, "x in result", "at least these
  keys") only catches *removals*, never *additions*. A new
  accidental export, leaked symbol, or extra field sails through.
  Trigger: "does this assertion fail when something is *added*,
  or only when something is *removed*?" The fix is a closed-set
  assertion (`actual == expected`, or an explicit allowlist that
  fails loudly with the diff). Disposition: `Simplify now` —
  the test already exists; it just has to actually bound the set.
- **New CI workflow that should mirror a sibling.** A workflow
  added to guard a new codegen/drift/schema check, while a
  sibling guard (`check-*-schema.yaml`, an existing drift job)
  already solved the same problems — dependency caching, store
  paths, frozen-lockfile installs, version pinning, concurrency
  groups. The new one silently drops them. Trigger: "is there an
  existing workflow of this shape, and does the new one match its
  setup?" Diff the new workflow against its nearest sibling and
  flag every step the sibling has that this one lacks — a missing
  cache is wasted minutes every run; a missing version pin is a
  byte-stability hole (the guard false-fails on an upstream
  release). Disposition: `Encode as standard` — the parity itself
  is the convention; if it recurs, a workflow template beats
  per-file review.

The unifying question for both: a guard is only as strong as the
*tightest* thing it actually checks, not the property its name or
docstring claims. Read the assertion, not the label.

### Weight findings by failure mode — silent beats loud

When findings outnumber what the team can act on, rank them by
*how the failure surfaces*, not by nominal severity alone. A
broken invariant that fails LOUD — a red CI check, a raised
exception, a crash on next deploy — is self-announcing; someone
will see it and fix it. One that fails SILENT — a page ships a
stale name, a guard quietly stops guarding, a derived value
drifts with no error — can sit in production for months. Two
findings of equal "severity" are not equal priority if one
screams and the other whispers.

For every guard, invariant, or new field, ask: "if this breaks,
is the failure loud or silent?" The silent one is the
higher-leverage finding and the one most worth a hard mechanism
(a gate, a raise, a CI check that *observes* the property). And
when a fix converts a silent failure into a loud one — raising
instead of returning a wrong value, a drift check that turns
stale data into a red build — that conversion is itself a
legitimate, often-sufficient resolution: the bug is not prevented
but it can no longer hide. Conversely, discount a loud-only
finding (an annoying false-fail that can never ship a wrong
result) below any silent one.

## Language-Specific Patterns

This section augments the language-agnostic process with idiomatic
patterns worth scanning for in specific languages. Project
conventions in `CLAUDE.md` and neighboring code always win over
this list. Add subsections for new languages as the repo expands.

### Python

Python's flexibility is a double-edged sword: easy structure means
easy *poor* structure, and the language gives the developer few
guardrails. The patterns below are drawn from the
[Hitchhiker's Guide to Python][1] (structure, style,
documentation, testing, gotchas) and chosen for staff-level
leverage. Each one either creates real bugs, blocks refactoring,
or taxes every future contributor — and each lists when it is
worth investing simplification effort versus when to leave it.

[1]: https://docs.python-guide.org/

**Structure** — module boundaries and dependency shape:

- **Circular imports between modules.** Modules that import each
  other bidirectionally produce import-time fragility and force
  workarounds like importing inside function bodies. The signal
  is decomposition — two modules are entangled and one of them
  is misfiled. Worth fixing when the cycle is in code that
  changes; the fix is usually a third module owning the shared
  concept. Disposition: `Simplify with conditions` — must land
  as a separate PR because renaming or moving symbols is risky.
- **Hidden coupling.** "Each change in `Table` breaks 20 tests
  in unrelated cases because it breaks `Carpenter`'s code." A
  signal that one module embeds unstated assumptions about
  another. High-leverage to untangle when the pain is currently
  being felt (test fragility, repeat oncall). Disposition:
  leverage point, usually `Simplify now` or `with conditions`.
- **Module-level mutable state / global context.** Module
  globals that callers can mutate ("modified on the fly by
  different agents") become race conditions in any concurrent
  execution path — web requests, async handlers, threadpools.
  Apply Chesterton's Fence: sometimes the state is intentional
  (process-wide cache, connection pool). When it is not,
  refactor to explicit parameter passing or stateless
  functions. Disposition: leverage point on concurrent paths;
  `Defer` for single-process scripts.
- **`from modu import *`.** Namespace pollution, makes call
  sites unreadable ("Is `sqrt` part of `modu`? A builtin?
  Defined above?"), and obscures dependency boundaries. Almost
  always worth fixing. Disposition: usually
  `Encode as standard or lint rule` — one rule (e.g. `flake8`
  `F403/F405`, `ruff` `F403`) fixes the whole codebase rather
  than touching files one by one.
- **Stateful objects on request paths.** In web applications
  with concurrent requests, holding state on long-lived objects
  produces race conditions and stale-data bugs. The python-guide
  framing is direct: "stateless functions are a better
  programming paradigm" for these architectures. Apply
  Chesterton's Fence carefully — caching, connection pooling,
  and intentional process-wide state are not bugs. Disposition:
  often `Needs more context` until the concurrency model is
  confirmed; otherwise leverage point.
- **Variable rebinding across types.** Reusing one name for a
  string, then a list, then a set (`items = 'a b c d'` →
  `items = items.split(' ')` → `items = set(items)`) forces
  every reader to hold the type history in their head. Worth
  fixing on hot paths and in code that gets edited; leave alone
  in stable internal helpers. Disposition: `Simplify now` for
  hot spots, `Leave it` otherwise.
- **Module and package naming that fights Python's import
  rules.** Filenames with dots, deeply nested submodule names
  (`library.foo_plugin` instead of `library.plugin.foo`), and
  ambiguous wrapper directories (`src/`, `python/`) all create
  small but persistent friction. Almost always
  `Encode as standard` — one project-layout convention beats
  fixing the names case by case.
- **`+=` string concatenation in loops.** Strings are immutable;
  each concatenation copies the whole string. The textbook fix
  is `''.join(list_of_parts)`. This belongs in a *performance*
  review, not a simplification one — flag it only when the loop
  is on a hot path and the perf cost is real. Otherwise
  `Leave it` (or `Defer` to a perf pass).

**Code style** — idiomatic constructs that materially aid review:

- **Manual resource management instead of `with`.** Manual
  `open()`/`close()`, manual lock acquire/release, manual
  cursor lifecycles — every one is a missing-cleanup bug
  waiting for an exception. Context managers ensure cleanup
  "even if an exception is raised inside the block." Always
  worth replacing. Disposition: `Simplify now` per instance;
  `Encode as standard` if the pattern recurs.
- **Manual indexing instead of `enumerate`/`zip`/unpacking.**
  `for i in range(len(xs))` and `tmp = a; a = b; b = tmp` are
  signals the author was reaching for the structural feature
  Python already gives them. Replacement is mechanical and
  reads better. Disposition: `Simplify now` on hot paths;
  often `Leave it` if buried in stable code.
- **`if key in d / d[key] / else default` instead of
  `d.get(key, default)`.** Three lines collapse to one. Always
  worth fixing where the default is a literal; flag the cases
  where the default is itself a function call (use
  `dict.setdefault` carefully — it always evaluates the
  default). Disposition: `Simplify now`.
- **List comprehensions used for side effects; explicit loops
  used for transforms.** Roles are reversed. `[print(x) for x
  in xs]` produces a throwaway list and obscures intent;
  `result = []; for x in xs: result.append(f(x))` is a
  comprehension begging to escape. Always worth fixing.
  Disposition: `Simplify now`.
- **List used as a lookup container.** Repeated `x in big_list`
  is O(n) per check. If the collection is large *and*
  repeatedly searched, a `set` or `dict` flips it to O(1) and
  the code reads better as well. Apply Chesterton's Fence —
  sometimes ordering matters and the list is intentional.
  Disposition: `Simplify now` on hot paths, `Defer` otherwise.

**Documentation** — names, docstrings, and comments:

- **The three-way split.** Names explain *what* the code is.
  Docstrings explain *how to use* the symbol from outside.
  Comments explain *why* — non-obvious constraints, workarounds,
  hidden invariants. A simplification review should remove
  redundancy across these layers, not collapse them into each
  other. Disposition: per-instance `Simplify now`.
- **"What" comments are noise.** A comment that paraphrases the
  next line of code (`# increment the counter` above
  `count += 1`) competes with the name and rots the moment the
  line changes. Delete as part of the simplification. The
  signal that a comment is noise: removing it loses no
  information. Disposition: `Simplify now`.
- **Code commented out with triple-quoted strings.** `"""old
  code"""` is not a comment — it is a string literal that
  `grep` cannot find when searching for "removed code." Use
  `#` at proper indentation, or (better) delete the dead code
  outright and recover from version control if needed.
  Disposition: `Simplify now`; flag as `Encode as standard` if
  the pattern recurs.

**Tests** — what test shape implies for refactor safety:

- **Tests with hidden ordering dependencies.** A test that
  passes only when run after another test (shared module
  state, unreset singletons, leaked DB rows) cannot be trusted
  to pin behavior during a refactor. python-guide is explicit:
  "Each test must be able to run alone, and also within the
  test suite, regardless of the order that they are called."
  Worth fixing before any non-trivial simplification of code
  under test. Disposition: blocker — `Simplify with conditions`
  (the conditions being: tests must isolate first).
- **Implementation-coupled tests.** Tests that assert on
  private attributes, internal helper calls, or exact
  mock-call shapes break the moment you simplify the
  implementation, even when behavior is unchanged. They
  convert refactor-safety into refactor-tax. Worth flagging as
  `Encode as standard` (test behavior, not internals) and as
  a candidate for rewriting before the simplification, not
  after.
- **Slow tests in the inner loop.** "If one single test needs
  more than a few milliseconds to run, development will be
  slowed down or the tests will not be run as often as is
  desirable." If the test loop discourages running tests, the
  review's recommendations will not get validated, which is
  itself a leverage problem. Disposition: `Defer` to a
  separate effort, but surface it as a quality recommendation
  in its own right.

**Common gotchas** — language semantics that produce subtle bugs:

- **Mutable default arguments (`def f(to=[])`).** Default
  arguments are evaluated *once* at function-definition time,
  not on each call, so the default object is shared across all
  invocations. Classic source of "why is this list growing
  between calls" bugs. Replace with
  `def f(to=None): ... if to is None: to = []`. Always worth
  fixing. Disposition: `Encode as standard or lint rule` if no
  linter is configured (`flake8-bugbear` `B006`, `ruff` `B006`
  catch this); per-file fix only when a single instance is
  found and no broader pattern exists.
- **Late-binding closures in loops.** `[lambda x: i*x for i in
  range(5)]` does not capture `i` per-iteration; every closure
  reads `i` at call time, so all five return the same value.
  Fix by binding via a default argument
  (`lambda x, i=i: i*x`) or via `functools.partial`. Subtle
  bug, ships to production often, hard to find after the fact.
  Disposition: `Simplify now` per instance; the pattern is too
  rare and context-bound to encode as a lint rule reliably.

What this list does not include: repository layout
(`tests/` vs inline tests, `setup.py` vs `pyproject.toml`,
package naming), CHANGELOG/README content, or Sphinx setup.
Those are project-structure or release-process work, not
code-simplification work — note the gap if it exists, but do
not try to do all those jobs in one review.

### LLM agent & prompt systems

Agent orchestrators, prompt assembly, model routing, and the
conversation transcript have their own recurring design smells.
Each below is a *trigger signal* — a concrete code shape that
should fire one of the design-smell lenses, so the finding
surfaces on commit one instead of in the iteration round.

- **Synthetic / injected messages that are persisted.** A
  reminder, nudge, or system note written into the transcript as
  a stored row (especially `role=user` with a `synthetic` meta
  flag). Persisting it drags exactly the machinery lens 1
  predicts: a client-visibility filter to hide it, and a
  *provenance* bug — any code that scans history for "the last
  user turn" (triggering-turn selection, sequence stamping) will
  mistake the synthetic row for a real one. Trigger lens 1 +
  lens 5; the fix is **derive-at-render-time** — recompute the
  injection when the transcript is assembled and delete the
  stored row.
- **`role` chosen for provider constraints.** Reminders forced
  to `role=user` because a mid-conversation `role=system` message
  is rejected by the current model. Legitimate, but note it is a
  *contingent property* (lens 4): it holds for this model
  generation and the caveat belongs next to the code. The same
  choice is what creates the provenance hazard above.
- **A constraint conveyed by attachment/instruction, not
  toolset.** "Read-only", "frozen", or "planning-only" mode
  implemented by injecting a reminder that *asks* the model not
  to mutate, while the mutating tools stay in the schema. This is
  soft enforcement (lens 2): looks locked, only asked-nicely
  locked. A mutating tool still runs if the model ignores the
  instruction. Surface it as an explicit choice; if it must be a
  guarantee, the gate is a per-mode toolset, not prose.
- **"Keeps the prompt cache warm" defending a design
  constraint.** When byte-identical prompts/tools across modes
  are justified by cache stability, check what *else* invalidates
  the cache on the same transition (lens 7). Anthropic prompt
  caching is keyed per model: if the two modes route to different
  models, the toggle turn is already a cache miss, so a per-mode
  prompt or toolset difference on that transition costs nothing
  extra. The constraint may still help *within* a mode (no swap),
  but the cross-mode argument is often illusory — and it is
  usually what foreclosed the hard tool gate above. Quantify
  before accepting it.
- **Config flag flipped by a mid-turn event, read from a cached
  context value.** A mode/flag set via a `config_change` (or
  equivalent) pending event, while a typed context field holding
  the same value was resolved at job-start. Anything stamped from
  the cached field before it is re-resolved records the *previous*
  value on the turn the flag flips (lens 4). Re-resolve at the
  read point, or stamp after the rebuild.
- **Prompt distillation / replacement that drops dynamic
  injections.** Replacing or shrinking a prompt (e.g. retiring a
  specialized agent's prompt into a smaller instruction block).
  Enumerate the *dynamic* values the old prompt injected — current
  date, locale, user/connector context, tool inventory — and
  confirm the new path still injects each. A dropped `current_date`
  silently sends time-sensitive work back to the training cutoff
  (lens 3: a property the old code guaranteed, quietly lost).
- **The same fact in the agent_settings bag and a column.** Mode,
  role, or feature flags stored in a JSONB/dict settings bag.
  Trigger lens 6, and recommend the **untyped bag → typed column**
  move: a real column with a documented legacy-fallback read
  during migration. Indexable, typed, single-sourced.

## Rationalizations

- "It works, leave it alone."
  - Rebuttal: working code that nobody can read is debt
    accruing interest. Fix hot spots; leave stable code alone.
    The default is contextual, not universal.

- "Fewer lines is simpler."
  - Rebuttal: comprehension is the metric, not line count.
    A one-line nested ternary is not simpler than a five-line
    if/else.

- "I'll clean up this unrelated code while I'm here."
  - Rebuttal: drive-by simplifications create review noise
    and regression risk in code the PR was not supposed to
    touch. Stay in scope. Recommend a follow-up if needed.

- "The original author had a reason; better leave it."
  - Rebuttal: sometimes. But "the residue of iteration under
    deadline" is also a real reason. Check `git blame`. If
    the reason is gone, the code can change.

- "We should refactor this into [pattern]."
  - Rebuttal: refactoring toward a pattern the rest of the
    codebase does not use creates inconsistency, not
    simplification. Match the codebase. Propose pattern
    shifts in their own RFC, not inside a simplification PR.

- "The types make it self-documenting."
  - Rebuttal: types document structure. Names document
    intent. They are not substitutes. A well-named function
    explains *why* better than a type signature explains
    *what*.

- "I'll refactor while I add the feature."
  - Rebuttal: two PRs. Mixed PRs are harder to review,
    revert, and read in history. Refactor first, ship; then
    add the feature against the cleaner base.

- "This abstraction might be useful later."
  - Rebuttal: do not preserve speculative abstractions.
    Remove and re-add when the second use case actually
    arrives. YAGNI is cheaper than maintaining unused
    indirection.

- "We should scope-creep this into a quality program."
  - Rebuttal: a single review is not the place to start a
    quality program. Note the gap, recommend the program as
    a separate initiative, and do not block this review on
    organizational change.

## Red Flags

- Recommendations with no specific surface (file, function,
  symbol). Feedback that cannot be acted on is not a review.
- Recommendations that touch more than 500 lines or more than
  five files in one change. At that scale, invest in
  automation — codemods, AST transforms — rather than manual
  edits.
- Recommendations that require modifying tests to pass. The
  change is altering behavior, not just simplifying.
- Recommendations that introduce a new pattern the codebase
  does not already use.
- Recommendations that strip error handling because "it makes
  the code cleaner."
- Reviewer treats simplification as a binary judgment per file
  rather than per surface. The nuance is per-symbol.
- Review produces observations but no dispositions. The
  staff-eng job is to tell the team what to do next.
- Review ignores the hierarchy and leads with cosmetic naming
  fixes when the same code has unhandled error paths or
  tangled state.
- The same recommendation appears in three or more places with
  no proposal that it should be documented as a standard or
  enforced by a lint rule. Repeated manual fixes are a process
  tax the team will pay on every future PR.
- The codebase has no documented conventions and no automated
  checks (no linter, no formatter, no type checker), and the
  review treats this as background rather than as the highest-
  leverage recommendation it can make.
- A finding stated as fact but never verified against the code
  at the revision under review — a pre-rebase line number, a
  stale or renamed path, or a claim that no longer holds at the
  current head.
- A "read-only", "frozen", or "admin-only" constraint enforced
  only by instruction or convention, presented as if it were a
  hard guarantee.
- State persisted when it is derivable from other state,
  dragging visibility-filtering, throttle, or cleanup machinery
  that would vanish if it were recomputed at use time.
- The same fact stored in two places that can drift (a column
  and a JSONB key, a cache and its origin, a frontend constant
  and a backend enum) with no defined winner.
- Design feedback that stops at the surface symptom instead of
  naming the pattern-class and tracing the inverse operation
  (toggle-back, delete, exit).
- Findings that appear only after reading the iteration history,
  bot comments, or later commits — reverse-derived from the
  fixes and presented as if predicted. A review run with the
  answer key is a changelog, not a review.
- A new mode / flag / stored field reviewed without enumerating
  its representations, its inverse, its legacy/rename path, and
  its constraint type. The forcing enumeration was skipped.
- A design-smell flagged ("this is persisted but derivable",
  "this lives in the JSONB bag") with no named architectural
  move (derive-at-render-time, untyped-bag → typed-column) to
  resolve it. Naming the smell without naming the refactor is
  half a review.
- A test or guard trusted by its name/docstring rather than its
  assertion — an open-set check (`issubset`, "x in result")
  behind a "locks the surface" claim, or a new CI workflow that
  drops the caching / version-pinning its sibling guard has.
- Findings ranked by nominal severity while ignoring failure
  mode — a silent-failure smell (drift with no error, a guard
  that stopped guarding) buried under a loud one (a red check)
  that announces and fixes itself.
- A fix accepted without re-running the lens on it, or that
  changes a shared resolution / contract / dependency without
  enumerating the other consumers — the N+1 site left to drift.

## Verification

Before closing the review, the agent should be able to answer:

- For each candidate, what is the specific surface (file,
  function, symbol), the simplification, the payoff, and the
  cost?
- For each candidate, what is the disposition — simplify now,
  simplify with conditions, leave it, defer, or needs more
  context?
- Are recommendations in scope, or did the review drift into
  drive-by cleanup?
- Do recommendations align with project conventions
  (`CLAUDE.md`, neighboring code), or do they impose external
  preferences?
- Did the review prioritize hot spots and leverage points
  over cosmetic naming and structure?
- Does the review check vector alignment — that recommended
  simplifications pull in the direction the codebase is
  already moving?
- Was Chesterton's Fence applied to every candidate, with
  uncertain candidates downgraded to "needs more context"
  instead of recommended?
- For recurring patterns (three or more places), did the
  review recommend a documented standard or an automated
  check rather than only per-file fixes?
- If the codebase lacks linters, formatters, or documented
  conventions, did the review surface this as a leverage
  recommendation in its own right?
- Does the review output tell the engineer what to do next,
  in priority order? A simplification review that ends in a
  list of observations without dispositions has not completed
  its job.
- For design-smell findings, was each claim verified against
  the source at the revision under review — not a stale path or
  a pre-rebase line number?
- Did design feedback name the pattern-class and trace the
  lifecycle, including the inverse operation, rather than
  stopping at the symptom?
- For any new field, mode, or stored state: is it derived where
  it could be, enforced where it claims to be, single-sourced,
  and complete on the inverse operation?
- Were the design-smell findings produced from the first commit
  *before* reading the iteration history or other reviewers'
  comments — not reverse-derived from the fixes?
- For each new mode / flag / field, was the forcing enumeration
  run (representations, derived?, inverse, legacy/rename path,
  same-turn ordering, constraint type)?
- Where a smell was found, did the review name the architectural
  move that resolves it (derive-at-render-time, untyped-bag →
  typed-column) rather than only describing the smell?
- For each guard, test, or CI job: does its assertion actually
  enforce the property its name/docstring claims (closed-set, not
  open-set), and does a new workflow match its sibling's caching
  and version-pinning?
- For each finding, is its failure mode named (loud vs silent),
  and are silent failures ranked above equally-severe loud ones?
- Were the review's own fixes re-reviewed, with every consumer of
  a changed shared resolution / contract / dependency enumerated?
