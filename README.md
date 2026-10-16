# methodic

[Leer en español → README.es.md](README.es.md)

**A methodical documenter for AI agents.** methodic understands any business by asking the right
questions, writes what it learned as a **traceable manual** of its processes, and only then
intervenes on the operator's computer: with a plan, the operator's OK for each action, a backup
and a logbook line. Industrial engineering methods (procurement, costing, project evaluation,
financing) are its tools; every number comes from a script with a test.

It works for any company. Each company's data and manual live **outside this repo**, on the
operator's computer (see «Private data»).

## How it works

```
/new-task we lose a day every week comparing supplier quotes
```

1. **Interview.** Batches of 3 to 4 questions with options, one batch at a time. "I don't know" is
   a valid answer: it becomes a declared gap with its date. Three rounds: the business, the process
   that hurts, the limits (which folders it may read, what it may never touch).
2. **Document.** Each process becomes one page: SIPOC on top, numbered steps below. Every step has
   a code (`PURCHASES-03`), a responsible, a tool and **where it came from** (interview, document,
   observation or `ASSUMPTION`). Status, revision and history like any controlled document. A script
   checks all of it.
3. **Intervene.** Plan → **your OK for that one action** → backup → execute → verify with a fact →
   logbook line. It never deletes, installs, uses the network, sends or pays: it prepares, you send.
   A permissions file generated from your scope makes Claude Code block the usual commands for that,
   because a skill's text alone cannot. It is a barrier, not a sandbox: your review of each plan
   stays the main control.
4. **Calculate** when a step needs numbers: the method's script computes, an independent agent
   re-runs it, and the result is tied to the step of the manual that asked for it.

**It is cheap to run, on any plan.** A session loads the manual's index (≤ 400 words) and the one
process it touches (≤ 800 words), not the whole manual nor a re-interview. What a session learns is
written back before closing, so the next one starts by reading one page. Every token is paid by the
operator's own agent account.

## Skills

| Skill | What it does |
|---|---|
| [orchestrate](skills/orchestrate/) | Takes a task through the stages; start here when it is not obvious where to begin |
| [interview](skills/interview/) | Asks in batches with options and records the answers and gaps |
| [manual](skills/manual/) | Writes the index and the process pages and checks caps and traceability |
| [intervene](skills/intervene/) | Changes a file on the operator's computer only through the safe cycle |
| [map-context](skills/map-context/) | Maps the folders of a task before reading them |
| [research](skills/research/) | One outside datum per gap, with source, date and reliability |
| [audit](skills/audit/) | Re-runs every calculation and compares |
| [procurement](skills/procurement/) | Whom to buy what from, when each supplier covers only part of the list |
| [cost-and-pricing](skills/cost-and-pricing/) | What a job really costs and what to sell it for (markup on cost) |
| [economic-evaluation](skills/economic-evaluation/) | Whether a project pays off: cash flow, NPV, IRR, sensitivity |
| [financial-evaluation](skills/financial-evaluation/) | How to finance it: loan, leasing, rental or cash |

Each skill with a script is tested with `python skills/<skill>/scripts/<script>.py --test`, which
ends in `OK` or fails. `python security/run_tests.py` runs them all.

The stages, modes and the `context/` folder are in [ARCHITECTURE.md](ARCHITECTURE.md); the
manual's format in [docs/MANUAL-FORMAT.md](docs/MANUAL-FORMAT.md).

## How it is organized

```
methodic/
├── skills/        documenter (interview · manual · intervene), orchestration and the methods
├── agents/        workers for one stage: cartographer · researcher · executor · auditor
├── commands/      /new-task
├── docs/          manual format, install, MCP server
├── mcp/           MCP server: the methods as tools for any MCP client
├── install/       installer for Codex, Cursor, Gemini CLI, Hermes and others
├── security/      scanner, manifest and tests that guard every change
├── graph/         linked notes method ↔ course ↔ pattern, for Obsidian and graphify
└── profiles/      the company profile template (empty)
```

## Install

| Where | How | Notes |
|---|---|---|
| Claude Code | `/plugin marketplace add ingeniero-agentico/methodic` and `/plugin install methodic@methodic` | Brings skills, agents, `/new-task` and the MCP server |
| Claude Code without the plugin | `python install/install.py --platform claude-code` | Skills, agents and commands in `~/.claude/` |
| Claude Desktop / claude.ai | `python install/install.py --platform claude-desktop` and upload the ZIPs in Customize | No agents in chat: the stages run in sequence |
| Codex | `python install/install.py --platform codex` | Reads `AGENTS.md` |
| Cursor | `python install/install.py --platform cursor` | Reads `AGENTS.md` |
| Gemini CLI | `python install/install.py --platform gemini` | Reads `GEMINI.md` → `AGENTS.md` |
| Hermes Agent | `python install/install.py --platform hermes` | Delegates with `delegate_task` |
| Other Agent Skills agents | `python install/install.py --platform agents` | Skills in `~/.agents/skills/` |
| Any MCP client | `python mcp/server.py` in its configuration | The methods as tools |

Step by step in [docs/INSTALL.md](docs/INSTALL.md); the MCP server in [docs/MCP.md](docs/MCP.md).
Before letting methodic touch files, install the permissions file that `intervene` generates from
your scope (see [skills/intervene/GUIDE.md](skills/intervene/GUIDE.md)).

## Private data

Everything about a company lives in a data folder outside the repo, found in this order:
`--data` / `--profile` · `METHODIC_DATA` · the sibling folder `../methodic-data/` (the legacy
`INGENIERO_DATOS` and `../ingeniero-agentico-datos/` still work). It holds:

```
methodic-data/
├── profiles/<company>.yaml     currency, taxes, rates, language
├── manual/<company>/           the manual, the interview record, the scope, the logbook, backups
└── cases/<case>/               inputs, outputs and context/ of each calculation
```

**It is never uploaded to this repo.** The profile's `language: es | en` sets the language of every
output for a person, `es` by default.

## Next

1. **Self-contained skills.** The profile template inside each skill, so the scripts work on
   claude.ai without `--profile` and without copying anything outside the skill.
2. **Tested inside real Codex, Cursor and Gemini.** Today only the installed format was checked.
3. **The documenter on a real business**, end to end: interview, manual approved by the operator,
   one intervention with its logbook line.

## Where it comes from

The methods come from Industrial Engineering courses and their use in real companies; the
documenter, from documenting real processes for small businesses. Each skill's `SOURCES.md` cites
the bibliography; course material is not reproduced.

## License

Code and scripts: MIT. Guides and notes: CC BY-SA 4.0. See `LICENSE`.
