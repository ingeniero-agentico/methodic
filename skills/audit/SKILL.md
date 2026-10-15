---
name: audit
description: "Use when the outputs of a method of this plugin (procurement, cost-and-pricing, economic-evaluation, financial-evaluation) must be checked before anyone relies on them (stage 4, after the executor agents finished), or when someone asks \"is this calculated right?\", \"can it be reproduced?\", \"audit the case\", \"¿está bien calculado?\", \"¿cuadra el VAN entre los dos métodos?\". Re-runs each method script with the same input in a temporary folder and compares every figure against the archived output (JSON and Excel), detects whether the script wrote into the case folder, and cross-checks values between chained methods (the project NPV that financial-evaluation read must equal the one economic-evaluation produced). Never fixes anything. Not for auditing a received document, code, security or folders, nor for recalculating with new data (call the method). Re-runs each method in a temporary folder and compares figure by figure against the archived output."
---

# Audit · re-run and compare

The mechanical half of stage 4. The judgment (assumptions, reliability, traceability, verdict) is
the `auditor` agent's; this skill only answers two questions without opinion: **does the archived
output come out the same if it is run again?** and **do two chained methods say the same number?**

```
python scripts/rerun.py run --script <method.py> --original <output.json> [--original <output.xlsx>] -- <args with {OUT}>
python scripts/rerun.py manifest <case>/context/runs/
python scripts/rerun.py value <file.json> <path>
python scripts/rerun.py cross <a.json> <path_a> <b.json> <path_b> [--tol-abs 1]
python scripts/rerun.py --test
```

Names before v1.1 still work: subcommands `correr`, `manifiesto`, `valor`, `cruzar`; flags
`--ignorar`, `--vigilar`, `--informe`, `--conservar`, `--probar`; the `{SALIDA}` marker; Spanish
manifest keys; and an old script path in a manifest (`skills/evaluacion-economica/scripts/evaluar.py`)
runs the renamed script (`skills/economic-evaluation/scripts/evaluate.py`).

## What `rerun.py` does

| Step | Rule |
|---|---|
| Temporary folder | `{OUT}` in the arguments is replaced by a new temporary folder. **Without `{OUT}` it does not run**: the output would go to the case folder and overwrite the archived one |
| Same input | The input is read from its original place (read-only); the relative paths it asks for (for example a project cash-flow file) keep resolving the same way |
| Compare JSON | Walks the whole tree: each number with a tolerance (`--tol-abs 0.01`, `--tol-rel 1e-9`), each text exactly, lists by position and length |
| Compare Excel | With openpyxl: every cell of every sheet, value and fill color (the yellow or orange that marks an assumption is compared too). `--ignore "SHEET!*"` skips cells, the same way `--ignore` skips JSON paths |
| Archived before v1.1 | Spanish JSON keys are read through `scripts/output_aliases.json` (see below) |
| Watch the case | Takes a snapshot (size and date) of the case folders before and after. If the script wrote there, it reports it as a change |
| If the script fails | Returns `FAIL` and its output **as it came** |
| Exit code | 0 = `SAME` · 1 = `DIFFERENT` (or something changed in the case) · 2 = `FAIL` or `MISSING` |

Paths inside a JSON: `indicators.npv`, `rows[0].value`, `alternatives["Leasing 36 payments"].cae`.

## The manifest of a run (contract with the `executor` agent)

Each executor run leaves `<case>/context/runs/<id>.json` (`ejecuciones/` in a context written
before v1.1). It is what makes re-running possible without guessing the command:

```json
{
  "id": "economic-evaluation-base",
  "method": "economic-evaluation",
  "date": "DD-MM-YYYY",
  "script": "skills/economic-evaluation/scripts/evaluate.py",
  "args": ["<absolute path>/input.json", "--profile", "<company>", "--out", "{OUT}"],
  "out_dir": "<absolute path of the case>",
  "outputs": ["<case>/output.json", "<case>/output.xlsx"],
  "decisive_figure": {"name": "NPV", "file": "<case>/output.json", "path": "indicators.npv", "value": 0},
  "assumptions": [{"field": "revenues[0].occupancy", "value": 0.5, "origin": "ASSUMPTION", "reason": "…",
                   "reliability": null}],
  "tol_abs": 0.01
}
```

`script` is relative to the repo root. `args` carries `{OUT}` where the output folder (or file)
goes: the executor replaces it with `out_dir` when it runs; `rerun.py manifest` replaces it with
the temporary folder and also checks that `decisive_figure.value` is what the output says. In
`assumptions`, `origin` is `person` · `profile` · `document` · `research <reliability>` ·
`ASSUMPTION`, and `reliability` is the `data[].reliability` of `research-data.json` when the value
came from the research (one format: see "The format" in `skills/research/SKILL.md`).

## Where the decisive figure of each method is

| Method | File | Path |
|---|---|---|
| procurement | `<output>.json` (next to the Excel) | `totals.net`, `missing` |
| cost-and-pricing | the one of `--json` (without `--json` there is no JSON: always pass it) | `totals.sales_total`, `totals.overall_margin` |
| economic-evaluation | the input's name with `input` → `output` (`entrada` → `salida`) | `indicators.npv`, `sensitivity.rows[0].critical` |
| financial-evaluation | `<case>-result.json` (`<case>-resultado.json` with `language: es`) | `winner`, `pv_difference`, `project_npv` |

The exact key names are in each method's `SKILL.md` («How to read the output»); if they differ from
this table, the method's `SKILL.md` prevails.

**An output archived before v1.1** keeps its Spanish JSON keys (`indicadores.van`, `ganadora`…),
while a re-run writes English keys. `rerun.py` detects it and reads it through
`scripts/output_aliases.json` (derived by running the new scripts on old inputs and pairing the
outputs): key names, paths written as text (`ingresos[0].ocupacion`) and enum words (`lineal`) are
translated; every number and every other text is still compared exactly. Fields a re-run carries
that the old format never had are listed as "added since v1.1" and not compared. The Excel compares
directly (with the profile's `language: es`, the default, its labels are the same). The line
`archived before v1.1: N Spanish keys…` says it happened; write in the audit that the output
predates v1.1.

What the aliases do **not** hide: in v1.1 `economic-evaluation` and `financial-evaluation` record
more assumptions (a value without a source is now marked; the assumptions of the chained project
flow are carried over; a tax-regime mismatch is warned). An output archived before v1.1 therefore
comes out `DIFFERENT` in `assumptions` and in the `SUPUESTOS` sheet only. To check that the
figures still reproduce, re-run with `--ignore "assumptions*" --ignore "parameters.tax_losses.*"
--ignore "SUPUESTOS!*"`, and report the assumption differences as what they are: the old output
marked fewer assumptions.

## Cross-checks between chained methods

| Chain | Must match |
|---|---|
| economic-evaluation → financial-evaluation | `indicators.npv` = `project_npv`; `parameters.rate.value` = `discount_rate`; `parameters.tax.value` = `income_tax`; `parameters.horizon.value` = `horizon_years`; amount, useful life and salvage value of the asset in both inputs |
| procurement → cost-and-pricing | what was assigned to each supplier (quantity, unit, unit price, currency and exchange rate) = the purchase lines of cost-and-pricing |

A cross-check that does not match is not an error if the difference is declared in the output (for
example, a scenario with another tax rate that says so). If only a separate summary declares it,
it is a finding.

## Typical errors

| Symptom | Cause |
|---|---|
| `MISSING · no argument carries {OUT}` | `--out "{OUT}"` (or `{OUT}/file.xlsx`) is missing. It is on purpose |
| `DIFFERENT` only in the sweeps or in the `SENSITIVITY` sheet | The archived output was run with other `--sweep` values: the command was not recorded |
| `DIFFERENT` in many JSON keys (`<missing>` on both sides) | A Spanish key of an archived pre-v1.1 output is not in `scripts/output_aliases.json`: add it there (derive it by running the new script on the old input), never by editing the output |
| `DIFFERENT` only in `assumptions` and the `SUPUESTOS` sheet of an evaluation | The output predates v1.1, which marks more assumptions: see above |
| `NOT GENERATED` | The name the script leaves is not the archived one (`--original path=new_name`) |
| `NOT COMPARED` on an `.xlsx` | openpyxl is missing; the JSON is compared anyway |
