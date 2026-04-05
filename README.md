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

Includes common rationalizations with rebuttals and red flags that should halt a review until addressed.

### Usage

Add this repo as a skill source in your Claude Code project, then invoke a review with `/design-review`.

## License

MIT
