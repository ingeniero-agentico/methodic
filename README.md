# ingeniero-agentico

[Leer en español → README.es.md](README.es.md)

Industrial engineering methods turned into **skills for AI agents**: each method brings the skill
the agent runs, a guide for a person (English `GUIDE.md`, Spanish `GUIA.md`), templates, the
calculation in a script and a test that has to match.

It works for any company. Each company's data lives **outside this repo**, in its own profile (see
«Private data»).

## Methods

| Method | What it solves | Status |
|---|---|---|
| [procurement](skills/procurement/) | Whom to buy what from, when each supplier covers only part of the list | v1 |
| [cost-and-pricing](skills/cost-and-pricing/) | What a job really costs and what to sell it for (markup on cost) | v1 |
| [economic-evaluation](skills/economic-evaluation/) | Whether a project or investment pays off: cash flow, NPV, IRR, sensitivity | v1 |
| [financial-evaluation](skills/financial-evaluation/) | How to finance it: loan, leasing, rental or paying cash | v1 |

Each method is tested with `python skills/<method>/scripts/<script>.py --test`: it runs a
fictitious case whose result was computed by a second route, and ends in `OK` or fails.

## How a task is orchestrated

```
/new-task should I buy another van to rent it out?
```

The `orchestrate` skill takes it through six stages (details in [ARCHITECTURE.md](ARCHITECTURE.md)):

1. **Map context:** a cheap agent maps the folders the task touches.
2. **Research:** only if data is missing; every figure with source, date and reliability (A–D).
3. **Plan and ask:** it shows you which agents it will launch, with which skill and model. It waits for your yes.
4. **Execute:** one agent per method, in parallel when they do not depend on each other.
5. **Audit:** an independent agent reruns every calculation and compares.
6. **Consolidate:** one answer with the decision, the assumptions that decide it and what is missing.

**Two modes.** The *first run* on a topic researches and maps everything. The following ones are a
*reread*: the map is read instead of the folders, with cheaper models. The mode is decided by
comparing the files' fingerprints, not by the model.

## How it is organized

```
ingeniero-agentico/
├── skills/        the methods + orchestrate · map-context · research · audit
├── agents/        workers for one stage: cartographer · researcher · executor · auditor
├── commands/      /new-task
├── mcp/           MCP server: the methods as tools for any MCP client
├── install/       installer for Codex, Cursor, Gemini CLI, Hermes and others
├── graph/         linked notes method ↔ course ↔ pattern, for Obsidian and graphify
└── profiles/      the company profile template (empty)
```

## Install

| Where | How | Notes |
|---|---|---|
| Claude Code | `/plugin marketplace add ingeniero-agentico/ingeniero-agentico` and `/plugin install ingeniero-agentico@ingeniero-agentico` | Brings skills, agents, `/new-task` and the MCP server |
| Claude Code without the plugin | `python install/install.py --platform claude-code` | Skills, agents and commands in `~/.claude/` |
| Claude Desktop / claude.ai | `python install/install.py --platform claude-desktop` and upload the ZIPs in Customize | No agents in chat: `orchestrate` runs the stages in sequence |
| Codex | `python install/install.py --platform codex` | Skills in `~/.agents/skills/`, agents as TOML; reads `AGENTS.md` |
| Cursor | `python install/install.py --platform cursor` | Skills and subagents in `~/.cursor/`; reads `AGENTS.md` |
| Gemini CLI | `python install/install.py --platform gemini` | Skills and subagents in `~/.gemini/`; reads `GEMINI.md` → `AGENTS.md` |
| Hermes Agent | `python install/install.py --platform hermes` | Skills in `HERMES_HOME/skills/`; delegates with `delegate_task` |
| Other Agent Skills agents | `python install/install.py --platform agents` | Skills in `~/.agents/skills/`, in sequence |
| Any MCP client | `python mcp/server.py` in its configuration | The methods as tools |

Step by step per platform in [docs/INSTALL.md](docs/INSTALL.md); the MCP server in
[docs/MCP.md](docs/MCP.md). `python install/install.py --test` installs into a temporary HOME for
every platform and checks it without touching your configuration.

## Private data

Each skill looks for the company profile in this order:

1. The path given with `--profile`.
2. The path in the `INGENIERO_DATOS` environment variable.
3. The sibling folder `../ingeniero-agentico-datos/`.
4. If it finds none, it works with `profiles/_template.yaml` and asks you for the missing data
   (everything it fills in comes out marked as an assumption).

That folder holds `profiles/<company>.yaml` and `cases/<case>/` (the older `perfiles/` and `casos/`
still work). **It is never uploaded to this repo.**

The profile's `language: es | en` field sets the language of the outputs (Excel labels, the
`SUPUESTO` / `ASSUMPTION` marker, console text). It defaults to `es`, so cases built with version
1.0 produce the same files. Spanish profile and input keys are still accepted.

## Next version

Version 1.1 (this branch) moves the repo to English with Spanish alongside, and closes the first
three items of the audit on real cases (15-10-2026): `procurement` and `cost-and-pricing` take and
return `assumptions` like the evaluation methods; one `research-data.json` format shared by
`research`, `executor` and `auditor`; and the map's core excludes a file that another declares
replaced («Replaces»). What remains:

1. **Self-contained skills.** The profile template inside each skill, so the scripts work on
   claude.ai without `--profile` and without copying anything outside the skill.
2. **Tested inside real Codex, Cursor and Gemini.** Today only the installed format was checked.
3. **Release versioning rule.** Every release bumps `version` in `.claude-plugin/plugin.json`:
   whoever installed the plugin receives no changes while the version stays the same.

## Where it comes from

Each method comes from Industrial Engineering courses and from its use in real companies. Each
method's `SOURCES.md` cites the bibliography; course material is not reproduced.

## License

Code and scripts: MIT. Guides and notes: CC BY-SA 4.0. See `LICENSE`.
