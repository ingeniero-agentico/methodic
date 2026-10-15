# ingeniero-agentico · instructions for any agent

This file is read by Codex, Cursor, Hermes Agent and Gemini CLI (through `GEMINI.md`) when they
open the repo. Claude Code reads `CLAUDE.md`, which holds the rules for whoever **modifies** the
repo; the rules for whoever **uses** it are here. How to install it on each platform:
`docs/INSTALL.md`.

## What it is

Industrial engineering methods turned into skills ([Agent Skills](https://agentskills.io/specification)
format). Each method carries a `SKILL.md` (what the agent decides), a Python script (what it
calculates), input templates and a test that has to add up. **No number is calculated from memory:
it comes from the script.**

| Skill | What for |
|---|---|
| `orchestrate` | Receives a task, chooses the method and runs the six stages. Start here if it is not obvious which method applies |
| `map-context` | Stage 0: map of the task's folders and mode (first run or reread) |
| `research` | Stage 1: one datum with source, date and reliability for each gap the calculation needs |
| `procurement` | Who to buy what from, when each supplier covers only a part |
| `cost-and-pricing` | Real cost of a job and sale price by markup on cost |
| `economic-evaluation` | Whether a project or investment is worth it: cash flow, NPV, IRR, sensitivity |
| `financial-evaluation` | How to finance it: cash, loan, leasing or rental |
| `audit` | Stage 4: re-runs each script with the same input and compares |

Each skill lives in `skills/<name>/SKILL.md`. In `agents/` are the workers of each stage
(`cartographer`, `researcher`, `executor`, `auditor`) in Claude Code format; `install/install.py`
converts them to the Codex, Cursor and Gemini format.

## How to run a method

1. Read **only** the `SKILL.md` of the method that applies (not all four).
2. Build the input from `skills/<method>/templates/` with the person's data.
3. Run the script the `SKILL.md` names, from the skill's folder:
   `python scripts/<script>.py <input> --profile <company|path.yaml> ...`
4. Before trusting a new installation: `python scripts/<script>.py --test` has to end in `OK`.

Requirements: Python 3.11 or later, the standard library and `openpyxl` (for the Excel files).
Flags and file names from before v1.1 (Spanish: `--perfil`, `--probar`, `contexto/`…) still work.

## Private data (hard rule)

A company's data **never** enters this repo nor the folder where the skills were installed. It
lives in a separate folder, `ingeniero-agentico-datos/`, with `profiles/<company>.yaml` and
`cases/<case>/` (`context/`, the map and the plan of each task, go there too). Older data folders
use `perfiles/` and `casos/`; the scripts look in both.

Each script looks for the profile in this order:

1. `--profile <name or path>`.
2. The environment variable `INGENIERO_DATOS`.
3. The sibling folder `../ingeniero-agentico-datos/` (sibling of the repo; in an install by copy,
   sibling of the configuration folder, e.g. `~/ingeniero-agentico-datos/`).
4. `profiles/_template.yaml`: everything that comes from there is marked as an assumption.

If there is more than one profile and the task does not say which, **ask**. If the platform runs
in an isolated environment (claude.ai, a container), ask the person to upload their profile and pass
it with `--profile`. The profile's `language` (`es` or `en`, default `es`) sets the language of
the outputs for people.

## Orchestrate a task

Use the `orchestrate` skill. The six stages are always the same; only who does them changes.

| # | Stage | Read first |
|---|---|---|
| 0 | Map the context | `skills/map-context/SKILL.md` and `agents/cartographer.md` |
| 1 | Research (only if there are gaps) | `skills/research/SKILL.md` and `agents/researcher.md` |
| 2 | Plan and **ask for approval** | `skills/orchestrate/SKILL.md` |
| 3 | Execute (one method per plan row) | the method's `SKILL.md` and `agents/executor.md` |
| 4 | Audit | `skills/audit/SKILL.md` and `agents/auditor.md` |
| 5 | Consolidate | `skills/orchestrate/SKILL.md` |

The full contract (modes, core, one research format, contexts from before v1.1) is in
`ARCHITECTURE.md`.

### Without subagents ("without agents" mode)

If your platform does not launch subagents, or the person says "without agents", do the six stages
**yourself, in sequence, in this conversation**:

1. Do each stage reading the agent's file as if it were your instructions for that stage. When it
   ends, leave its output in `context/` before moving to the next one.
2. **Stage 2 is a gate.** Write `context/PLAN.md` with the stage table, show it to the person and
   **stop until they say "yes"** (or change a row). Run no method before that.
3. In stage 4 re-run each script with `skills/audit/scripts/rerun.py`; do not review your own
   calculation "from memory". Since the audit was not done by another agent, say so in the answer:
   "audit in the same conversation".
4. If a stage fails, report it and propose the fix; do not replace it with a calculation of yours.

### With subagents

Codex, Cursor and Gemini CLI have subagents, and Hermes delegates with `delegate_task`. Launch them
only after the "yes" of stage 2, one per plan row, in parallel what does not depend on each other.
Pass each one its plan row, the path of `context/`, the profile, the case folder and the `agents/`
file it gets. A subagent does not launch another: the orchestration stays in the main conversation.

## If you are going to modify the repo

Read `CLAUDE.md` first. The minimum: zero real data (no tax IDs, no companies, no people, no local
paths; the examples are fictitious), every number comes from a script with a test that adds up, the
`.md` files with frontmatter go in UTF-8 **without BOM**, and an aside goes in parentheses.
