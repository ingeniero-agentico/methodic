# Map context · step-by-step guide

The same method as `SKILL.md`, for a person. It walks through the sample case in
`tests/sample-case.json`: the folder of a purchasing task of **Ferretería Andes** (fictitious) for
**Constructora Sur** (fictitious), with notes, data, a script and a skill. A Spanish version lives
in `GUIA.md`.

## 0 · What it is for

Before researching or calculating you need to know what is there. Reading a folder file by file is
the most expensive part of the work; the map does it once and, when you come back to the topic,
says what changed. If almost nothing changed, you read the map and those few files: that is the
**reread**.

## 1 · Choose the folders and the output

- **Folders:** the task's. In the case, `task/`.
- **Output:** a `context/` folder next to the task's data. Never inside a public repo, and never
  inside a folder that cannot be touched (in that case it goes to `<data>/cases/<case>/context/`).

## 2 · Run the first time

```bash
python scripts/map_context.py task --out task/context
```

What happens in the case (`--test` checks it against `tests/expected.json`):

- **9 files** (10 if openpyxl is installed and the test adds `data/sheet.xlsx`). `.git/` and
  `node_modules/` do not enter.
- **8 links:** `README.md` → `purchasing/notes.md` by wikilink; `README.md` → `data/profile.yaml`
  by markdown link; `purchasing/notes.md` cites `scripts/calculation.py` and `data/summary.json`
  in the text; `skills/buy/SKILL.md` cites `purchasing/notes.md`; `agents/buyer.md` uses the skill
  `buy` (which is in the folder) and the skill `quote` (which is not: it stays as an external node).
- **Core:** `README.md` and `JOB.md` (key names, at the root) and `purchasing/notes.md` (the most
  linked: 2 inbound).
- **Summaries without an LLM:** `scripts/calculation.py` → its docstring; `data/profile.yaml` →
  "keys: company, currency, vat"; `JOB.md` → "Fictitious job · status: open · client:
  Constructora Sur · Pipes are bought for a water network. · sections: What was asked; What is
  missing".
- **Orphans:** `orphan.txt` and `JOB.md` (nobody cites them and they cite nobody).
- The final line says `MODE: first-run`.

## 3 · Read `MAP.md`

In this order:

1. **The MODE** (line 3). On a first run, everything is new.
2. **Core · always read:** the three files through which you enter the topic. If a file declares
   that it replaces another («**Replaces:** `LIST-001.md`»), the replaced one is left out and the
   map says so. If the rule still chose badly, run again with `--core`.
3. **Folders:** how many files, of what kind and from when.
4. **Files:** one line per file: name, size, date, summary.
5. **Most linked:** where to keep reading.
6. **Orphans:** what nobody cites (either it is left over, or a link is missing).
7. **No summary:** what the script could not read. Open by hand only those that matter (10 at
   most).

## 4 · Mark read

When the topic has been read and the task closed, empty what is pending:

```bash
python scripts/map_context.py --out task/context --mark-read
```

Until that happens, **the first run stays a first run** even if the map is run again: nobody has
read it. After marking, the base is the 10 files of that moment.

## 5 · Come back to the topic

`purchasing/notes.md` is edited (a fourth quote arrived) and the map runs the same way:

```bash
python scripts/map_context.py task --out task/context
```

1 of 10 files changed (10%, under the 20% threshold): **`MODE: reread`**, and "To reread" lists
exactly `purchasing/notes.md`. You read the core, that file and the map; nothing else.

**What was not read accumulates.** If it runs again without marking read, `purchasing/notes.md`
stays in "To reread". If `scripts/calculation.py` also changes, the list carries both and
`changes.json` keeps the two runs with their date. Only `--mark-read` brings it to 0.

If instead three files are touched and `orphan.txt` is deleted, 4 of 10 change (40%) and it goes
back to `first-run`: the topic changed enough to reread it whole.

(The figures are the ones `--test` prints with openpyxl installed; without the sheet there are 9
files.)

## 6 · Large tree

With 1,200 notes in 40 folders, the full map would go over 3,000 words. The script compresses: it
shortens summaries, keeps the most relevant files of each folder and summarizes the rest ("+N more:
12 markdown"). The test requires it to stay under the cap.

## 7 · A replaced file

A job folder often keeps an old list next to the current one. The test builds one: `LIST-001.md`
is the most linked file (four notes cite it), and `LIST-002.md` says «**Replaces:** `LIST-001.md`».
Without the rule, the old list would enter the core; with it, the core is `README.md`,
`LIST-002.md` and the next most linked file, and the map lists `LIST-001.md` as "left out". The
Spanish form («Reemplaza a», also in a table row and with a bare name such as `LISTADO-001`) works
the same.

## 8 · A context from before v1.1

A `contexto/` folder written by the Spanish version (`MAPA.md`, `huellas.json`, `cambios.json`,
Spanish keys) is read as it is: the next run finds 0 changes if nothing changed, and keeps writing
the same file names, so no duplicate map appears.

## Errors the method catches

| Error | Where it is caught |
|---|---|
| Reading everything again for no reason | the mode comes from the fingerprints, not from the model's judgment |
| Losing a change because the map ran twice | what was not read accumulates until `--mark-read` |
| Rereading only what changed and losing the thread | the core is always read |
| Reading an old list as if it were current | a file declared replaced never enters the core by rule |
| Believing something changed because its date changed | the sha1 is compared, not the date |
| A map so long nobody reads it | a 3,000-word cap with compression by relevance |
| Mapping its own outputs | the `context/` folder excludes itself |
| A link to a file that does not exist | a link enters only if the target exists |
