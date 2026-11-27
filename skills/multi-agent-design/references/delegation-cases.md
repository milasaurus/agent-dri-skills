# Worked delegation cases

These are illustrative designs. Adapt the resource model, policies and completion rules to the caller's system.

## A specialist editing a shared schedule

**Request.** “Group my selected workshop sessions by topic. Keep the keynote in its confirmed room.” The parent has the audience's terminology and the confirmed exception. Choosing topic groups requires interpretation. Applying slot limits, checking room conflicts and committing schedule edits are deterministic operations. If the request is simply “sort this list by start time,” call the sort tool directly.

**Handoff.** The parent supplies the selection, constraints, fixed keynote and desired grouping. The service binds the actor, editable sessions and starting revision. The child can read neighboring slots to understand conflicts. It can edit only the selected records and any explicitly permitted secondary effects. A room outside the grant remains outside the grant even if it would solve a conflict.

**Execution.** The child inspects the selected sessions, proposes groups, and submits a bounded batch. Code computes placements and checks revisions. A scheduler moves one session while the child is working. The old proposal must not overwrite it. The executor returns the conflict so the child can reread, replan within scope, or stop. If a commit acknowledgement is lost, reconcile the operation before issuing further writes. An undo should preserve edits made after the operation.

**What can the parent say?** Suppose six sessions were admitted. Four moves are verified, one session was already correctly placed and verified, and the concurrently edited session was skipped. Report those three counts and identify what remains. If the service acknowledged a write but readback failed, record both facts. A domain reviewer can still reject the topic grouping even if every move was correctly executed.

## Competing candidates and a newer revision

**Request.** A documentation team asks for two candidate summaries and will select one for publication. Each writer can work independently from the same source revision. A single parent owns selection. The publisher checks the chosen artifact and revision. Workers cannot publish directly.

**Timeline.** Worker A returns. The reviewer requests a revision before worker B finishes. The parent opens a new round for the revised brief. A delayed result from B is retained with the old round and cannot replace the new choice. If one acceptable candidate suffices under the agreed policy, a losing worker need not hold the parent open. If the user requested both candidates for comparison, both are required and the parent reports any missing work.

**Late approval.** If the user cancels before publication, a delayed approval for a candidate from that round cannot revive the job. Serialize the publish decision against cancellation and the reviewed revision. If publication already committed, show its receipt and any available recovery action. Cancellation alone cannot establish that publication was undone.

**Crash boundary.** A child finished and stored a result just before its parent restarted. Recovery finds the undelivered result, consumes it idempotently and continues the appropriate round. A transport retry of the launch uses the original child identity. A changed brief receives a new identity. If a paid provider call was already accepted, replaying the delegation alone cannot tell the caller whether it is safe to issue the charge again.

## When one agent is enough

A support team proposes researcher, writer and reviewer agents for one policy lookup. Its approved policy fits in one request, the answer is read-only and it can cite one relevant clause. Begin with retrieval plus one answering agent and a small evaluation suite. If independently checking policy fidelity is valuable, try a read-only grader. Revisit a child session if the work later needs a distinct permission boundary, an independent evidence-gathering loop, or a lifetime the parent cannot support.
