# agent-dri-skills

Staff-level engineering judgment encoded as skills for AI agents. See `README.md` for the skill catalog and install instructions.

## Conventions

- Every skill lives in `skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`).
- Description starts with what the skill does, then trigger conditions ("Use when…").
- Every SKILL.md contains: Why this skill / When to use / Process / Common rationalizations / Red flags / **Dispositions**. The disposition framework is non-negotiable — see Boundaries.
- Slash commands live in `.claude/commands/<name>.md` and map 1:1 to skills.
- Evals live in `skills/<name>/evals/evals.json` (skill-creator format). Eval workspaces (`*-workspace/`) are gitignored — they're regeneratable.
- File paths in plans, skills, and command files must be repo-relative.

## Boundaries

- **Always** produce explicit dispositions. A skill that ends in observations without a decision (`approve` / `simplify` / `build` / `pivot` / `stop`) has not completed its job.
- **Always** check for adjacent existing skills before adding a new one. If 70%+ of the work is already done by `compound-engineering:ce-plan`, `compound-engineering:document-review`, or any `agent-skills:*` skill, narrow the scope or skip.
- **Always** anchor skills in observable failure modes. New skills are justified by pain that existing tools miss, not by theoretical gaps.
- **Never** add a skill that's vague advice. Each skill must drive a decision.
- **Never** duplicate content between skills — reference them.
- **Never** loosen the disposition bar to make a skill easier to apply. A skill that softens to "consider X" instead of producing a verdict is broken.
