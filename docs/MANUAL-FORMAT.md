# The operator's manual · shared format

Version 1.3 (16-10-2026). The single contract read by `interview`, `manual`, `intervene` and
`orchestrate`. If a skill and this file differ, this file rules; fix the skill.

## What it is

methodic understands a business by asking, writes what it learned as a **traceable manual** and
only then intervenes on the operator's computer. The manual is the memory between sessions: a new
session starts by reading one page instead of asking everything again.

Two layers that must not be confused:

- **The manual** is written complete. It has no total size limit, because it is split in pieces.
- **The context** (what a model loads) is the index plus the one process the task touches. The
  word caps apply here, and `manual.py check` (in `skills/manual/scripts/`) measures them.

## Where it lives

Outside the repo, in the operator's data folder, one manual per company profile:

```
<data>/manual/<company>/
```

`<data>` is resolved in this order: `--data` · `$METHODIC_DATA` · `$INGENIERO_DATOS` (legacy) ·
the repo's sibling `../methodic-data/` · the legacy sibling `../ingeniero-agentico-datos/`.
`<company>` is the profile's file name without `.yaml` (`profiles/<company>.yaml`); the profile's
`language` (`es` by default) chooses the file names below.

## The layout

| Piece | `language: es` | `language: en` | Cap | Loaded |
|---|---|---|---|---|
| Index of the business | `NEGOCIO.md` | `BUSINESS.md` | 400 words | Always |
| One file per process | `procesos/<CODE>.md` | `processes/<CODE>.md` | 800 words | When the task touches it |
| Interview record | `entrevista/AAAA-MM-DD.md` | `interview/YYYY-MM-DD.md` | none | Only to resolve a source |
| Scope of the computer | `alcance.yaml` | `scope.yaml` | none | By the scripts |
| Logbook | `bitacora.md` | `logbook.md` | none (append only) | Only to resolve a source |
| Backups | `respaldos/` | `backups/` | none | Never |
| Free work area | `trabajo/` | `work/` | none | When used |

A script reads both name sets and writes the one of the profile's language. A manual keeps the
names it was created with (same rule as `context/` in `ARCHITECTURE.md`).

Words are counted on the body only: the frontmatter and the `History` / `Historial` section do not
count. Every other limit of the conversation (150 words per answer, the rest to a file) is a rule of
the skills, not of the script.

## The index (`NEGOCIO.md` / `BUSINESS.md`)

```markdown
---
company: Ferretería Andes
date: 16-10-2026
revision: A
---
# Ferretería Andes

## Qué hace
Una o dos líneas.

## Clientes y cobro
...

## Quién decide
Roles, nunca nombres de personas reales en el repo (en los datos del operador, lo que él diga).

## Procesos
| Código | Proceso | Estado | Archivo | Duele |
|---|---|---|---|---|
| COMPRAS | Comprar material | En revisión · rev. B | procesos/COMPRAS.md | sí |

## Límites
Resumen humano de `alcance.yaml`.

## Huecos
- <dato que falta> · declarado el DD-MM-AAAA
```

English headings: `What it does`, `Customers and billing`, `Who decides`, `Processes`, `Limits`,
`Gaps`; table headers `Code | Process | Status | File | Pain`.

## A process page (format 1 · SIPOC on top, steps below)

```markdown
---
process: COMPRAS
title: Comprar material
status: En revisión
revision: B
date: 16-10-2026
owner: dueña
---
# COMPRAS · Comprar material

## SIPOC
| Proveedores | Entradas | Proceso | Salidas | Clientes |
|---|---|---|---|---|
| Bodega, 3 distribuidores | Solicitud, cotizaciones | Comprar material | Orden de compra | Bodega, contabilidad |

## Operación
- Frecuencia: dos o tres veces por semana · Origen: entrevista · dueña · 16-10-2026
- Fallas habituales: un proveedor no responde y se compra al de siempre · Origen: entrevista · dueña · 16-10-2026
- Archivos: carpeta Compras, una planilla por mes · Origen: entrevista · dueña · 16-10-2026

## Pasos
1. **COMPRAS-01** Bodega pide el material por WhatsApp.
   - Responsable: bodega · Herramienta: WhatsApp
   - Origen: entrevista · dueña · 16-10-2026
2. **COMPRAS-03** ◆ Se comparan las cotizaciones y se elige proveedor → `procurement`.
   - Responsable: compras · Herramienta: planilla
   - Origen: documento · comparativo-agosto.xlsx, hoja 1
3. **COMPRAS-04** ◆ Sobre $500.000 aprueba la dueña.
   - Responsable: dueña
   - Origen: SUPUESTO · monto no confirmado

## Huecos
- Monto de aprobación de COMPRAS-04 · declarado el 16-10-2026

## Historial
| Rev. | Fecha | Cambio | Aprobó |
|---|---|---|---|
| A | 16-10-2026 | Creado en la entrevista | — |
| B | 16-10-2026 | COMPRAS-03 enlazado al comparativo | dueña |
```

`## Operación` (`## Operation`) is optional and holds what describes the process as a whole:
`Frecuencia` / `Frequency`, `Fallas habituales` / `Usual failures`, `Archivos` / `Files`. Each line
ends with its own source, of the same four kinds as a step. It counts toward the 800 words.

English: `## Steps`, `- Responsible: … · Tool: …`, `- Source: …`, `## Gaps`, `## History`
(`Rev. | Date | Change | Approved by`), SIPOC headers `Suppliers | Inputs | Process | Outputs |
Customers`.

Rules, all checked by `manual.py check`:

1. **Code.** `<PROCESS>-NN`, optionally `.N` for a sub-step (`COMPRAS-03.2`); `<PROCESS>` is the
   frontmatter `process`, uppercase letters, digits and `-`. Unique within the manual. A code is
   never reused after a step is removed (the history says it was removed).
2. **Every step has exactly one source line**, of one of these four kinds:

   | Kind | es | en | Resolves to |
   |---|---|---|---|
   | Interview | `entrevista · <rol> · DD-MM-AAAA` | `interview · <role> · DD-MM-YYYY` | `entrevista/AAAA-MM-DD.md` must exist |
   | Document | `documento · <archivo>[, <lugar>]` | `document · <file>[, <location>]` | a path relative to a `read` root, or a bare name searched under the `read` roots (never inside `never`), or a file in the manual's `trabajo/`; warning, not error, when the scope is missing |
   | Observed | `observado · bitácora, línea N` | `observed · logbook, line N` | physical line N of the logbook must exist |
   | Assumption | `SUPUESTO · <por qué>` | `ASSUMPTION · <why>` | nothing; it is counted and listed |

3. **Decisions** carry `◆` right after the code. **A method call** is `→ \`<skill>\`` and the skill
   must exist in the repo's `skills/`.
4. **Status** is one of `Borrador · En revisión · Aprobado` (`Draft · In review · Approved`).
   **Revision** is a letter (`A`, `B`, …) until approved, `0` on approval, then `1`, `2`, …
   Two errors: an `Aprobado` page with a letter revision, and a numbered revision (`0`, `1`, …) on a
   page that is not `Aprobado`. A new letter revision moves `Borrador` to `En revisión`. A change to
   an approved page waits as a proposal in `trabajo/` until the operator approves it, which gives
   the next number. `--approve` needs `--by` and is refused while the page has errors. The index
   carries a `revision` but no history: its date changes with every revision of a page.
5. **History** has one row per revision, the last row's revision equals the frontmatter's.
6. Dates are `DD-MM-AAAA` everywhere (file names of the interview record use `AAAA-MM-DD` so they
   sort).

## The interview record (`entrevista/AAAA-MM-DD.md`)

Written by `interview.py record`, never by hand. One block per batch:

```markdown
## Tanda 1 · El negocio · 16-10-2026 15:10
Respondió: dueña

1. [neg-01] ¿Qué vende principalmente? → Productos
2. [neg-04] ¿Quién aprueba una compra? → Depende del monto
3. [neg-08] ¿Qué proceso le quita más tiempo hoy? → Compras
4. [lim-01] ¿Qué carpetas puedo leer? → No sé · HUECO
```

Each line carries the question's id from the bank in brackets: the id, not the text, ties an
answer to its question, so a question reworded later keeps its earlier answers. Round 2 headers
carry the process code (`## Tanda 3 · El proceso · COMPRAS · 16-10-2026 15:30`). English labels:
`## Batch N · …`, `Answered by:`, `· GAP`. A form filled at once (`interview.py form`) is recorded
as one block and may hold more than 4 answers.

`No sé` / `I don't know` is a valid answer: it becomes a gap in the index with its date. The
`manual` skill writes the gap as the missing datum («monto sobre el cual aprueba la dueña»), not as
the question's text.

## The scope (`alcance.yaml` / `scope.yaml`)

The only machine-readable limits. Written with the operator during the third interview round.

```yaml
read:              # folders methodic may read (absolute paths)
  - C:/Users/usuario/Documents/Empresa
write_with_ok:     # folders where a file may be changed, with backup and OK each time
  - C:/Users/usuario/Documents/Empresa/Planillas
never:             # never read nor touched, even inside read
  - C:/Users/usuario/Documents/Empresa/Sueldos
sensitive:         # kinds of data to treat with care (free text)
  - RUT y sueldos del personal
ok_by:             # roles that may give the OK for an intervention
  - dueña
```

`intervene.py log --ok` warns when the role is not in `ok_by` (an empty or missing `ok_by` accepts
any role and warns once).

The manual folder's own work area (`trabajo/`) is always writable without asking; the rest of
the manual folder is read-only for `intervene` (only `manual.py` and `interview.py` write there).
Anything not under `read` is out of scope. **Every `write_with_ok` folder must sit inside a `read`
folder**; `intervene.py check` warns otherwise. `never` wins over everything, the work area included.

## The logbook (`bitacora.md` / `logbook.md`)

Append only, one line per action on the operator's files, written by `intervene.py log`. The
logbook has **no header**: `manual.py init` creates it empty, so entry N is physical line N and a
source `observado · bitácora, línea N` points to exactly one action.

```
16-10-2026 15:42 · COMPRAS-05 · plantilla-oc.xlsx · columna IVA corregida · respaldo: respaldos/plantilla-oc_2026-10-16_1542.xlsx · verificado: total 119.000 = 100.000 × 1,19 · OK: operador
```

Fields: date and time · step code (or `—`) · file (path relative to its scope folder) · what
changed · backup path · how it was verified · who gave the OK. A file that did not exist before has
no backup: `log --new-file` writes `respaldo: — (archivo nuevo)`. Labels follow the manual's
language, like its file names. A line is never edited or deleted; a correction is a new line that
cites the old one (`corrige línea 7`).

## The intervention cycle

Plan → **OK of the operator** → backup → execute → verify → logbook. No step is skipped:

- **Plan**: what file, what change, why, which step of the manual, how it will be verified.
  `intervene.py check <path>` says whether the path is in scope and needs an OK.
- **OK**: the operator answers yes to that action. An OK covers one action, not a session. Bulk
  work (reorganizing a folder) is shown as several numbered plans at once and answered by number
  ("sí a 1 y 3"); a yes given before the plans are seen is not an OK.
- **Backup**: `intervene.py backup <path>` copies the file to `respaldos/` with a timestamp before
  any change.
- **Verify**: a fact, not "looks fine" (a total recomputed, a file reopened, a count).
- **Logbook**: `intervene.py log …`.

Never, at any level: delete (what is retired goes to the recycle bin or `_archivo`), install
software, use the network, send or pay anything (methodic prepares, the person sends), touch
anything outside the scope. The skills say so, and the **permissions file** that
`intervene.py permissions` generates from the scope blocks the usual commands in the operator's
agent (Claude Code). It is a barrier, not a sandbox: a rule matches the command's text, so a
roundabout command (`cmd /c del`, a script that opens files itself) can get through, and Codex,
Cursor and Gemini CLI offer no per-folder read deny. The limits are written in
`skills/intervene/GUIDE.md`; the operator's review of each plan stays the main control.
