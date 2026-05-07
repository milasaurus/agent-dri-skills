# agent-dri-skills

This repo encodes staff-level engineering judgment as reusable skills for AI coding agents. Each skill captures the mental model, priorities, and failure-pattern recognition that experienced engineers develop over years, structured so an agent can apply them consistently. The goal is to scale staff engineers, not replace them.

## Skills

Each skill targets a staff-engineer competency — judgment that's hard to teach and expensive to learn through mistakes.

- **system-design-review** — staff-level architecture review. Gates on business value, focuses on leverage points, produces dispositions (approve / approve with conditions / changes required). Invoke with `/design-review`.
- **code** — staff-level code review with a simplification lens. Two filters first: will this code change again, and do you understand why it's the way it is. Produces dispositions (`simplify now`, `with conditions`, `encode as standard`, `leave it`, `defer`, `needs more context`). Invoke with `/code-review`.
- **eng-feasibility** — assumption-first feasibility check before any production code. Lists assumptions, defines falsifiable go/no-go gates, runs a single-file spike against real services, records pivots in `tradeoffs.md`. Invoke with `/eng-feasibility`.

Secondary skills (curated external) are listed in `README.md`.

## Planning

When authoring or maintaining a plan in this repo (or in plans handed to agents working on this repo), follow `PLANS.md`. It defines the bar plans must clear: cold-read self-containment, observable acceptance, decisions resolved in the plan, four living sections kept current during execution, idempotence for risky steps. Plan-authoring tools (`ce-plan`, `planning-and-task-breakdown`) are the *how*; PLANS.md is the *what good looks like*.

## Conventions

- Every skill lives in `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`).
- Description starts with what the skill does, then trigger conditions ("Use when…").
- Every SKILL.md contains: Why this skill / When to use / Process / Common rationalizations / Red flags / **Dispositions**. The disposition framework is non-negotiable — see Boundaries.
- Slash commands live in `.claude/commands/<name>.md` and map 1:1 to skills.
- Evals live in `skills/<name>/evals/evals.json` (skill-creator format). Eval workspaces (`*-workspace/`) are gitignored — they're regeneratable.
- File paths in plans, skills, and command files must be repo-relative.

## Commands

This is a documentation/skills repo with no build step.

- **Validate skills**: every `skills/*/SKILL.md` has YAML frontmatter with `name` and `description`.
- **Install locally**: `claude --plugin-dir /path/to/agent-dri-skills`
- **Install via marketplace**: `/plugin marketplace add github:milasaurus/agent-dri-skills` then `/plugin install agent-dri-skills`.
- **Reload after edits**: `/reload-plugins`.

## Boundaries

- **Always** produce explicit dispositions. A skill that ends in observations without a decision (`approve` / `simplify` / `build` / `pivot` / `stop`) has not completed its job.
- **Always** check for adjacent existing skills before adding a new one. If 70%+ of the work is already done by `compound-engineering:ce-plan`, `compound-engineering:document-review`, or any `agent-skills:*` skill, narrow the scope or skip.
- **Always** anchor skills in observable failure modes. New skills are justified by pain that existing tools miss, not by theoretical gaps.
- **Never** add a skill that's vague advice. Each skill must drive a decision.
- **Never** duplicate content between skills — reference them.
- **Never** loosen the disposition bar to make a skill easier to apply. A skill that softens to "consider X" instead of producing a verdict is broken.
