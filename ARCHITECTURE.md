# Architecture · how a task is orchestrated

Version 2.1 (15-10-2026). Replaces the `orquestador` agent of v1. English since v1.1 (names in
the table at the end).

## The constraint that rules

In Claude Code **an agent cannot launch other agents**. That is why:

- The **orchestrator is a skill** (`skills/orchestrate/`) that runs in the main conversation, the
  only one that can launch agents.
- The **agents are workers** (`agents/`): each one does one stage, with its skills and its model.

## The six stages

| # | Stage | Who | Model | Reads | Leaves |
|---|---|---|---|---|---|
| 0 | Map the context | agent `cartographer` + skill `map-context` | economical | the task's folders | `context/MAP.md` + `context/graph.json` + `context/fingerprints.json` + `context/changes.json` |
| 1 | Research | agent `researcher` + skill `research` | strong | the map and the gaps | `context/RESEARCH.md` + `context/research-data.json` (each datum with source, date and reliability) |
| 2 | Plan and ask | skill `orchestrate` | the session's | map + research | `context/PLAN.md`; **it is shown to the person and waits for their yes** |
| 3 | Execute | agent `executor` (one per method, in parallel if they do not depend on each other) | per the plan | the plan and its input | the method's output in `cases/` + `context/runs/<id>.json` |
| 4 | Audit | agent `auditor` (read-only) | strong | inputs, scripts and outputs | `context/AUDIT.md` (re-runs each script and compares) |
| 5 | Consolidate | skill `orchestrate` | the session's | everything above | the answer: decision, deciding assumptions, where it was left, what is missing |

## Two modes, depending on what is already known

The mode is decided by `map-context` comparing `fingerprints.json` (size, date and sha1 of each
file) and the unread changes in `changes.json` with the disk. The model does not choose it "by eye".

| | First run (`first-run`) | Reread (`reread`) |
|---|---|---|
| When | There is no map, or the scope is new, or too much changed | There is a map and the fingerprints barely changed |
| Stage 0 | Full map | Only the files that changed |
| Stage 1 | Full research of the gaps | Skipped, unless the plan declares a new gap |
| Reading | The source files | `MAP.md` (≤ 3,000 words) + its **core** (max. 3 files) + the ones that changed |
| Models | Strong in research and audit | Economical everywhere except the audit |
| For whom | Whoever arrives at a topic and researches it for the first time | Whoever returns to the same topic with a bounded budget |

**The saving of a reread is reading the map instead of the folders.** The map says what is there,
where, from when, what each file says in one line and what links to what. But **it orients, it does
not replace**: tested on a real job (15-10-2026), the map said what to open but not what was pending
nor the figures. That is why it carries a **core** of up to 3 files that are always read (the job
file, the current list, the README), chosen by a fixed rule and correctable by hand with `--core`.
**A file that another declares replaced** («Replaces:» or «Reemplaza a:») never enters the core by
rule: the old list stays out and the current one gets in.

Changes accumulate in `context/changes.json` until `orchestrate` marks them read when
consolidating: two runs of the cartographer in a row do not erase what nobody read.

## The request (stage 2)

No agent is launched without the person approving the plan. The plan is a table:

| Stage | Agent | Skill | Model | Input | Output | Depends on |
|---|---|---|---|---|---|---|

plus the mode, the number of agents and a rough cost estimate (agents × model). The person answers
"yes", changes a row or asks for another mode. If the person's environment does not allow agents,
`orchestrate` runs the stages in sequence in the same conversation.

## Where `context/` lives

Next to the task's data, never in the public repo:
`<data>/cases/<case>/context/`, or `<task folder>/context/` if there is no data folder. The data
folder is `ingeniero-agentico-datos/` (or `INGENIERO_DATOS`); the scripts look in `profiles/` then
`perfiles/`, and in `cases/` then `casos/`.

## One research format (read by `research`, `executor` and `auditor`)

`context/research-data.json` is validated by `skills/research/scripts/validate_research.py`. The
executor fills inputs from it and the auditor checks against it, both through the same fields:
`gaps[].chosen` (which datum), `gaps[].for` (which input field), `data[].reliability` (A–D) and the
usage derived from `usable` and `assumption` (`yes` · `ASSUMPTION` · `no`). Definition in
`skills/research/SKILL.md` ("The format").

## Reliability of a source (used by `research` and `auditor`)

| Level | What it is |
|---|---|
| A | Norm, law, official body, the client's own document |
| B | Academic book or paper, manufacturer's technical manual |
| C | Supplier site, quote, specialized press |
| D | Blog, forum, AI without a source: it only orients, it never enters a calculation without being marked as an assumption |

## Contexts written before v1.1

The Spanish version wrote `contexto/` with Spanish file names and keys. Everything is still read:

| Before v1.1 | Since v1.1 |
|---|---|
| `contexto/` | `context/` |
| `MAPA.md` · `grafo.json` · `huellas.json` · `cambios.json` | `MAP.md` · `graph.json` · `fingerprints.json` · `changes.json` |
| `INVESTIGACION.md` · `datos-investigados.json` | `RESEARCH.md` · `research-data.json` |
| `AUDITORIA.md` · `ejecuciones/` · `sensibilidad/` | `AUDIT.md` · `runs/` · `sensitivity/` |
| modes `primera-vez` · `relectura` | `first-run` · `reread` |
| `{SALIDA}` in a manifest | `{OUT}` |

**A context keeps the layout it was created with.** `map_context.py` detects it (English
`fingerprints.json` first, then `huellas.json`) and writes the same names it found, so an old case
does not end up with two maps; `validate_research.py` and `rerun.py` accept the Spanish keys. The
agents keep writing into an old `contexto/` with its Spanish names. A new case gets the English
names.

## Language

Everything an agent or a developer reads is English. Outputs for a person (Excel labels, the
assumption marker `SUPUESTO`/`ASSUMPTION`, `PLAN.md`, `AUDIT.md`, the answer) follow the profile's
`language` field, `es` by default. People-facing guides keep a Spanish version (`GUIA.md` in each
skill, `README.es.md`).
