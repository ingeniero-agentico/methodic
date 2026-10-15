---
name: economic-evaluation
description: Use when someone must decide whether a project or investment is worth doing on its own merits, regardless of how it is financed (buying a vehicle or machine to rent it out, a new business line, replacing equipment, expanding capacity). Builds the pure project cash flow with tax, depreciation, working capital and salvage value; computes NPV, IRR (with multiple-IRR handling when flows change sign more than once), payback, NPV index and a sensitivity with the critical value that makes NPV zero. Use it even for a quick NPV or IRR of given flows, or when a computed IRR looks wrong: the script gives the traceable figure. Triggers: "is it worth buying...?", "evaluate this project", "compute NPV and IRR", "the IRR came out weird", "what occupancy pays for it?", "¿me conviene comprar...?", "calcula el VAN y la TIR", "¿con qué ocupación se paga?". Not for how to pay for it (financial-evaluation), nor for the monthly break-even of a service with no investment (cost-and-pricing).
---

# Economic evaluation · is the project worth doing?

Evaluates the **pure project**: whether the business is worth doing by itself, as if it were paid
in full with the owner's money. How to finance it (loan, leasing, equity cash flow) is another
method: `financial-evaluation`, which starts from the flow produced here.

## When

- Buying an asset to produce or rent out (vehicle, machine, premises).
- Opening a business line, expanding capacity, replacing equipment.
- Any "is it worth it?" or "how much must it sell to pay for itself?" question.

## What the agent decides (the script does not)

1. **What goes into the flow.** Only what is **incremental**: what changes if the project is done.
   A cost the company pays anyway (the owner's salary, the office) stays out. Revenue taken from
   another product of the same company is subtracted.
2. **Net or gross of VAT.** If the company recovers the input VAT, everything goes net. If it does
   not (exempt activity, a vehicle without the right to the credit), the VAT on the purchase is part
   of the investment. Say it in the input `note`: the script copies the note to the assumptions
   sheet, marked, so it cannot hide there.
3. **Revenues.** `price` per unit and `quantity`, or `capacity` × `occupancy` when what drives the
   result is how much the asset is used (days rented, machine hours). With `occupancy`, the
   sensitivity gives the **critical occupancy** directly.
4. **Costs.** Variable (per unit of a revenue, field `per_unit_of`) and fixed (per year). What the
   client pays apart (fuel, tolls) is not a project cost.
5. **Investments.** Amount, year, tax useful life (the table of the country's tax authority),
   salvage value. A reinvestment halfway is another investment with its own `year`.
6. **Working capital.** What must be in cash before collecting (insurance, permits, inventory,
   collection lag). Recovered at the end unless `"recovered": false`.
7. **Tax losses.** `carry_forward` (stand-alone project: the loss reduces future profits of the
   same project) or `offset` (the company has other profits and the loss saves tax that year).
   Default `carry_forward`, the conservative one. It is a claim about the company, so a plain value
   comes out marked **ASSUMPTION**; to present it as data give
   `{"value": "offset", "assumption": false, "source": "..."}`.
8. **What is an assumption.** Every number that did not come from the user or a document carries
   `"assumption"` (`true` for the whole item, or the list of fields) and its reasoning in `source`.
   The output highlights them. Never invent a number without marking it.
9. **Rate and tax.** They come from the profile. If the profile lacks them, the script requires
   `--rate` or `--tax` and marks them as assumptions; the agent says where the proposed value came
   from.

## What the script computes

`scripts/evaluate.py` (Python 3.11+, standard library + openpyxl):

- **Pure project cash flow**, year 0 to N: revenue − variable costs − fixed costs − depreciation +
  sale of assets − book value = profit before tax; − tax (profile rate) = net profit; +
  depreciation + book value (not cash outflows) − investments − working capital + its recovery =
  flow.
- **Market salvage value** (`salvage_method: market`): assets are sold at the end at
  `salvage_value`; the gain over book value pays tax and a loss reduces it. With `book` they are
  sold at book value (no tax effect).
- **Indicators**: NPV, IRR (every root between −95 % and 1,000 %; warning if the flow changes sign
  more than once), simple and discounted payback (interpolated within the year), NPV index = NPV ÷
  investment in present value.
- **Sensitivity**: each variable ±`--delta` (10 % by default) with the rest fixed, sorted from the
  one that moves NPV most to the least, and the **critical value** of each (the one that makes NPV
  zero, by bisection). The critical value of the rate is the IRR. `--sweep` walks one variable
  through given values.

```
python scripts/evaluate.py <input.json> [--profile <name|path>] [--rate 0.12] [--tax 0.27]
                           [--delta 0.10] [--sweep "revenues[0].occupancy=0.3,0.5,0.7"]
                           [--out <folder>]
python scripts/evaluate.py --test
```

The Spanish flags (`--perfil --tasa --impuesto --barrer --salida --probar`) still work, and so do
Spanish input keys (`ingresos`, `costos_fijos`, `supuesto`...) and Spanish sweep keys
(`ingresos[0].ocupacion`).

The profile is found in this order: `--profile` (name or path) · `$INGENIERO_DATOS` ·
`../ingeniero-agentico-datos` (in `profiles/`, then `perfiles/`; used if there is only one) · the
repo template `profiles/_template.yaml` (fallback `perfiles/_plantilla.yaml`). The empty input is
`templates/input.json`.

## Output language

The profile field `language` (`es` by default, `en`) sets the sheet names, labels, the marker
(`SUPUESTO` or `ASSUMPTION`) and the console text. JSON keys are always English. With `es` the
workbook is the same as before the translation.

| es | en |
|---|---|
| SUPUESTOS · FLUJO · INDICADORES · SENSIBILIDAD | ASSUMPTIONS · CASH FLOW · INDICATORS · SENSITIVITY |

## How to read the output

`<input>` named `input*.json` writes `output*.xlsx` and `output*.json`; one named `entrada*.json`
writes `salida*.*`; any other name adds `-salida` (es) or `-output` (en).

| Sheet | What it has |
|---|---|
| ASSUMPTIONS | each parameter with its value, origin (profile, argument, input field and source) and mark; the input note, marked |
| CASH FLOW | the flow line by line, year by year, with the "Origin" column |
| INDICATORS | decision, NPV, IRR, sign changes, payback, NPV index and the warnings |
| SENSITIVITY | tornado (±x %) and critical value of each variable; the sweeps requested |

The JSON carries the same: `parameters`, `assumptions` (the common format of every method:
`[{parameter, value, origin, text}]`, only what is marked, `origin` one of `input` · `profile` ·
`template` · `default` · `script` · `research:<id>`; an item with `"research": "D05"` gets
`research:D05`), `traceability` (the whole ASSUMPTIONS sheet, data rows included), `cash_flow`
(`years`, `rows`, `net_cash_flow`, `assets`), `indicators`, `sensitivity`, `sweeps`.
`financial-evaluation` reads `cash_flow`, the tax regime (`parameters.tax`,
`parameters.depreciation`) and `assumptions`.

The decision is the **NPV**: ≥ 0 is worth it at the required rate. The IRR goes along; with several
sign changes it is not used. What the person is told is the NPV, the critical value of the
variable that weighs most (e.g. "it pays for itself if rented more than 170 days a year", from the sample case) and how
much room there is between the assumed value and the critical one.

## Country notes

- **Chile (`country: CL`).** Useful lives come from the SII table (normal and accelerated, in
  `useful_life` and `accelerated_life`); amounts usually go net of IVA when the company recovers it;
  money in today's pesos means a real rate. See `SOURCES.md`.
- Any other country: the same method with that country's tax rate (profile), its depreciation
  table and its VAT rule. Nothing in the script is Chilean except the default labels.

## Typical mistakes

- **Bringing in the financing.** Loan interest and installments do not go here: they go in
  `financial-evaluation`, on top of this flow.
- **Forgetting to add depreciation back.** It is subtracted to compute tax and added back because
  it does not leave the cash box.
- **Salvage value without tax.** Selling above book value pays tax; the script does it.
- **Nominal rate with today's money.** If amounts carry no inflation, the rate is real.
- **New asset occupancy = current fleet occupancy.** What counts is the **additional** demand lost
  today for lack of the unit, not the average of the ones already there.
- **Costs paid anyway.** A salary or a rent that does not change is not part of the project.
- **Deciding with the IRR when the flow changes sign several times.** There may be several.

## Test

`python scripts/evaluate.py --test` runs `tests/sample-case.json` (Transportes del Valle, a van
for daily rental) against `tests/expected.json`, checked by an independent path, plus a run with
Spanish keys and one with `language: en`, and ends in `OK` or `FAIL`.
