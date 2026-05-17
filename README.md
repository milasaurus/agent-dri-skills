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
