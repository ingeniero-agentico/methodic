# Interview · step-by-step guide

The same method as `SKILL.md`, for a person. It walks the fictitious case in `tests/`: **Ferretería
Andes**, a hardware shop with about fifteen people, is about to start working with methodic. Nobody
has written down how the shop works. The interview finds out by asking, in short batches, and keeps
a dated record that the manual will cite.

**What the interview does and what it does not.** It asks and writes down the answers. It does not
write the manual pages (the `manual` skill does) and it does not open or change any file on the
computer (the `intervene` skill does, later, inside the limits agreed in round 3).

## 0 · The profile and the data folder

The record lives outside the repo, in the operator's data folder:

```
C:/Users/usuario/methodic-data/
├── profiles/ferreteria-andes.yaml      ← company = the file name without .yaml
└── manual/ferreteria-andes/entrevista/ ← created by the first record
```

Copy `profiles/_template.yaml` to `profiles/ferreteria-andes.yaml` and fill at least `language`
(`es` or `en`) and `company.name`. The script finds the data folder in this order: `--data`,
`METHODIC_DATA`, `INGENIERO_DATOS`, `../methodic-data/`, `../ingeniero-agentico-datos/`.

## 1 · Ask for the first batch

```bash
python scripts/interview.py next
```

```
Ferretería Andes · Tanda 1 · El negocio
[neg-01] ¿Qué vende principalmente la empresa? (varias)
   1) Productos que compra y revende · 2) Productos que fabrica o arma · 3) Servicios u obras · 4) No sé · u otra respuesta
[neg-02] ¿En qué tipo de negocio está?
   ...
```

Four questions, each with options and always «No sé». The agent asks them as they are (with the
AskUserQuestion tool where it exists, or this same list in text). It does not reword them: the record
must match the bank.

## 2 · Record the answers

The owner answers. The agent writes the answers by question id and records them at once:

```json
{"round": 1, "who": "dueña", "answers": [
  {"id": "neg-01", "answer": ["Productos que compra y revende"]},
  {"id": "neg-02", "answer": "Comercio (tienda o distribuidora)"},
  {"id": "neg-03", "answer": ["Personas (público general)", "Empresas"]},
  {"id": "neg-04", "answer": ["Al contado al entregar", "Con factura a 30 o 60 días"]}]}
```

```bash
python scripts/interview.py record --answers batch-1.json
```

`who` is a role (`dueña`, `vendedor`, `bodega`), never a person's name in the repo.

## 3 · «No sé» is an answer

The second batch is answered by the salesperson. He does not know how prices are set:

```bash
python scripts/interview.py record --answers batch-2.json --who vendedor
```

Today's file `entrevista/2026-10-16.md` now holds two blocks (the date is the day it was recorded):

```markdown
## Tanda 2 · El negocio · 16-10-2026 15:20
Respondió: vendedor

1. [neg-05] ¿Cómo se fija el precio de lo que vende? → No sé · HUECO
2. [neg-06] ¿Cuántas personas trabajan en la empresa contando al dueño? → 6 a 20
3. [neg-07] ¿Quién decide lo importante (precios, compras grandes, contrataciones)? → El dueño o la dueña
4. [neg-08] ¿Qué procesos le quitan más tiempo o le dan más problemas hoy? (si son otros, escríbalos separados por coma) → Compras, Cobranza
```

The gap is not a failure: it says what is missing and since when. When the owner is available,
`next --gaps` asks it again; the new answer closes the gap. The file is only appended to: an earlier
block is never edited.

## 4 · Where we are

```bash
python scripts/interview.py status
```

```
Ferretería Andes · entrevista · 2 tanda(s) · última 16-10-2026 15:20
Ronda 1 · El negocio: 8/10 (1 no aplica)
Ronda 2 · El proceso:
   COMPRAS (Compras) · duele: 0/12
   COBRANZA (Cobranza) · duele: 0/12
Ronda 3 · Los límites: 0/8
Huecos abiertos (1):
   - neg-05 · ¿Cómo se fija el precio de lo que vende? · declarado el 16-10-2026
Siguiente: Ronda 1 · neg-10, neg-11
```

«1 no aplica» is `neg-09` (up to what amount a head decides): the owner decides everything, so it is
not asked. The answer «Compras, Cobranza» named two processes that hurt, and they get codes.

## 5 · Round 2, once per process

When round 1 is done, `next` moves to `COMPRAS`: what starts it, how often, the steps in order, who
does each one, with which tool, where its files live, where someone decides and who approves, what it
delivers and to whom, what usually fails and who answers for it. Then the same for `COBRANZA`. Each
block carries the code: `## Tanda 4 · El proceso · COMPRAS · …`.

To jump: `next --round 2 --process COBRANZA`.

## 6 · Round 3, the limits

The last round settles what methodic may do on the computer: which folders it may read (paths
written out, like `C:/Users/usuario/Documents/FerreteriaAndes`), where it may change a file (always
with a backup and an OK each time), what is never touched (payroll, banks), which data are sensitive,
who gives the OK, whether there is a backup, and who sends or pays what gets prepared (methodic
prepares; a person sends).

The owner prefers to fill this round alone, at once:

```bash
python scripts/interview.py form --round 3 > limites.md
# she ticks [x] and writes paths in «Otra respuesta», then:
python scripts/interview.py record --form limites.md
```

Same questions, same ids, one block in the record.

## 7 · Hand over to the manual

When `status` says nothing is left to ask, the `manual` skill reads `status --json` and writes
`NEGOCIO.md`, one page per process and `alcance.yaml`. Each step cites its answer
(`entrevista · dueña · 16-10-2026`), each gap goes to `Huecos` with its date, and whatever nobody
answered is marked `SUPUESTO`.

## Errors the method stops

| Error | Where it is stopped |
|---|---|
| The agent fills in what "a shop usually does" | only recorded answers count; the rest is `SUPUESTO` in the manual |
| A question nobody could answer gets lost | it stays as a dated gap in `status` and in the index |
| Twenty questions in one message | batches of at most 4; `record` refuses more |
| A reworded question loses its earlier answers | each record line carries the question id |
| An earlier answer quietly overwritten | the file is append only; a new answer is a new block |
| A process step with no source | every answer carries who gave it and when |
