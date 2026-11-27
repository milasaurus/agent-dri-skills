# agent-dri-skills

Staff+ engineering skills for AI agents.

## Why

AI agents can follow instructions, but they don't bring judgment. When you ask an agent to review a system design, it produces observations, not the kind of pointed, experience-driven feedback a staff engineer in the real world would give. It won't push back on a missing business case, won't zero in on the data model as the highest-leverage risk, and won't tell you whether the design is actually ready to ship.

This repo encodes that judgment as reusable skills. Each skill captures the mental model, priorities, and failure pattern recognition that experienced engineers develop over years, structured so an agent can apply them consistently. The goal isn't to replace staff eng, but to scale them: every team gets an experienced staff eng that catches the things that are easy to miss and expensive to fix later.

## Skills

| Skill | What it does | Invoke |
|---|---|---|
| `system-design-review` | Staff-level architecture review — gates on business value, checks reliability, scalability, operability, and decomposition | `/system-design-review` |
| `code` | Staff-level code review with a simplification lens — hot spots and leverage points first, explicit dispositions per candidate | `/code-review` |
| `eng-feasibility` | Validates load-bearing assumptions before production code — single-file spike, falsifiable gates, build/pivot/stop decision | `/eng-feasibility` |
| `multi-agent-design` | Gates and designs multi-agent systems — forces a documented single-agent justification before any topology is selected | `/multi-agent-design` |
| [`technical-architecture-study-guide`](skills/technical-architecture-study-guide/SKILL.md) | Draft or audit a guide that teaches a technical lead to trace one operation, diagnose a failure, and explain why the system works this way. | `/technical-architecture-study-guide` |
| [`coding-agent-goal`](.agents/skills/coding-agent-goal/SKILL.md) | Write a coding-agent handoff, or refresh a stale task goal during a running PR loop. | `/coding-agent-goal` |

Use `contract-only` for the reusable rules or `task-only` for a fresh goal. When installed as a Claude Code plugin, use `/agent-dri-skills:coding-agent-goal`.

## Agent architecture

| Skill | Decision it supports |
| --- | --- |
| [`/model-api-conformance`](skills/model-api-conformance/SKILL.md) | Does this model route satisfy the calling application's API contract? Build and run adapter-level tests for the primitives it uses. |
| [`/agent-change-eval`](skills/agent-change-eval/SKILL.md) | Does the candidate improve the outcome of an assigned task? Compare it with the baseline on matched cases and identify the evidence needed for release. |
| [`/agent-loop-governance`](skills/agent-loop-governance/SKILL.md) | Use when designing or debugging an agent that can retry, revise, or delegate on its own. Decide what authorizes the next action and when a person or runtime must stop it. |

## Judge development

| Skill | Reach for it when |
| --- | --- |
| [`/judge-create`](skills/judge-create/SKILL.md) | Describe what success means. The agent chooses and runs the relevant specialists and combines their results when a task has several requirements. |
| [`/deterministic-judge-create`](skills/deterministic-judge-create/SKILL.md) | Records, file properties or events let you verify the requirement with code. |
| [`/text-judge-create`](skills/text-judge-create/SKILL.md) | You need to check meaning, such as whether a reply honored a policy exception. |
| [`/vlm-judge-create`](skills/vlm-judge-create/SKILL.md) | You need a vision-language model to grade images or video. Define the visual evidence and output contract, build a candidate, and measure how it agrees with human reviewers. |
| [`/judge-tune`](skills/judge-tune/SKILL.md) | You have a judge and labeled examples. Compare one revision at a time, inspect which decisions changed, and validate the selected version before promotion. |

## Launch measurement

Start with [`/launch-measurement-run`](skills/launch-measurement-run/SKILL.md) to run the chain or resume from existing artifacts. Each stage also works as a standalone command.

| Stage | Deliverable |
| --- | --- |
| [`/launch-measurement-plan`](skills/launch-measurement-plan/SKILL.md) | Decision, metric definitions, denominators and guardrails |
| [`/launch-instrumentation-spec`](skills/launch-instrumentation-spec/SKILL.md) | Verified signal map and gaps by metric |
| [`/launch-eng-handoff`](skills/launch-eng-handoff/SKILL.md) | Implementation asks with owners and acceptance checks |
| [`/launch-logging-audit`](skills/launch-logging-audit/SKILL.md) | Post-deployment evidence and coverage limits |
| [`/launch-dashboard-metrics`](skills/launch-dashboard-metrics/SKILL.md) | Dashboard or build specification with validation status |

## Experimentation

| Skill | What it does | Reach for it when |
| --- | --- | --- |
| [`/experiment-design`](skills/experiment-design/SKILL.md) | Trace the product flow, choose an A/B test or rollout, check overlap with live tests, size it, and fill the tracker and pre-launch gate. | Before building an experiment. |
| [`/experiment-pr-check`](skills/experiment-pr-check/SKILL.md) | Check the primary metric, treatment delivery and identity mapping first. Then compare the full setup PR with its tracker row and give separate merge and exposure decisions. | When a PR wires up an experiment, before merge or exposure. |
| [`/experiment-readout`](skills/experiment-readout/SKILL.md) | Check whether the results are interpretable and publish one action with the evidence, owner and timing. | At a planned decision point or when a stop condition is met. |

## Secondary skills

| Skill | Source | What it does |
|---|---|---|
| `langfuse` | [langfuse/skills](https://github.com/langfuse/skills) | LLM observability — tracing, prompt management, evaluation |

## Installation

```bash
/plugin marketplace add github:milasaurus/agent-dri-skills
/plugin install agent-dri-skills
/plugin install langfuse
```

Run `/help` to confirm the slash commands appear.

## Local development

```bash
claude --plugin-dir /path/to/agent-dri-skills
```

Edit any `SKILL.md` and run `/reload-plugins` to pick up changes without restarting.

## License

MIT
