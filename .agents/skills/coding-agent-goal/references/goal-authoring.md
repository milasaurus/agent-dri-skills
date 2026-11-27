# Write the task goal

Use this structure for the document the coding agent receives. Ground the decisions in the supplied source, target repository and CI configuration. Prefer a short handoff with a decisive test for each unit.

## Mission

State the outcome, source of truth, scope boundary, and the contract existing callers rely on. Name the target repo, base branch and PR if known. Use repo-relative paths for implementation files.

## Verifiable stop condition

Map requirements to commands, expected results and the revision under test. Include the repository's actual task checks and the final CI and review sweep from the [operating contract](operating-contract.md). Specify how to resolve runtime parameters such as the PR number when the PR will only exist later. Distinguish permission to open and maintain a PR from permission to merge.

## Decisions made in advance

Write each important fork as a decision with a reason or a source. Examples include precedence when inputs disagree, compatibility with older records, which component owns a write, what should happen if a dependency is unavailable, and a nearby refactor that is outside scope. Include only forks the change creates. A reversible implementation detail can be left to the agent with a rule for choosing and recording it.

## Work units

Carry forward existing U-IDs and requirement IDs. Otherwise assign U1, U2 and so on in dependency order. For each unit, name the touched path or symbol, intended behavior, relevant prior decision, test cases and verification command. A useful acceptance case distinguishes the new behavior from a regression.

For example, if a plan says a new timeout option overrides the legacy setting, make that a pre-made call. Have one unit verify both supplied, legacy alone and neither supplied at the normal config-loading entry point. Use the test command actually declared by that repo.

## Hard constraints and handoff

Read the repo and directory instructions. Pull in the constraints that affect this work, such as compatibility, generated sources, flags or branch ownership. Identify which review or CI actions the requester authorized. Preserve the final boundary of a review-ready PR unless instructed otherwise. If the user supplies a past goal as a writing example, borrow its structure and verify every project-specific rule against the current repo.
