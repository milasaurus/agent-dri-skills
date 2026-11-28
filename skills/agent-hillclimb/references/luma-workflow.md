# Which workflow fits in a Luma checkout?

These commands belong to luma-core. Its project-specific [hill-climb guide](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/agent-hillclimb/SKILL.md) supplies the runner commands and environment setup. In another repository, use the local equivalents.

| Decision | Luma workflow |
| --- | --- |
| Which failures deserve cases? | Use [/convo-analysis](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/convo-analysis/SKILL.md) to find capability gaps and [/session-quality](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/session-quality/SKILL.md) to inspect completion, friction and abandonment. |
| Which inputs can we replay? | [/promptbank](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/promptbank/SKILL.md) prepares a reusable bank from a sampling recipe. Add starting state, expected outcomes and checks for the behavior under test. |
| Did this particular edit take effect? | For a skill-text PR, [/vibe-check](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/vibe-check/SKILL.md) compares the edited skill with staging on a small suite. Use the project hill-climb for a targeted PR plan, verification from an export, or repeated baseline comparisons. |
| What did the recorded runs establish? | [/eval-report](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/eval-report/SKILL.md) produces candidate versus baseline, serving-stack and daily readouts. Match the orchestrator or executor role to the decision. |
| Why did a run fail? | Start with [/what-happened-to-my-eval-run](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/what-happened-to-my-eval-run/SKILL.md). For a Vespa pipeline failure, [/vespa-eval-triage](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/vespa-eval-triage/SKILL.md) traces affected cases to jobs and artifacts. |

For board performance, use [/canvas-benchmark](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/canvas-benchmark/SKILL.md). For app-package evals during promotion, use [/app-ship](https://github.com/lumalabs/luma-core/blob/main/.claude/skills/app-ship/SKILL.md). When the grader itself needs evaluation, Judy has a [judge runner](https://github.com/lumalabs/luma-core/blob/main/tools/judy-run) and a [registration tool](https://github.com/lumalabs/luma-core/blob/main/tools/judy-register-judge).
