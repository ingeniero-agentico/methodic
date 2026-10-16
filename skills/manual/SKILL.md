---
name: manual
description: "Use when how a business works must be written down as a traceable operator's manual, after the interview recorded answers, when documents or observed actions must become a process page, or when an existing manual must be revised, approved or checked before anyone relies on it. Writes the business index (NEGOCIO.md or BUSINESS.md) and one page per process (SIPOC on top, coded steps below, every step with exactly one source, interview, document, observed or ASSUMPTION), records revisions and the operator's approval, and checks every rule of docs/MANUAL-FORMAT.md (word caps, codes, sources that resolve, history). Triggers: \"documenta el proceso\", \"arma el manual\", \"escribe el procedimiento\", \"estandariza cómo se hace\", \"revisa el manual\", \"write the procedure\", \"check the manual\". Not for asking the questions (interview), not for changing the operator's files (intervene), not for computing figures (the method skills). Escribe y verifica el manual trazable del operador, cada paso con su origen."
---

# Manual · write the traceable manual

**A step without a source is not in the manual.** The manual is the memory between sessions: a new
session reads one page instead of asking everything again. That only works if every line can be
traced back to what the operator said, a document, or something observed and logged. What nobody
said goes to Gaps, never into a step.

The format is the contract in `docs/MANUAL-FORMAT.md`; this skill writes it and checks it. The
agent writes the pages; the script creates the files, records revisions and checks every rule.

```bash
python scripts/manual.py init --company <name> [--data <folder>]
python scripts/manual.py new-process COMPRAS "Comprar material" --owner dueña
python scripts/manual.py revise COMPRAS --change "COMPRAS-03 linked to the comparison" [--by <role>] [--approve]
python scripts/manual.py check [--company <name>] [--strict] [--json]
python scripts/manual.py --test      # the fictitious Ferretería Andes manual must end in OK
```

## When to use it

- The interview recorded answers and a process must be written.
- A page changed, or the operator approved it, and the revision must be recorded.
- Before `intervene` touches a file: the step it serves must exist in the manual.

Not for asking the questions (`interview`), not for changing the operator's files (`intervene`),
not for computing a figure (the method skills, called from a step with `` → `skill` ``).

## Where it lives

`<data>/manual/<company>/`, outside the repo. `<data>` is `--data`, else `$METHODIC_DATA`, else
`$INGENIERO_DATOS`, else the repo's sibling `../methodic-data/`, else `../ingeniero-agentico-datos/`.
`<company>` is the profile's file name without `.yaml`; its `language` (`es` by default) picks the
file names. Both name sets are read; a manual keeps the names it was created with.

## How a page is written from the interview

The handover is `interview.py status --json`: its `answers` list carries, per answer, `id`,
`round`, `process`, `maps_to`, `question`, `answer`, `gap`, `who`, `date`, `batch` and `file`.
Read it, plus the index; open `entrevista/AAAA-MM-DD.md` only to confirm a line.

| `maps_to` | Goes to |
|---|---|
| `index:what_it_does` · `index:customers_and_billing` · `index:who_decides` · `index:processes` · `index:limits` | that index section |
| `process:sipoc.suppliers` · `.inputs` · `.outputs` · `.customers` | the SIPOC row |
| `process:steps` · `process:steps.responsible` · `.tool` · `.decision` | the steps (a decision carries `◆`) |
| `process:owner` | the page's `owner` |
| `process:operation.frequency` · `process:operation.failures` · `process:operation.files` | `## Operación`: `Frecuencia`, `Fallas habituales`, `Archivos`; `files` also feeds `document` sources and `scope:read` |
| `scope:read` · `scope:write_with_ok` · `scope:never` · `scope:sensitive` · `scope:ok_by` | `alcance.yaml` / `scope.yaml` |

1. `new-process <CODE> "<title>" --owner <role>` (the answer's `process`) creates the page
   (Borrador/Draft, rev. A) and its index row. Steps are `COMPRAS-01`, `COMPRAS-02`, sub-steps
   `COMPRAS-03.2`; a code is never reused after a step is removed.
2. One numbered step per action, in order, with exactly **one** source line:

   ```markdown
   1. **COMPRAS-01** Bodega pide el material por WhatsApp.
      - Responsable: bodega · Herramienta: WhatsApp
      - Origen: entrevista · dueña · 16-10-2026
   ```

   | Kind | es | en |
   |---|---|---|
   | Interview | `entrevista · <rol> · DD-MM-AAAA` | `interview · <role> · DD-MM-YYYY` |
   | Document | `documento · <archivo>[, <lugar>]` | `document · <file>[, <location>]` |
   | Observed | `observado · bitácora, línea N` | `observed · logbook, line N` |
   | Assumption | `SUPUESTO · <por qué>` | `ASSUMPTION · <why>` |

   An answer gives `entrevista · <who> · <date>` (the batch's date, never today's). A document is a
   path under a `read` folder, or a bare name searched there (never inside `never`). An observed
   source is a physical logbook line. `◆` goes right after the code; a method call is
   `` → `procurement` `` and the skill must exist.
3. `## Operación` (optional, after SIPOC): `- Frecuencia: … · Origen: …`, same for
   `Fallas habituales` and `Archivos`. Each line ends with its own source and counts toward the
   800 words.
4. **An answer with `gap: true` goes to Gaps as the missing datum, not as the question's text**:
   `- Monto sobre el cual aprueba la dueña · declarado el 16-10-2026`, never «¿Desde qué monto
   aprueba usted?». It is never a step.
5. **An assumption only when the step cannot be left out**, as `SUPUESTO · <why>`. The check counts
   and lists them; the operator confirms or corrects each one.
6. Roles, never names of real people.

## The check is the gate

`check` applies every rule of the contract and exits 1 on any error. **A page with errors is not
shown as done**: fix it and run again. The summary gives errors, warnings, assumptions and words
per piece against its cap (index 400, process 800; frontmatter and History do not count).
`--json` gives every finding with file and line.

Error codes: `manual-missing` · `index-missing` · `frontmatter` · `section-missing` · `cap-words`
· `code-format` · `code-duplicate` · `process-mismatch` · `source-missing` · `source-multiple` ·
`source-kind` · `operation-line` · `interview-missing` · `logbook-line-missing` · `document-missing` ·
`document-out-of-scope` · `decision-mark` · `skill-unknown` · `status-invalid` ·
`revision-invalid` · `status-revision` · `history-missing` · `history-mismatch` ·
`history-sequence` · `date-format` · `sipoc-table` · `index-row-missing` · `index-file-missing` ·
`index-mismatch` · `scope-invalid` · `scope-missing` (only with `--strict`).

Warnings: `scope-missing` (documents not verified) · `skills-unchecked` (installed outside the
repo) · `no-steps` · `sipoc-empty` · `gap-undated` · `interview-role` · `layout-mixed` ·
`title-mismatch` · `owner-missing` · `document-search-capped`.

## Revisions and approval

- Edit the page, run `check`, then `revise <CODE> --change "<what>"`: a history row, the next
  letter (A → B → C), status En revisión/In review, the date and the index row are updated.
- **The operator approves, never the model.** Only after the operator says yes to that page:
  `revise <CODE> --change "<what>" --approve --by <role>`. Revision becomes `0`, status
  Aprobado/Approved. The script refuses `--approve` without `--by`, or while the page has errors.
- After `0`, every change is approved again by the operator: `1`, `2`… `revise` without
  `--approve` on an approved page is refused. Draft the change in `trabajo/` until the OK.

## What to load into context

The index plus the one process the task touches. Never the whole manual, never the interview record
or the logbook except to resolve one source. That is why the caps exist: a page over 800 words is
split into two processes, not loaded as is.

## Typical errors

| Symptom | Cause |
|---|---|
| `source-missing` | A step written from memory. Find where it came from, or move it to Gaps |
| `interview-missing` | The source date is the day the page was written, not the batch's date |
| `logbook-line-missing` | The line number was guessed. Open the logbook and count |
| `document-missing` | The file is outside `read`, or the scope is still empty |
| `status-revision` | Someone typed «Aprobado» by hand. Approval goes through `revise --approve` |
| `history-mismatch` | The frontmatter was edited without `revise` |
| `cap-words` | The process holds two processes. Split it |
| Many `SUPUESTO` | The interview is not finished. Ask before writing more |

## Files

`GUIDE.md` (the method for a person, with Ferretería Andes; Spanish in `GUIA.md`) · `templates/`
(index and process page in both languages, `alcance.yaml`, `scope.yaml`) · `tests/` (`sample/` +
`expected.json`) · `SOURCES.md`.
