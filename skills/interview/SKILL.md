---
name: interview
description: "Use when methodic must understand a business before touching anything, such as a new company or operator, a process nobody has written down, or a manual (NEGOCIO.md or BUSINESS.md) that is missing or full of gaps. Asks fixed questions in batches of 3 to 4 with options (AskUserQuestion where it exists, a numbered list otherwise) in three rounds (the business, each process that hurts, the limits of the computer) and records every answer with who gave it and when. «I don't know» becomes a dated gap, never a guess. Triggers include «entiende el negocio», «levanta el proceso», «hazme las preguntas», «documenta cómo trabajamos», «understand the business», «map this process», «what do you need to know about us?». Not for a single calculation when the data is already at hand (call the method skill directly, e.g. procurement), not for writing the manual pages (manual) and not for changing files (intervene). Asks in batches from a fixed bank and keeps the dated interview record the manual cites."
---

# Interview · understand the business by asking

**Ask, do not assume.** methodic learns a business from the people who run it, in short batches of
3 to 4 questions with options. What nobody knows is written down as a gap with its date, so the next
session asks it again instead of inventing it. The contract is `docs/MANUAL-FORMAT.md`.

The model asks and listens. The script decides what to ask and writes it down. The question bank is
fixed (`templates/questions.es.json`, `templates/questions.en.json`): it is never regenerated, so the
conversation only carries one batch and its answers.

```bash
python scripts/interview.py next   [--company X] [--data D] [--round N] [--process CODE] [--gaps] [--json]
python scripts/interview.py record --answers <answers.json|-> --who <role> [--process CODE]
python scripts/interview.py record --form <filled-form.md> [--who <role>]
python scripts/interview.py status [--json]
python scripts/interview.py form --round N [--process CODE]
python scripts/interview.py --test      # the fictitious case must end in OK
```

## When to use it

- First session with a company (no `<data>/manual/<company>/` yet).
- A process hurts and the manual has no page for it.
- The index lists gaps and the person who knows is available (`next --gaps`).
- `intervene` needs a folder the scope does not cover yet (round 3).

**Not** when the user brings the data for one calculation: call the method (`procurement`…).

Data folder, company and language are resolved as in `docs/MANUAL-FORMAT.md`; the record goes to
`<data>/manual/<company>/entrevista/AAAA-MM-DD.md` (`interview/YYYY-MM-DD.md` in English).

## How a batch is asked

1. `next --json` gives the batch: `round`, `process`, and per question `id`, `header`, `text`,
   `options`, `multi`, `free`.
2. **With AskUserQuestion** (Claude Code): one call per batch, one entry per question.
   `question` = `text`, `header` = `header` (12 characters or less), `options` = the bank's options as
   labels, `multiSelect` = `multi`. The tool adds «Other» for free text; the last option is always
   «No sé» / «I don't know». Do not reword, reorder or add options.
3. **Without it**, list the batch in text exactly as `next` prints it (numbered options plus «or
   another answer») and let the person reply in one message.
4. `free: true` means the real answer is usually written (paths, steps, names): invite it.
5. Record **right after** the answers arrive, before asking anything else:
   ```json
   {"round": 1, "who": "dueña", "answers": {"neg-05": "No sé", "neg-06": "6 a 20"}}
   ```
   Multi answers go as a list. `--who` is a role, never a real person's name in the repo. Round 2
   needs `"process": "COMPRAS"` (or `--process`). `-` reads the JSON from stdin.

A person who prefers to answer everything at once gets `form --round N` (same ids, same texts): they
tick `[x]` or write in «Otra respuesta», and `record --form` takes the file back as one block.

## The three rounds

| Round | What it settles | Lands in |
|---|---|---|
| 1 · The business | what it sells, customers, billing, price, size, who decides, tools, which processes hurt | the index (`index:*`) |
| 2 · The process (per process named in round 1) | trigger, frequency, steps, who, tool, where the files live, decisions and who approves, output, receiver, what fails, owner | the process page (`process:*`) |
| 3 · The limits | folders to read, folders to change with OK, never touched, sensitive data, who gives the OK, backup, who sends, shared folders | the scope (`scope:*`) and the index's limits |

`next` without flags walks round 1, then round 2 for each named process (painful first), then round 3.
`--round` and `--process` jump. Processes are named by question `neg-08` (they hurt) and `neg-11`
(worth writing down): «Compras» becomes `COMPRAS`; «COMPRAS: Comprar material» keeps its code.

## What the script does

| Command | What it does |
|---|---|
| `next` | the first 3 to 4 unanswered questions of the open round, skipping those whose `when` is false (`neg-09` only if a head decides) |
| `record` | appends one block to today's file, each line `N. [id] question → answer`; «No sé» lines end in `· HUECO` / `· GAP`. Never edits an earlier block. Refuses more than 4 answers, unknown ids, mixed rounds, round 2 without process, no role and empty answers |
| `status` | coverage per round and process, open gaps with their date, processes named, the next batch |
| `form` | the whole round as a fillable markdown form |

The record is the only memory: `status` and `next` read it back and tie each line to its question by
the `[id]` (old lines without id, by their exact text). The latest answer wins and closes its gap.

## How answers reach the manual

`interview` only records. The `manual` skill writes `NEGOCIO.md`, `procesos/<CODE>.md` and
`alcance.yaml`. It reads `status --json`, whose `answers` carry `maps_to`, `who` and `date`:

| `maps_to` | Goes to |
|---|---|
| `index:what_it_does` · `:customers_and_billing` · `:who_decides` · `:processes` · `:limits` | that section of the index |
| `process:sipoc.suppliers` · `.inputs` · `.outputs` · `.customers` | the SIPOC table |
| `process:steps` · `.responsible` · `.tool` · `.decision` | the steps (a decision carries `◆`) |
| `process:owner` | the page's `owner` |
| `process:operation.frequency` · `.failures` · `.files` | `## Operación` / `## Operation` (`files` also hints `document` sources) |
| `scope:read` · `:write_with_ok` · `:never` · `:sensitive` · `:ok_by` | `alcance.yaml` / `scope.yaml` |

Each answer used is cited `entrevista · <role> · DD-MM-AAAA`; each gap goes to `Huecos` as the
missing datum with `declarado el DD-MM-AAAA`. What nobody answered is `SUPUESTO` / `ASSUMPTION`.

## Rules

1. **One batch at a time.** Ask, record, then ask the next. Never two batches in one message.
2. **Never invent an answer.** Not from a website, not from "what shops usually do". If the person
   did not say it, it is not recorded.
3. **«No sé» is a good answer.** It becomes a gap with its date. Do not push; ask who knows and offer
   `next --gaps` when that person is available.
4. **The bank's text, verbatim.** The same wording every session keeps answers comparable.
5. **Short in the conversation.** Each message to the person is 150 words or less: the batch and one
   line of context. Summaries and pages go to files.
6. **Roles, not names.** `dueña`, `bodega`, `contador`.
7. **Nothing is touched.** The interview only writes the record. Folders named in round 3 are read
   later, by `intervene`, inside the scope.

## Typical errors

| Symptom | Cause |
|---|---|
| `status` warns that record lines do not match the bank | an unknown id, or an old line without id whose question was reworded; ask it again |
| `next` keeps asking an answered question | it was recorded under another process code, or not recorded |
| Round 2 says no process is named | `neg-08` was «No sé»; ask which process hurts, or use `--process CODE` |
| `VENTAS` and `VENTAS-2` | two names start with the same word; answer `CODE: name` in `neg-08` |
| The agent ticked options the person did not choose | invention; record the real answer in a new batch (the latest wins) |

Files: `GUIDE.md` / `GUIA.md` (step by step with Ferretería Andes) · `templates/questions.*.json` ·
`tests/` · `SOURCES.md`.
