---
name: coding-agent-goal
description: Write or revise a coding-agent goal for implementation, CI, and PR review. Use when asked for a handoff or when an active coding loop lacks a usable goal, needs a clarified acceptance check, or must hand unfinished work to another agent. Routine CI and review iterations follow the current goal.
---

# Coding agent goal

## Why this skill

“Implement the plan and get the PR green” leaves the implementer to guess whether a pending check counts, who owns an ambiguous compatibility decision, and whether pushing a fix closes a review thread. Write a goal the implementer and a reviewer can independently check.

## When to use

Invoke directly with a plan, PR, ticket, or description. An agent may also select this skill during an authorized coding loop when the next worker cannot tell what remains or how to prove completion. Typical triggers are a missing goal, a new in-scope requirement from the requester, or a handoff where the current goal is stale. Team and quarterly goals belong in the planning workflow.

**Inside a loop, use task-only by default.** Read the current goal and the evidence that made it inadequate. Update the existing task document in place when available. Carry forward the branch, PR, completed units, decisions, constraints, and outstanding checks. Return control to the running loop at the next unfinished unit. A failing test with a known expected result calls for a fix; a pending check calls for a wait. Neither warrants rewriting the goal.

A goal revision inherits the user's scope and authority. Preserve acceptance criteria unless the requester changes them or a grounded clarification preserves their intent. A red check is never grounds for weakening the definition of done. An explicit authoring request ends with the document; it does not start a new implementation run.

## Process

1. Select the mode from the arguments:
   - **Default:** deliver two parts: the reusable [operating contract](references/operating-contract.md) and a newly authored task goal. If the recipient already has the contract, link to that copy and supply the task document to append under its task heading. For a handoff in chat where the recipient cannot read linked files, include both parts in full.
   - **contract-only:** return the complete reusable contract immediately. No plan or repo is needed.
   - **task-only:** return only the task goal. Make the acceptance gates checkable even if the recipient reads it separately.
2. For modes that need a task, read the supplied plan, PR or ticket, applicable repo instructions, and relevant code, tests and CI configuration. Preserve the source's requirement IDs and confirmed paths. For a plain description, build the smallest grounded scope from the repo. If the source is inaccessible, mark the missing fact and its impact. Ask only if it prevents a usable handoff.
3. Use [the task authoring guide](references/goal-authoring.md) to write the mission, stop condition, decisions made in advance, dependency-ordered work units, and hard constraints. For GitHub PR tasks, carry the contract's check and review commands into the task or cite the attached contract and supply the task-specific parameters. In task-only mode include the commands themselves.
4. Deliver in the requested destination. Otherwise write the task goal as `codex-<topic>-goal.md` in the agreed workspace when writing a file is appropriate. For a chat draft, provide copy-ready Markdown. Identify both parts and where they fit together. Do not assume another engineer can read the author's home directory.

## Common rationalizations

- “The CI workflow covers it.” Name the actual check and the exact task behavior it covers. Include a local verification command for requirements CI misses.
- “The implementer can pick either behavior.” Resolve reversible choices against the source. If a decision expands scope or requires authority the implementer lacks, identify its owner and what work can still proceed.

## Red flags

A unit says only “add tests.” A PR check can pass while no checks were reported. The handoff assumes everyone shares one home directory or that an implementation agent can approve its own changes.

## Dispositions

Return **ready to hand off** with the requested artifact, or **blocked on a named input** if the missing information prevents an actionable goal. For contract-only, the contract itself is the complete deliverable.
