---
name: technical-architecture-study-guide
description: Draft, audit, or expand a technical architecture study guide from system evidence. Use when a technical lead needs to explain requirements, ownership, an end-to-end flow, failure recovery, and design tradeoffs.
---

# Technical Architecture Study Guide

## Why this skill

Build a document that lets a technical lead explain how a system works, why it has its current shape, where it fails, and what would justify changing it.

## When to use

Choose the mode from the request. If the decision is whether to approve a proposed architecture for implementation, use [system design review](../system-design-review/SKILL.md).

- **Draft:** create a new guide from supplied sources.
- **Audit:** review an existing guide, identify material gaps, and edit it only when the user asks for changes.
- **Focused expansion:** deepen one named section without rewriting unrelated parts.

Read [references/document-contract.md](references/document-contract.md) before drafting or assessing coverage. Treat its sections as architectural questions to answer, not a rigid table of contents. Read [references/review-rubric.md](references/review-rubric.md) before final handoff.

## Process

### Establish the assignment

Identify:

- the system or technical area and its boundary
- the primary reader and what they must be able to explain
- the factual sources
- the destination and whether it is new or existing
- known constraints, decisions, and questions

Make reasonable assumptions when they do not change the system boundary. Ask only when a missing choice would materially change the document.

If the user supplies an example or reference document, borrow its structure and writing standard without carrying its system-specific facts, people, dates, metrics, or decisions into the new guide.

### Build from evidence

Inspect the sources needed to establish actual behavior. Separate every material claim into one of these categories in the prose when ambiguity matters:

- **Observed:** directly supported by a source or current system behavior.
- **Inferred:** the best explanation of the evidence, but not directly confirmed.
- **Recommended:** a proposed design or working default.
- **Open:** a decision that still needs evidence or ownership.

Do not invent implementation details to make a diagram or section feel complete. When sources disagree, surface the disagreement and explain why it matters.

Prefer system concepts over file and code references. Use code references only when they establish a contract, boundary, or current behavior that the prose could otherwise misstate.

### Explain the system at three levels

Every complete guide should make these three views coherent:

1. **Product contract:** requirements, scale, constraints, and user-visible states.
2. **System contract:** components, ownership, data, handoffs, and invariants.
3. **Operating contract:** failure recovery, cost, observability, testing, release, and open decisions.

Use one representative end-to-end request to connect the views. At each important handoff, answer:

- What committed?
- Which component owns the next state?
- What may be delivered or executed more than once?
- How is an ambiguous outcome reconciled?
- What does the user see while the systems disagree?

For each major component, state:

- what it owns
- what it receives
- what it emits
- what it must not decide
- how the system behaves when it is unavailable

For each major tradeoff, state:

- the competing choices
- what the selected or proposed choice buys
- what it makes worse
- the working default, if any
- the evidence that would justify revisiting it

### Write for understanding

- Use question-based headings and plain English.
- Start with the shortest useful mental model, then deepen it.
- Define specialized terms before relying on them.
- Keep diagrams readable at the destination's normal width. Explain the important handoffs below the diagram.
- Use a table only when several items share the same comparison fields.
- Use concrete product examples instead of generic architecture claims.
- Keep confirmed behavior distinct from recommendations.
- Give study questions inline answers. Give open questions an explicit tradeoff and working default.

Do not force agent-specific concepts onto unrelated systems. Adapt boundaries such as model versus code into the relevant equivalent: policy versus mechanism, planner versus executor, control plane versus data plane, or user intent versus authorized operation.

### Work in the requested destination

When the user targets an existing document, read the current version, preserve its hierarchy and edit only the requested surface. Use the destination's available editing tools. For a shared document, guard against concurrent edits and read back the changed section. Keep any local canonical source in sync when one already exists.

Do not silently substitute a local draft for the requested live document.

### Finish with a skeptical review

Use [references/review-rubric.md](references/review-rubric.md). Remove repeated explanation, unsupported certainty, generic tradeoffs, decorative diagrams, and code detail that does not improve understanding.

Check that a technical lead can answer the questions that apply to this system:

- what the product requires
- what owns each important state
- how one request moves end to end
- where work can be duplicated, lost, delayed, or charged incorrectly
- how the system repairs partial failure
- how authority, credentials, cost, and cancellation propagate
- what is tested deterministically, statistically, or by human judgment
- which guarantees must survive a change of implementation or provider

At handoff, link the finished artifact and state any material source, connector, or visual property that could not be verified.

## Common rationalizations

- “The diagram already shows the retry.” Walk the reader through an acknowledgment that goes missing after the write. Name the record they can inspect and what that record proves.
- “The design doc says this is the owner.” Check whether that document describes deployed behavior or a proposal. If the sources disagree, show the disagreement at the point where it changes the explanation.

## Red flags

A walkthrough skips from “accepted” to “done.” A study question has no answer. A scale estimate has no workload assumption. A style example has contributed an architectural claim about a different system.

## Dispositions

Report **ready** when the reader can explain the requested scope from the evidence, **revise** when specific edits can close a material teaching gap, or **needs evidence** when a missing fact blocks the explanation. Name the gap and what would resolve it. For an audit, return the findings. For a focused expansion, apply the verdict to the requested section.
