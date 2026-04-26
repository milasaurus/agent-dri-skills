# agent-dri-skills

Staff+ engineering skills for AI agents.

## Why

AI agents can follow instructions, but they don't bring judgment. When you ask an agent to review a system design, it produces observations, not the kind of pointed, experience-driven feedback a staff engineer in the real world would give. It won't push back on a missing business case, won't zero in on the data model as the highest-leverage risk, and won't tell you whether the design is actually ready to ship.

This repo encodes that judgment as reusable skills. Each skill captures the mental model, priorities, and failure pattern recognition that experienced engineers develop over years, structured so an agent can apply them consistently. The goal isn't to replace staff eng, but to scale them: every team gets an experienced staff eng that catches the things that are easy to miss and expensive to fix later.

## Skills

Each skill targets a core staff engineer competency, the kind of judgment that's hard to teach and expensive to learn through mistakes. The goal is to eventually cover the full set of technical leadership skills that distinguish top tier staff level work.

### system-design-review

A staff-level architecture review that evaluates system designs against reliability, scalability, operability, and sound decomposition.

- **Gates on business value** — requires a clear business goal and user-facing impact before evaluating anything else
- **Focuses on leverage points** — prioritizes interfaces, stateful systems, and data models, the things most expensive to change after launch
- **Assesses fundamentals concretely** — data model design, failure modes, scalability under real load numbers, rollout strategy, observability with specific SLOs, and migration safety
- **Produces a clear disposition** — approve, approve with conditions, or specific changes required

Includes common rationalizations with rebuttals and red flags that should halt a review until addressed. Invoke with `/design-review`.

### code

A staff-level code review with a simplification lens. Encodes the judgment about when to leave code alone, when to invest in cleanup, and which simplifications actually pay off.

- **Gates first** — two filters apply before any pattern matching: will this code change again, and do you understand why it's written this way?
- **Prioritizes hot spots and leverage points** — interfaces, error paths, stateful logic, and code currently causing oncall pain take precedence over cosmetic cleanup
- **Escalates repetition to standards and automation** — when the same recommendation appears across multiple files, the right answer is a documented standard or a lint rule, not per-file fixes
- **Includes Python-specific patterns** — circular imports, mutable defaults, late-binding closures, manual resource management, namespace pollution from `import *`, implementation-coupled tests, and the structure/style/documentation conventions from the [Hitchhiker's Guide to Python](https://docs.python-guide.org/)
- **Produces explicit dispositions** — `simplify now`, `simplify with conditions`, `encode as standard or lint rule`, `leave it`, `defer`, or `needs more context`

A code review that ends in observations without dispositions has not completed its job. Invoke with `/code-review`.

## Secondary skills

Curated external skills bundled in this marketplace.

| Skill | Source | Use |
|---|---|---|
| langfuse | [langfuse/skills](https://github.com/langfuse/skills) | LLM observability — tracing, prompt management, evaluation |

## Installation

### From the plugin marketplace (recommended)

Add this repo as a marketplace, then install whichever plugins you want:

```bash
/plugin marketplace add github:milasaurus/agent-dri-skills

# Mila's staff-engineering skills (system-design-review, code-review)
/plugin install agent-dri-skills

# Curated external skill — Langfuse for LLM observability
/plugin install langfuse
```

Once installed, the slash commands (`/design-review`, `/code-review`, etc.) are available in any project. Run `/help` to confirm they appear.

### Local development

To test the skills against a working project without pushing changes upstream, point Claude Code at this repo as a local plugin directory:

```bash
claude --plugin-dir /path/to/agent-dri-skills
```

Edit the SKILL.md files and run `/reload-plugins` to pick up changes without restarting.

## License

MIT
