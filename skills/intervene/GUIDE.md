# Intervene · step-by-step guide

The same method as `SKILL.md`, for a person. It follows a fictitious case: at **Ferretería Andes**
the owner asks the agent to fix the purchase order template, whose VAT column comes out empty.
Spanish version: `GUIA.md`. The contract behind every rule is `docs/MANUAL-FORMAT.md`.

**What this skill is.** A way to let an agent change files on your computer without losing control:
it reads only the folders you authorized, writes freely only in its own work folder, and changes one
of your files only after showing you the plan, getting your yes for that one change and making a
backup. Then it checks the result with a fact and writes one line in the logbook.

**What it is not.** The skill's text guides the model; it does not stop it. What stops it is the
permissions of the agent program you use. That is why the skill generates a permissions file for
Claude Code, and why step 1 below is to install it.

## 0 · What must exist first

| Piece | Where | Who writes it |
|---|---|---|
| Profile | `<data>/profiles/ferreteria-andes.yaml` | you (`language: es` or `en`) |
| Manual | `<data>/manual/ferreteria-andes/` | the `interview` and `manual` skills |
| Scope | `<data>/manual/ferreteria-andes/alcance.yaml` | you and the agent, in the third interview round |

`<data>` is `--data`, or `$METHODIC_DATA`, or `$INGENIERO_DATOS`, or the folder `methodic-data`
next to the repo (then the legacy `ingeniero-agentico-datos`). The example scope is
`templates/alcance-ferreteria-andes.yaml`:

| List | Ferretería Andes | Meaning |
|---|---|---|
| `read` | `C:/Users/usuario/Documents/FerreteriaAndes` | may be read |
| `write_with_ok` | `.../FerreteriaAndes/Planillas` | may be changed, one approved change at a time |
| `never` | `.../FerreteriaAndes/Sueldos`, `.../Bancos` | never read nor touched |
| `ok_by` | `dueña`, `encargado de compras` | roles that may give the OK; `log --ok` warns for any other (an empty list accepts any role and warns) |

Anything not under `read` is out of scope, **including a `write_with_ok` folder that is not inside a
`read` folder** (the script warns about it). The manual's `trabajo/` folder is always free to write.

## 1 · Install the permissions (Claude Code)

```bash
python skills/intervene/scripts/intervene.py permissions --platform claude-code
```

It writes `trabajo/permisos-claude-code.json` (`work/claude-code-permissions.json` with
`language: en`) and nothing else: it never touches your agent's configuration. What it contains:

| List | Rules | Effect |
|---|---|---|
| `allow` | `Read(//c/.../FerreteriaAndes/**)`, the manual folder; `Edit(//c/.../trabajo/**)` | read and work without prompts |
| `ask` | `Edit(//c/.../Planillas/**)`, the scope file, `mcp__*` | a prompt before every change there, and before every MCP tool (mail, chat, payments) |
| `deny` | `Read` and `Edit` of every `never` folder; `Edit` of the backups and the logbook; `Edit` of `read` folders that hold nothing writable; deletions (`rm`, `rmdir`, `del`, `rd`, `Remove-Item`...), network (`curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod`, `WebFetch`, `WebSearch`), installs (`pip install`, `npm install`, `npx`, `winget`, `choco`, `msiexec`...) and `git push` | refused |

It also sets `defaultMode: "default"` (ask before edits) and disables the bypass and auto modes.
`templates/claude-code-settings.json` is the same idea without paths, for any folder.

Two ways to use it (you do this, not the agent):

- **One session:** start Claude Code with the file:
  `claude --settings "C:/Users/usuario/methodic-data/manual/ferreteria-andes/trabajo/permisos-claude-code.json"`.
  It applies above your user and project files and below managed settings, and changes no file.
- **Always, for one folder:** put the `permissions` block of the generated file in the
  `.claude/settings.local.json` of the folder where you start Claude Code. If that file already has
  lists, add the rules to them: Claude Code merges lists across files, and a deny always wins.

Start Claude Code **in the manual's `trabajo/` folder**: then the only working directory is the work
area, and everything else is reached through the rules above. Run `/permissions` to see the rules
loaded and `/status` to confirm the file was read.

**Checked against the official documentation on 16-10-2026:**
`https://code.claude.com/docs/en/permissions` (rule syntax, `allow`/`ask`/`deny` order, `Bash`,
`PowerShell`, `Read`/`Edit` paths, `WebFetch`, symlinks, modes) and
`https://code.claude.com/docs/en/settings` (file scopes, `--settings`, list merging, `$schema`). The
address `code.claude.com/docs/en/iam` now opens the authentication page; permissions moved to
`/permissions`. What those pages say, and what this file relies on:

- Rules are checked deny, then ask, then allow; the first match decides. An allow cannot carve an
  exception out of a deny.
- `Bash(rm *)` and `Bash(rm:*)` are the same; a trailing ` *` also matches the bare command.
  PowerShell rules use the same shape, are case-insensitive and match common aliases (the page's
  example: `Get-ChildItem` also matches `gci`, `ls`, `dir`; by the same rule `Remove-Item` covers
  `rm` and `del` typed in PowerShell).
- On Windows a path is matched in POSIX form: `C:\Users\usuario` becomes `/c/Users/usuario`, so an
  absolute rule is `//c/Users/usuario/...`. A single leading `/` is **not** absolute.
- `Edit` rules cover every built-in editing tool, `Write` included; a `Read` deny also blocks
  `Edit` and `Write` on that path. Path rules written as `Write(...)` are never consulted.
- A bare `WebFetch` or `WebSearch` in `deny` removes the tool.
- Through a symlink or junction, an allow needs both the link and its target to match; a deny needs
  either.

**What it cannot stop (also from those pages, said plainly):**

- A `Bash` or `PowerShell` rule matches the command text, not the program. `Bash(rm *)` stops
  `rm -rf x/` but not `/bin/rm -rf x/` nor `bash -c 'rm -rf x/'`; `cmd /c del` is not matched either.
- `Read` and `Edit` rules do not reach a script that opens files itself (a Python script run by the
  agent). That is why `intervene.py` checks the scope on its own.
- Read-only shell commands (`cat`, `ls`, `grep`) run without a prompt even outside the working
  directory. A `Read` deny does reach `cat`, `head`, `tail` naming a `never` path, but not
  `grep -r` started from a folder above it.
- A `read` folder that contains a `write_with_ok` folder cannot be denied for `Edit` without also
  blocking the writable one (a deny wins over everything, and the `!` carve-out works only for
  relative paths). Changes there fall to the normal prompt of `default` mode.
- For a barrier that does not depend on the command text, Claude Code has an OS-level sandboxing
  feature; this skill does not configure it.

**Other agents.** `templates/codex.md`, `cursor.md` and `gemini-cli.md` say what was verified for
each. Where a piece is not verified (for example a per-folder read deny), the skill's rules and
`intervene.py check` are the only barrier there.

## 2 · The case, step by step

The owner says: "arregla la plantilla de OC, la columna IVA sale vacía". The process page
`procesos/COMPRAS.md` has the step **COMPRAS-05** (issue the purchase order).

**Check.** `intervene.py check C:/Users/usuario/Documents/FerreteriaAndes/Planillas/plantilla-oc.xlsx --write`
answers `write-needs-ok`: it may be changed, through the cycle.

**Plan.** The agent writes the plan and shows it:

```
Plan 1 · COMPRAS-05 · pide OK
   Archivo   C:/Users/usuario/Documents/FerreteriaAndes/Planillas/plantilla-oc.xlsx
   Cambio    columna IVA corregida
   Por qué   la OC salía sin IVA
   Verificar total = neto × 1,19
   Antes     respaldo en respaldos/
¿Lo hago? Responde sí o no (este OK cubre solo esta acción).
```

**OK.** The owner answers "sí". That yes covers this change only.

**Backup.** `intervene.py backup .../plantilla-oc.xlsx` prints
`respaldos/plantilla-oc_2026-10-16_1542.xlsx`. A second backup in the same minute gets seconds
(`_154200`), then `-2`: one never overwrites another.

**Execute and verify.** The agent fixes the column, reopens the file and recomputes a row: net
100.000, VAT 19.000, total 119.000. That is the fact.

**Logbook.** `intervene.py log --step COMPRAS-05 --file .../plantilla-oc.xlsx --change "columna IVA corregida" --backup respaldos/plantilla-oc_2026-10-16_1542.xlsx --verified "total 119.000 = 100.000 × 1,19" --ok dueña`
appends:

```
16-10-2026 15:42 · COMPRAS-05 · plantilla-oc.xlsx · columna IVA corregida · respaldo: respaldos/plantilla-oc_2026-10-16_1542.xlsx · verificado: total 119.000 = 100.000 × 1,19 · OK: dueña
```

and says it is line 7, for example. The process page can now cite `observado · bitácora, línea 7`.

## 3 · Reorganizing a folder

One plan per file: "move `cotizacion (3).pdf` to `Cotizaciones/2026-10_proveedor-a.pdf`". Several
plans can be shown together, numbered, and answered together by number ("sí a 1, 2 y 4"). Nothing is
deleted: what is retired goes to `_archivo` (through the cycle) or the person sends it to the recycle
bin.

## 4 · When something goes wrong

- **The verification fails.** The agent says so and proposes restoring the backup as a new plan.
  The restore gets its own logbook line, citing the failed one with `--corrects N`.
- **A logbook line is wrong.** It is never edited: a new line with `--corrects N`.
- **You asked for something forbidden** (delete, install, send, pay, a folder outside the scope):
  the agent leaves it ready in `trabajo/` (the command, the draft, the list) and you do it.

## Errors the method catches

| Error | Where it is caught |
|---|---|
| A path that escapes through `..`, a link or a junction | `check` judges the requested and the real path; the stricter wins |
| A change without a backup | `log` refuses a backup that does not exist or is outside `respaldos/` |
| "Looks fine" as verification | `log` refuses it |
| A rewritten logbook | `log` only appends; `--corrects` adds a line |
| A backup overwritten by the next one | backups are created in exclusive mode, with seconds and a counter |
| A permissions file installed by the agent | `permissions` writes only inside `trabajo/` |

The test (`python scripts/intervene.py --test`) builds this case in a temporary folder (with a CSV in
place of the workbook), runs every verdict, the whole cycle and the refusals, removes its temporary
folder and ends in `OK`.
