---
description: Review code from a staff-level lens with a simplification focus.
---

Invoke the agent-dri-skills:code skill.

Review the provided code surface and produce a staff-level
simplification assessment:

1. Read CLAUDE.md and study neighboring code to understand
   project conventions before recommending any change.
2. Confirm the scope — the specific files, functions, or
   symbols being reviewed. Push back on requests with no
   boundary ("clean up the codebase").
3. Apply the two filters before any pattern matching:
   - Will this code change again? Stable code that nobody
     touches is not worth simplifying.
   - Do you understand why it is written this way? If not,
     read the call sites and `git blame` first.
4. Identify hot spots — code currently causing bugs, slow
   PRs, repeated review questions, or oncall pages. Hot
   spots get the first dispositions.
5. Apply best practices within scope — guard clauses for
   deep nesting, descriptive names, deletion of dead code,
   alignment with the codebase's existing style. Match
   what is already there; do not import external preferences.
6. Address leverage points — interfaces, error paths,
   stateful logic, and control flow at module boundaries.
   Prioritize one of these over five cosmetic cleanups.
7. Check vector alignment — does each recommended
   simplification pull in the direction the codebase is
   already moving? If a deprecation or migration is in
   flight, do not invest in polishing the old surface.
8. Apply Chesterton's Fence to every candidate. Confirm the
   original reason for the code no longer applies before
   recommending a change. Downgrade uncertain candidates to
   "needs more context."
9. Look for repetition. If the same candidate type appears in
   three or more places, recommend encoding the rule as a
   documented standard or an automated check (linter,
   formatter, type rule) rather than fixing each instance by
   hand. If the codebase has no linter, formatter, or
   documented conventions, surface that as a leverage
   recommendation in its own right.
10. Produce a disposition for every candidate — simplify now,
    simplify with conditions, encode as standard or lint rule,
    leave it, defer, or needs more context. Each disposition
    names a specific surface (or, for systemic dispositions,
    the rule and where it should live), the change, the
    payoff, and the cost.

If the request has no scope or no clear reason it is happening
now, flag this before any other feedback. Use the `code` skill
to validate the final assessment, and prioritize hot spots and
leverage points over cosmetic naming and structure. If the
codebase is Python, also check the language-specific patterns
documented in the skill — circular imports, mutable defaults,
late-binding closures, manual resource management, namespace
pollution from `import *`, implementation-coupled tests, and
the structure/style/documentation conventions from the
Hitchhiker's Guide to Python.
