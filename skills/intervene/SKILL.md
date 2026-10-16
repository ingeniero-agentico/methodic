---
name: intervene
description: "Use when the operator asks for a change on their own computer and it must be done methodically and safely, such as fixing a spreadsheet, renaming or moving files, filling a template, reorganizing a folder or applying a change the manual describes. Runs the cycle plan, OK of the person, backup, execute, verify with a fact, logbook line. Reads only inside the authorized folders, writes freely only in the manual's work folder, and changes an operator file only after an OK for that one action and a backup. Never deletes, installs, uses the network, sends or pays. Also writes the agent's permissions file from the scope. Triggers: \"arregla esta planilla\", \"cambia esto en mi PC\", \"ordena la carpeta\", \"aplica el cambio\", \"hazlo en mi computador\". Not for learning the business or writing the manual (interview, manual), nor for computing a method's numbers (procurement and other methods). Without a scope file, run the interview first. Cambia archivos del operador con plan, OK, respaldo, verificación y bitácora."
---

# Intervene · change the operator's files, one approved action at a time

**One action, one OK, one backup, one fact, one logbook line.** The contract is
`docs/MANUAL-FORMAT.md` ("The scope", "The logbook", "The intervention cycle"); if this file and the
contract differ, the contract rules.

**Honesty first.** This text guides the model; it does not enforce anything. The barrier is the
agent platform's permissions. `intervene.py permissions` writes a Claude Code permissions file from
the scope, and the person installs it (`GUIDE.md`, "Install the permissions"). On a platform without
one (`templates/codex.md`, `cursor.md`, `gemini-cli.md` say what was verified), the rules below are
the only barrier, and you say so to the person once.

```bash
python scripts/intervene.py check <path> [--write]          # verdict against the scope
python scripts/intervene.py plan --file P --step CODE --change "..." --why "..." --verify "..."
python scripts/intervene.py backup <path>                   # prints respaldos/<name>_<stamp>.<ext>
python scripts/intervene.py log --step CODE --file P --change "..." --backup respaldos/... \
       --verified "..." --ok <who>                          # prints the line number
python scripts/intervene.py permissions --platform claude-code
python scripts/intervene.py --test                          # must end in OK
```

Every subcommand takes `--data`, `--company` and `--json`. The data folder is found as the contract
says (`--data` · `$METHODIC_DATA` · `$INGENIERO_DATOS` · `../methodic-data` ·
`../ingeniero-agentico-datos`); the profile's `language` picks `alcance.yaml`/`bitacora.md`/
`respaldos/`/`trabajo/` (`es`) or `scope.yaml`/`logbook.md`/`backups/`/`work/` (`en`).

## Before the first action

1. The manual and its scope exist. Without `alcance.yaml` the script refuses everything: run the
   interview (third round) first. Read `NEGOCIO.md` and the one process page the task touches.
2. Ask once whether the permissions file is installed. If not, generate it and tell the person how
   to install it; you never install it yourself.

## The verdicts

| Verdict | Read | Write |
|---|---|---|
| `work-area-free` | yes | yes, no OK (the manual's `trabajo/`) |
| `write-needs-ok` | yes | only through the cycle |
| `read-only` | yes | no (includes the manual folder, the logbook and the backups) |
| `never` | no | no |
| `out-of-scope` | no | no |

Links, junctions and `..` are resolved first; the requested path and its real path are both judged
and the stricter verdict wins.

## The cycle

1. **Plan.** `check --write`, then `plan` with the file, the change, why, the step code and how it
   will be verified. Show the printed block as is. One plan is one file and one change.
2. **OK.** The person answers yes to that plan, and `--ok` names their role. If the role is not in
   the scope's `ok_by`, `log` warns: confirm they could approve it. **An OK covers one action, not a
   session.** Several
   numbered plans may be shown together; the answer must name them ("sí a 1 y 3"). Silence,
   "dale" before seeing the plan, or an OK given an hour ago for something else is not an OK.
3. **Backup.** `backup <path>` before touching the file. It never overwrites a backup. A new file
   has nothing to back up: log it with `--new-file --backup —`.
4. **Execute** exactly the plan. If the file is not what the plan assumed (another sheet, another
   total), stop and plan again.
5. **Verify** with a fact (below). If it fails, say so, and propose restoring the backup as a new
   plan.
6. **Logbook.** `log` appends one line and prints its number. Cite it in the manual as
   `observado · bitácora, línea N`. A wrong line is never edited: `--corrects N` adds a new one.

## What counts as verification

A fact someone else could repeat: a total recomputed (`119.000 = 100.000 × 1,19`), the file
reopened and the cell read, a count of files before and after, the new name present and the old
one absent. "Se ve bien", "OK", "listo" are refused by the script. If the number comes from a
method, the method's script computes it (repo rule 3).

## Step codes

`--step` is the manual's code (`COMPRAS-05`, `COMPRAS-03.2`); it ties the action to the step it
changes, so the process page can cite the logbook line. If no step applies, `—`, and the gap goes to
the manual (a step that happens and is not written down).

## Never

At any level and whoever asks: **delete** (what is retired goes to the recycle bin or `_archivo`,
through the cycle), **install** software, use the **network**, **send or pay** anything, touch anything
**outside the scope** or in `never`. Never edit the logbook, a backup or the scope by hand.

## When the person asks for something forbidden

Prepare it and let the person do it. Say what you will not do and why in one line, then leave it
ready:

| Asked | What you do |
|---|---|
| "Borra esos archivos" | Plan the move to `_archivo` (or list them for the person to send to the recycle bin) |
| "Instala X" | Write the exact command in `trabajo/`; the person runs it |
| "Mándale el correo" / "paga la factura" | Draft the mail or the payment details in `trabajo/`; the person sends or pays |
| A folder outside the scope | Ask whether to add it to `alcance.yaml` (with the person, as in the interview); do not read it meanwhile |
| "Hazlo todo sin preguntarme" | Explain that each change needs its OK; offer numbered plans to answer together |

## Typical errors

| Symptom | Cause |
|---|---|
| `out-of-scope` for a folder the person "gave" | It is in `write_with_ok` but not under `read`: the contract leaves it out (`check` warns) |
| `out-of-scope` on a path inside `read` | It goes through a link or junction that ends outside |
| `log` refused: backup does not exist | The backup was skipped, or its path was mistyped (copy what `backup` printed) |
| `log` refused: verification | A judgement was written instead of a fact |
| Two logbook lines for one action | One should have been `--corrects N`; never delete the extra one |
| The agent edited without a prompt | The permissions file is not installed, or the session runs in a mode that skips prompts |

## Files

`GUIDE.md` (the method for a person, with Ferretería Andes; Spanish in `GUIA.md`) ·
`templates/claude-code-settings.json` (generic permissions) · `templates/alcance-ferreteria-andes.yaml`
· `templates/codex.md`, `cursor.md`, `gemini-cli.md` · `tests/expected.json` · `SOURCES.md`.
