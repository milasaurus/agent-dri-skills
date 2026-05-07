---
description: Validate a project's load-bearing assumptions with a focused single-file spike before committing to a build.
---

Invoke the agent-dri-skills:eng-feasibility skill.

Build a feasibility spike for the project described and
produce a build / pivot / stop decision:

1. Read CLAUDE.md and any project brief or plan to frame
   what the project is, who it serves, and what ships.

2. **Always produce the assumptions list before any code.**
   It is what makes "is this project worth the time?"
   decidable. Categorize each as **must hold** (project
   dies if false), **should hold** (architecture changes if
   false), or **nice if it holds** (optimization). Cover
   API capability, model behavior, latency/cost, data
   shape, and integration assumptions. Two-to-four
   must-hold items.

3. Define a go/no-go gate per must-hold assumption.
   Measurable and falsifiable ("≥3/5 cases pass", "HTTP
   200", "p50 under N seconds") — never "it works."

4. Time-box the spike to hours-to-a-day. If the box blows,
   reset based on what you've learned — don't extend
   silently.

5. Write the spike as a single file. Hardcoded inputs,
   prints everything, real services (no mocks), no Pydantic
   / FastAPI / config files. Run across 5+ hand-picked
   inputs. Reference: image-morpher `spike/spike.py` (~270
   lines, no production scaffolding).

6. Write `tradeoffs.md` next to the spike as you go. For
   each must-hold assumption record: **assumption / gate /
   result / learning / pivot**. Side findings (URL TTLs,
   undocumented fields, silent no-ops, SDK migrations) go
   here too. Strongest finding leads. A `tradeoffs.md` with
   no pivots anywhere is suspicious.

7. Produce a decision: **build**, **pivot architecture**,
   **pivot narrative**, or **stop**. State which.

If no assumptions list exists, do not start writing code.
The list is a precondition. Use the `eng-feasibility` skill
to validate the spike, gates, and decision; refer to
image-morpher (`docs/plan.md` Unit 1, `spike/spike.py`) as
the canonical example.
