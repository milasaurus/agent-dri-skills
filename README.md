# agent-dri-skills

Staff+ engineering skills for AI agents.

## Skills

| Skill | What it does | Invoke |
|---|---|---|
| `system-design-review` | Staff-level architecture review — gates on business value, evaluates reliability, scalability, and operability | `/design-review` |
| `code` | Staff-level code review with a simplification lens — prioritizes hot spots and leverage points over cosmetic cleanup | `/code-review` |
| `eng-feasibility` | Validates load-bearing assumptions before any production code — spike against real services, falsifiable gates, build/pivot/stop decision | `/eng-feasibility` |
| `multi-agent-design` | Gates and designs multi-agent systems — forces a documented single-agent justification before any topology is selected | `/multi-agent-design` |

---

### system-design-review `/design-review`

A staff-level architecture review that evaluates system designs against reliability, scalability, operability, and sound decomposition.

- **Gates on business value** — requires a clear business goal and user-facing impact before evaluating anything else
- **Focuses on leverage points** — prioritizes interfaces, stateful systems, and data models — the things most expensive to change after launch
- **Assesses fundamentals concretely** — data model design, failure modes, scalability under real load numbers, rollout strategy, observability with specific SLOs, and migration safety
- **Produces a clear disposition** — approve, approve with conditions, or specific changes required

---

### code `/code-review`

A staff-level code review with a simplification lens. Encodes the judgment about when to leave code alone, when to invest in cleanup, and which simplifications actually pay off.

- **Gates first** — two filters apply before any pattern matching: will this code change again, and do you understand why it's written this way?
- **Prioritizes hot spots and leverage points** — interfaces, error paths, stateful logic, and code currently causing oncall pain take precedence over cosmetic cleanup
- **Escalates repetition to standards and automation** — when the same recommendation appears across multiple files, the right answer is a documented standard or a lint rule, not per-file fixes
- **Includes Python-specific patterns** — circular imports, mutable defaults, late-binding closures, manual resource management, namespace pollution from `import *`, implementation-coupled tests, and the structure/style/documentation conventions from the [Hitchhiker's Guide to Python](https://docs.python-guide.org/)
- **Produces explicit dispositions** — `simplify now`, `simplify with conditions`, `encode as standard or lint rule`, `leave it`, `defer`, or `needs more context`

---

### eng-feasibility `/eng-feasibility`

A staff-level feasibility check that validates a project's load-bearing assumptions before any production code is written. Produces a single-file spike run against real services and a `tradeoffs.md` that turns "should we build this?" into a decidable question.

- **Lists assumptions before code** — explicit, categorized list (must hold / should hold / nice if it holds); the list is what makes "is this project worth the time?" answerable
- **Defines falsifiable go/no-go gates** — each must-hold assumption gets a measurable pass condition (e.g. "≥3/5 cases produce the expected output"); "it works" is not a gate
- **One file, no abstractions** — the spike is disposable, hardcoded, and prints everything; production scaffolding is forbidden
- **Records learnings and pivots in `tradeoffs.md`** — assumption / gate / result / learning / pivot per must-hold item, written as the spike runs
- **Produces a clear decision** — build, pivot architecture, pivot narrative, or stop

---

### multi-agent-design `/multi-agent-design`

Gates and designs multi-agent systems. The primary value is step 2: defaulting to single agent and requiring a written justification before any topology is chosen. Invoke early — before the decision is made, not after.

- **Defaults to single agent** — evaluates single-threaded linear agent and compressor model alternatives before reaching for multi-agent
- **Two load-bearing context engineering principles** — full trace sharing (subagents need the orchestrator's decisions, not just the task) and conflicting implicit decisions (parallel agents making independent choices produce inconsistent outputs)
- **Topology selection with compound reliability math** — `p^N` for sequential pipelines, with retry adjustment formula; if the result falls below the reliability requirement, the topology must change
- **Model tier framework** — Opus for planning/judgment, Sonnet for reasoning over defined inputs, Haiku for structured translation (with a judgment test to prevent asserting Haiku on tasks that require situational reasoning)
- **Context contracts with validation failure behavior** — format, handoff type, validation strategy, and what happens when validation fails at runtime, per contract
- **Produces a clear disposition** — proceed, simplify first, resolve open questions first, or redesign

Invoke on any architecture decision where multi-agent might be the answer — including "I want a researcher agent, a writer agent, and a fact-checker," anything mentioning orchestrator/workers/subagents, or ADR creation for any agentic workflow.

---

## Secondary skills

Curated external skills bundled in this marketplace.

| Skill | Source | Use |
|---|---|---|
| langfuse | [langfuse/skills](https://github.com/langfuse/skills) | LLM observability — tracing, prompt management, evaluation |

## Installation

### From the plugin marketplace (recommended)

```bash
/plugin marketplace add github:milasaurus/agent-dri-skills

# Mila's staff-engineering skills
/plugin install agent-dri-skills

# Curated external skill — Langfuse for LLM observability
/plugin install langfuse
```

Once installed, slash commands (`/design-review`, `/code-review`, `/eng-feasibility`, `/multi-agent-design`) are available in any project. Run `/help` to confirm they appear.

### Local development

```bash
claude --plugin-dir /path/to/agent-dri-skills
```

Edit the SKILL.md files and run `/reload-plugins` to pick up changes without restarting.

## Why

AI agents can follow instructions, but they don't bring judgment. When you ask an agent to review a system design, it produces observations, not the kind of pointed, experience-driven feedback a staff engineer gives. It won't push back on a missing business case, won't zero in on the data model as the highest-leverage risk, and won't tell you whether the design is actually ready to ship.

This repo encodes that judgment as reusable skills. Each skill captures the mental model, priorities, and failure pattern recognition that experienced engineers develop over years, structured so an agent can apply them consistently.

## License

MIT
