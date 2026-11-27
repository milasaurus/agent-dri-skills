---
name: deterministic-judge-create
description: Build a deterministic grader for an observable rule over records, files, events, or numeric results. Use when code can decide whether a requirement was met.
---

# Create a deterministic judge

## Why this skill

A three-row export can contain a duplicate and omit a requested record. A count check passes it. Comparing ID multiplicities identifies both errors.

## When to use

Use when the criterion can be written as an executable predicate. It can apply to any input type, including image metadata. For judgments about meaning or appearance, let [judge creation](../judge-create/SKILL.md) select the appropriate specialist.

## Process

1. Choose the authoritative observation and when to sample it. A final-state promise requires a read of the resulting state. A requirement about event order needs an ordered trace. A successful tool acknowledgment alone settles neither.
2. Write the matching rule in the caller's terms. Specify which differences matter, such as order, duplicate occurrences, units, tolerances or allowable completion delay. Distinguish observed absence in a complete snapshot from an unavailable snapshot.
3. Implement the predicate using the caller's harness. Return a verdict and the smallest useful witness, such as missing and duplicate IDs. Mark insufficient evidence as an abstention and read or parsing failures as runner errors. For a starting adapter, see the [export example](../judge-create/examples/export_judge.py).
4. Run a known pass, a near miss that a weaker check would accept, and a missing-evidence case. Include boundary values where relevant. Test whether two equally valid orderings or representations produce the intended verdict. For the bundled example, from this skill's directory run:

   ```sh
   python3 ../judge-create/scripts/run.py ../judge-create/examples/cases.jsonl --judge python3 ../judge-create/examples/export_judge.py
   ```

## Common rationalizations

- “The counts match.” Check identity and multiplicity when the contract names specific items.
- “Nothing appeared in the log.” Establish whether the log covers the relevant interval.

## Red flags

The check rewards the agent's own success message. A failed read is treated as an empty result. The verifier requires arbitrary ordering the user never requested.

## Dispositions

Return **verified for the tested rule**, **revise the matcher**, or **hold for missing evidence**. Supply the runnable check, the witness from a failing case and the scope of verification.
