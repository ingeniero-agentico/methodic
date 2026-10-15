---
name: map-context
description: "Use when a task comes with folders or files nobody has read yet, to map them before reading (what files exist, where, from when, what each one says in one line and what links to what) and to decide whether this is a first run or a reread (stage 0 of ingeniero-agentico). Also when someone comes back to a topic already worked and asks what changed (\"I'm back after two weeks, what changed?\", \"volví al tema, ¿qué cambió en la carpeta?\", \"¿qué hay de nuevo desde la última vez?\"), when a folder is too large to read file by file, or when the orchestrator needs context/MAP.md. Runs a deterministic script with no LLM; the mode comes from comparing file fingerprints, never from judgment. Picks a core of up to 3 files that are always read. Not for finding external data or current figures (research), nor for geographic maps, mind maps or auditing how folders are published. Maps the task's folders without an LLM and says what changed since the last run."
---

# Map context · stage 0

**The saving of a reread is reading the map instead of the folders.** This skill leaves that map,
cheap and always the same for the same input, and decides the mode by comparing fingerprints
(size, date and sha1 of each file). The model does not choose the mode "by eye".

The script does everything: it walks, summarizes each file in one line without an LLM, extracts
the links, compares with the previous run and writes the files. The agent only chooses which
folders, completes what the script left empty and names the gaps.

```bash
python scripts/map_context.py <folder> [<folder> ...] --out <context/> [--exclude PATTERN] [--threshold 0.20] [--core path1,path2] [--graphify]
python scripts/map_context.py --out <context/> --mark-read   # orchestrate calls it when consolidating
python scripts/map_context.py --test      # the sample case has to end in OK
```

The last line it prints is the one to read:

```
MODE: reread · changed 1 · map 454 words
```

Flags before v1.1 still work as hidden aliases (`--salida`, `--excluir`, `--umbral`, `--nucleo`,
`--marcar-leido`, `--probar`).

## When to use it

- A task arrives with one or more folders and nobody has read them yet (`first-run`).
- A topic already worked is reopened: the map says what changed and rereading that is enough (`reread`).
- The folder is large and reading it whole costs more than it is worth.

## Where `context/` goes

Next to the task's data, **never in the public repo** (`ARCHITECTURE.md`):
`<data>/cases/<case>/context/`, or `<task folder>/context/` if there is no data folder.
If the task folder is read-only, the output goes to `<data>/cases/<case>/context/`.
If `context/` ends up inside the mapped folder, the script excludes it by itself.

**A context written before v1.1** (`contexto/` with `MAPA.md`, `grafo.json`, `huellas.json`,
`cambios.json` and Spanish keys) is read as it is and keeps its file names: the script detects
the layout, so a reread on an old context still finds 0 changes. A new context gets the English
names.

## What the script computes

| Step | Rule |
|---|---|
| Walk | Every folder given. Excludes `.git`, `node_modules`, `__pycache__`, `.venv`, `.obsidian`, `graphify-out` and the like, system files (`~$…`, `desktop.ini`), binaries over `--max-mb` (25 MB), whatever matches `--exclude` and the output folder. Does not follow links or junctions |
| Summary | No LLM. `.md`: title · status fields (`Status`, `Purpose`, `Replaces`, `Client` and their Spanish forms `Estado`, `Para qué`, `Reemplaza a`, `Cliente`) · frontmatter `description` or first sentence · `##` sections. `.json`/`.yaml`: top-level keys. `.py`: docstring or first comment. `.xlsx`: sheets with their size and the first row (openpyxl). `.pdf`: title or first line and pages (pypdf). `.docx`: title and first paragraph. Images: dimensions. Everything else: the name only |
| Links | `[[wikilinks]]`, markdown links to local files, paths cited in the text that exist (in backticks or bare) and the frontmatter `skill:`/`skills:`. A link enters only if the target exists; a skill not in the folders stays as an external node `skill:<name>` |
| Fingerprints | Per file: size, date (ns) and a 12-character sha1. If size and date did not change, the previous sha1 and summary are reused without opening the file again |
| Changes | Each run compares against the previous one and, if something changed, records the difference with its date in `changes.json`. What is recorded **accumulates** until `--mark-read`: running twice does not erase what is pending. Net: new and then changed stays new; new and then deleted disappears |
| Mode | Computed against the **accumulated unread** changes. No previous fingerprints, no map, or other roots: `first-run`. A `first-run` stays one until it is marked read. Otherwise: accumulated files ÷ files of the base (the one of the last `--mark-read`). Up to `--threshold` (20%): `reread` with the list; above: `first-run`. A file whose date changed but whose sha1 did not **does not count as changed** |
| Core | Up to 3 files that are always read, by a fixed rule: 1) those of `--core`; 2) key names `LEEME`/`README`, `TRABAJO`/`JOB`, `CLAUDE`, `INDICE`/`INDEX` (shallowest first, in that order); 3) the most linked, without images, archives or CAD; tie: the most recent. **A file that another one declares replaced** (`**Replaces:** <file>`, `**Reemplaza a:** <file>`, a table row with that field, or a `replaces:` frontmatter key) never enters by rule; the map lists it as "left out". A `--core` path that is not in the map aborts |
| Cap | `MAP.md` ≤ 3,000 words (`--max-words`). If it goes over, it compresses by levels: shorter summaries, the most relevant files of each folder ("+N more"), grouped folders, and as a last resort it cuts with a notice |

Relevance of a file (decides who stays when compressing): inbound links × 3 + outbound, plus
more if it is a document, if it is called `README`, `LEEME`, `SKILL`, `CLAUDE`, `INDEX`, `RESULT`
or similar, and if it changed in the last 30 days of the set.

## What the agent decides

1. **Which folders.** The task's, not the root of the disk. Several folders go in the same call
   (each keeps its name as a prefix).
2. **What else to exclude.** Generated outputs, backups, folders of another topic: `--exclude`.
   **What to pin in the core.** If the rule leaves out a central file, `--core` fixes it. It is
   passed on every run: it is not saved.
3. **Complete summaries.** The map carries "No summary (N)" ordered by relevance. Open at most
   **10** of those, only the ones that matter for the task, and write their line in the answer
   (the script is not edited by hand).
4. **Name the gaps.** What the task needs and the map does not show: a document that is cited
   and missing, a quote that is missing, a datum without a source. That feeds stage 1.

## How to read the output

| File | For whom | What it carries |
|---|---|---|
| `MAP.md` | the orchestrator and the person | the MODE on top, "Core · always read" (with the replaced files left out), "To reread" (in a reread, with the date since which it accumulates), folders, one line per file, most recent, most linked, orphans and no summary |
| `graph.json` | scripts and graphify | `nodes` (`id`, `label`, `type`, `file_type`, `source_file`, `summary`, degrees, `replaced_by`) and `links` (`source`, `target`, `relation`, `confidence`). `graph.core`, `graph.replaced`, `graph.changes` (everything accumulated) and `graph.changes_this_run` |
| `fingerprints.json` | the next run | the state of each file in the last run |
| `changes.json` | the next run and `orchestrate` | the base (files at the last `--mark-read`), whether a first run is pending, and the unread runs with their date |

**Reread = core + "To reread" + the map.** Nothing else.

Relations: `wikilink`, `link` and `uses_skill` are `EXTRACTED` (the file says it); `mention` is
`INFERRED` (a path in the text that matches a file).

**What is pending is emptied by whoever reads, not by whoever maps.** `orchestrate` runs
`--mark-read` when consolidating, once what changed has been read. Until then, each run adds to
the list.

## graphify (optional)

With `--graphify`, if it is installed, the map adds how to enrich it with `/graphify` (it extracts
concepts with a model; the script does **not** call it). `graph.json` has the same shape as
`graphify-out/graph.json` and `graphify merge-graphs` joins them.

## Typical errors

| Symptom | Cause |
|---|---|
| It always says `first-run` | Nobody ran `--mark-read` after the first run; or the output changes folder between runs; or the roots are passed in another order |
| "To reread" lists files already read | `--mark-read` was skipped when consolidating |
| The core carries the wrong file | The replaced file does not say «Replaces:» (or says it in a way the script cannot resolve to a file): pin the right one with `--core` |
| `reread` with many changes expected | The threshold is high for that task: lower `--threshold` |
| An edited file does not appear in "To reread" | It was saved without changing the content (same sha1): that is correct |
| The map fills up with generated files | `--exclude` is missing (for example `--exclude "output*"`) |
| A PDF comes out only as "N pages" | It has no title nor text on the first page (a scan): open it by hand if it is key |
| A path over 260 characters | The script uses the `\\?\` prefix on Windows; if it is still missing, check permissions |
| Two maps in one folder (`MAP.md` and `MAPA.md`) | The folder was copied by hand between layouts; the script writes the layout it finds (`fingerprints.json` first, then `huellas.json`) |
