# Manual · step-by-step guide

The same method as `SKILL.md`, for a person. It walks through the fictitious **Ferretería Andes**
(a hardware store that sells over the counter and to contractors) whose purchasing process is
written from the first interview. The finished sample is in `tests/sample/`. Spanish version:
`GUIA.md`.

**What the script does and what it does not.** It creates the folders and files, records revisions
and checks every rule of `docs/MANUAL-FORMAT.md`. It does not write the steps: a person (or the
agent) writes them from the interview record, and the check says whether they hold.

## 0 · The profile and the data folder

The manual lives outside the repo, in the operator's data folder:

```
<data>/manual/<company>/
```

`<data>` is `--data`, else `$METHODIC_DATA`, else `$INGENIERO_DATOS`, else the folder
`methodic-data` next to the repo, else `ingeniero-agentico-datos` next to the repo. `<company>` is
the name of the profile file: `profiles/ferreteria-andes.yaml` gives `ferreteria-andes`. Its
`language` (`es` by default) picks the file names: `NEGOCIO.md`, `procesos/`, `entrevista/`… with
`es`; `BUSINESS.md`, `processes/`, `interview/`… with `en`.

## 1 · Create the manual

```bash
python scripts/manual.py init --company ferreteria-andes
```

It creates the index, the process and interview folders, the scope, an empty logbook, and the
backup and work folders. If something already exists it is kept, never overwritten: running it twice
is harmless.

## 2 · Read the interview record

The interview writes `entrevista/2026-10-16.md` (never by hand). For Ferretería Andes, batch 2:

```markdown
## Tanda 2 · El proceso · COMPRAS · 16-10-2026 15:40
Respondió: dueña

1. [pro-01] ¿Qué hace partir este proceso y quién lo pide? → Bodega pide el material por WhatsApp
2. [pro-02] ¿Cada cuánto ocurre? → Dos o tres veces por semana
3. [pro-03] ¿Cuáles son los pasos en orden de principio a fin? → Pedir tres cotizaciones por correo; compararlas en una planilla; emitir la orden
4. [pro-06] ¿Dónde quedan los archivos de este proceso? → Carpeta Compras, una planilla por mes
```

The bracketed id ties each answer to its question. `interview.py status --json` hands the same
answers over as a list (`id`, `process`, `maps_to`, `answer`, `gap`, `who`, `date`…), and
`maps_to` says where each one goes: `process:steps` to the steps, `process:operation.frequency` to
the Operation section, `scope:read` to the scope, and so on (table in `SKILL.md`). Each answer that
describes an action becomes a step. Each «No sé» becomes a gap.

## 3 · Create the process page

```bash
python scripts/manual.py new-process COMPRAS "Comprar material" --owner dueña
```

The page starts as Borrador (Draft), revision A, with one history row, and its row is added to the
index table. The code is in uppercase; steps will be `COMPRAS-01`, `COMPRAS-02`…

## 4 · Write the page

**SIPOC on top**, from what was said: who supplies (warehouse, three distributors), what comes in
(request, quotes), the process, what comes out (purchase order) and who receives it (warehouse,
accounting).

**Operation** (optional, right after SIPOC): what describes the process as a whole, each line with
its own source.

```markdown
## Operación
- Frecuencia: dos o tres veces por semana · Origen: entrevista · dueña · 16-10-2026
- Fallas habituales: un proveedor no responde y se compra al de siempre · Origen: entrevista · dueña · 16-10-2026
- Archivos: carpeta Compras, una planilla por mes · Origen: entrevista · dueña · 16-10-2026
```

Only those three labels (`Frequency`, `Usual failures`, `Files` in English); the lines count toward
the 800 words.

**Steps below**, one per action, each with exactly one source line:

```markdown
1. **COMPRAS-01** Bodega pide el material por WhatsApp.
   - Responsable: bodega · Herramienta: WhatsApp
   - Origen: entrevista · dueña · 16-10-2026
3. **COMPRAS-03** ◆ Se comparan las cotizaciones y se elige proveedor → `procurement`.
   - Responsable: compras · Herramienta: planilla
   - Origen: documento · comparativo-agosto.xlsx, hoja 1
4. **COMPRAS-04** ◆ Sobre $500.000 aprueba la dueña.
   - Responsable: dueña
   - Origen: SUPUESTO · monto no confirmado
5. **COMPRAS-05** Se emite la orden de compra desde la plantilla.
   - Responsable: compras · Herramienta: plantilla-oc.xlsx
   - Origen: observado · bitácora, línea 1
```

| Source | When | What the check verifies |
|---|---|---|
| `entrevista · <role> · <date>` | the operator said it | `entrevista/<date>.md` exists (and the role appears in it) |
| `documento · <file>[, <place>]` | a file shows it | the file is under a `read` folder of the scope |
| `observado · bitácora, línea N` | it was done and logged | line N of the logbook exists |
| `SUPUESTO · <why>` | it cannot be left out and nobody confirmed it | nothing; it is counted and listed |

- `◆` marks a decision, right after the code.
- `` → `procurement` `` says the step is done with that method; the skill must exist.
- The interview date is the batch's date, not the day the page is written.

**Gaps**: what is not known, with its date, written as the **missing datum**, not as the question.
The owner answered «No sé» to «¿Quién aprueba en ese momento y con qué criterio?», so the gap reads
`- Monto de aprobación de COMPRAS-04 · declarado el 16-10-2026`. Step COMPRAS-04 keeps the
assumption until the owner gives the amount.

## 5 · The scope

`alcance.yaml` holds the only machine-readable limits, written with the operator:

```yaml
read:
  - C:/Users/usuario/Documents/FerreteriaAndes
write_with_ok:
  - C:/Users/usuario/Documents/FerreteriaAndes/Planillas
never:
  - C:/Users/usuario/Documents/FerreteriaAndes/Sueldos
sensitive:
  - RUT y sueldos del personal
ok_by:
  - dueña
```

`ok_by` lists the roles that may give the OK for an intervention (`intervene` warns about any other).

A document source is looked up under `read` (a bare file name is searched there; `never` is not
searched). Without a scope, document sources are a warning; with `check --strict`, an error.

## 6 · Check

```bash
python scripts/manual.py check --company ferreteria-andes
```

For the sample:

```
  NEGOCIO.md                  113 / 400 palabras
  procesos/COMPRAS.md         159 / 800 palabras · En revisión · rev. B · 5 pasos
errores 0 · avisos 0 · supuestos 1
  SUPUESTO · COMPRAS-04 · monto no confirmado
OK
```

Any error ends in `FAIL` and exit code 1: **the page is not done until the check passes**. Words
are counted on the body only (frontmatter and History do not count): 400 for the index, 800 per
process. `--json` gives every finding with file and line.

## 7 · Revise and approve

After a change to the page:

```bash
python scripts/manual.py revise COMPRAS --change "COMPRAS-03 enlazado al comparativo" --by dueña
```

A history row is added, the revision moves to the next letter (A → B), the status becomes
En revisión, and the page date and the index row are updated.

**Approval is the operator's.** Only after the owner says yes to the page:

```bash
python scripts/manual.py revise COMPRAS --change "Aprobado" --approve --by dueña
```

The revision becomes `0` and the status Aprobado. The script refuses if the page has errors or if
`--by` is missing. After that, every change is approved again (`1`, `2`…); a change without
`--approve` to an approved page is refused, so it is drafted in `trabajo/` until the OK.

## 8 · What a session loads

The index (`NEGOCIO.md`) and the one process the task touches. The interview record and the logbook
are opened only to resolve a source. If a process passes 800 words, it holds two processes: split it.

## Errors the check stops

| Error | Code |
|---|---|
| A step written from memory | `source-missing` |
| Two sources mixed in one step | `source-multiple` |
| An Operation line without its source, or with another label | `source-missing` · `operation-line` |
| The interview date is not a batch's date | `interview-missing` |
| A guessed logbook line | `logbook-line-missing` |
| A document outside the scope | `document-missing` · `document-out-of-scope` |
| The same code twice, or a code that is not `COMPRAS-NN` | `code-duplicate` · `code-format` |
| «Aprobado» typed by hand with a letter revision | `status-revision` |
| Frontmatter edited without `revise` | `history-mismatch` · `history-sequence` |
| A date like 2026-10-16 or 31-02-2026 | `date-format` |
| A page missing from the index, or a row without its page | `index-row-missing` · `index-file-missing` |
| A page that grew too long | `cap-words` |
