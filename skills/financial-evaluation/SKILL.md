---
name: financial-evaluation
description: Use when an asset or project is already worth doing (or will be done anyway) and the question is how to pay for it: cash, a bank loan (French or German amortization, effective annual cost such as Chile's CAE), financial leasing (installments, purchase option, tax effect) or renting instead of buying, and how much each option changes the owner's after-tax result. Builds the equity (investor) cash flow with the interest tax shield, investor NPV, after-tax effective cost per alternative and the discount rate at which the decision flips; reads the pure project flow from economic-evaluation or a year/flow CSV. Triggers: "cash, loan or leasing?", "build the amortization table", "what does this loan really cost?", "rent or buy?", "¿contado, crédito o leasing?", "¿arriendo o compro?", "¿cuál es la CAE?". Not for whether the project itself is worth doing (economic-evaluation), nor for personal finance advice.
---

# financial-evaluation

Answers **how to pay for** an asset and how much it changes for the owner. It does not answer
whether the project is worth doing: that is `economic-evaluation`, and its pure project flow is
this method's input.

It is a calculation method, not personalized financial advice.

## When

- The project is already worth it (or will be done anyway) and the choice is between paying cash,
  taking a loan, a leasing or renting.
- A loan or leasing quote arrived and you need its real cost (CAE, implicit rate, after-tax cost).
- Someone asks for the amortization table, the investor cash flow or the investor NPV.

## What the agent decides (the judgment)

1. **Which alternatives to compare.** Only those the company can really take. If it does not have
   the money, cash stays as a reference, not an option; say so in the output.
2. **That they are the same asset.** Normalize before comparing: same net price, same period of
   use, same sale value at the end. What changes between offers (a bonus for financing with the
   brand, a rent that includes maintenance) goes into the case: the alternative's own price in
   `net_price` and the rest in `non_comparable_notes`, which the output declares, not averages.
3. **Which discount rate.** The profile's (`finance.discount_rate`): the opportunity cost of the
   owner's money. If the profile lacks it, the script requires `--rate` and marks it as an
   assumption. A small company does not need CAPM: what its money earns in its best real
   alternative is enough (a deposit, paying off another debt, another project). WACC and CAPM are
   in the GUIDE as reference.
4. **Which tax.** `company.income_tax` in the profile or `--tax`. If the regime is unclear, run the
   sensitivity with the possible rates (`sensitivity.tax_rates` in the case) and say which one
   changes the decision.
5. **Find the missing data** (price, loan rate, leasing terms): with the source (URL and date) in
   `source`; if it cannot be found, `"assumption": true`. A datum from the research stage carries
   `"research": "<id>"` and its origin comes out as `research:<id>`.

## What the script computes

`scripts/financial_evaluation.py` (Python 3.11+, standard library + openpyxl):

- **Amortization table** per alternative: loan with French (fixed installment) or German (fixed
  principal) amortization, leasing with initial installment and purchase option. Installments and
  interest rounded to the currency unit; the last installment absorbs the rounding.
- **Effective annual cost of the loan** (monthly IRR × 12 of what reaches the borrower against what
  is paid, with fees and loan tax; in Chile this is the CAE) and the **implicit rate** of the
  leasing (or it solves it when the installment is given).
- **Asset flow** month by month and after tax: payments, tax saving on interest and financial
  costs, on depreciation, on leasing installments or on rent (at each year's close), and residual
  value net of the tax on the sale.
- **After-tax present value cost** of each alternative; the lowest wins.
- **After-tax effective annual cost**: IRR of (alternative − cash). If it is below the discount
  rate, financing that way beats paying cash.
- **Investor flow and NPV**: project flow + (asset flow with the alternative − asset flow in
  cash). So the purchase is not counted twice; with cash, investor NPV = project NPV.
- **Indifference rate** between the winner and the runner-up, and tax × rate sensitivity.
- **Tax regime check**: when the project flow is an economic-evaluation output, its tax rate and
  depreciation are compared with the financing's; if they differ, `warnings` and
  `project_flow_regime.matches = false` say the investor NPV mixes two regimes (decide by the PV
  cost). A CSV does not state its regime, so that is listed as an assumption.

```
python scripts/financial_evaluation.py --case case.json [--project flow.csv|output.json]
       [--profile company] [--rate 0.12] [--tax 0.25] [--out folder]
python scripts/financial_evaluation.py --test
```

The Spanish flags (`--caso --proyecto --perfil --tasa --impuesto --salida --probar`) still work,
and so do Spanish case keys (`activo`, `alternativas`, `valor`, `supuesto`...) and codes
(`credito`, `francesa`, `una_cuota`, `instantanea`).

The profile is found in this order: path given in `--profile` (or the case `profile` field) ·
`$INGENIERO_DATOS/profiles/<company>.yaml` (then `perfiles/`) · `../ingeniero-agentico-datos/`
(same two folders) · the repo template `profiles/_template.yaml` (fallback
`perfiles/_plantilla.yaml`), and then everything comes out as an assumption.

The project flow is a file: the economic-evaluation output JSON as it is (new English
`output.json` or an old Spanish `salida.json`), or a CSV with columns `year,flow` (numbers without
thousands separator). Templates in `templates/`.

## Output language and files

The profile field `language` (`es` by default, `en`) sets sheet names, labels, the marker and the
console text. JSON keys are always English.

| | es (default) | en |
|---|---|---|
| Sheets | SUPUESTOS · AMORTIZACION · FLUJO-INVERSIONISTA · COMPARACION | ASSUMPTIONS · AMORTIZATION · INVESTOR-CASH-FLOW · COMPARISON |
| Files | `<case>-resultado.json` · `<case>-evaluacion-financiera.xlsx` | `<case>-result.json` · `<case>-financial-evaluation.xlsx` |
| Default folder | `<case folder>/salidas` | `<case folder>/outputs` |

## How to read the output

| Sheet | What it says |
|---|---|
| ASSUMPTIONS | each parameter, its value, where it came from; orange row = assumption; model rules, warnings and the assumptions inherited from the project flow |
| AMORTIZATION | one table per loan or leasing, with CAE or implicit rate and the check "sum of principal = amount financed" |
| INVESTOR-CASH-FLOW | per alternative and per year: project, payments, tax savings, residual, investor flow; at the end the monthly table the NPV is computed with |
| COMPARISON | ranking by PV cost, winner and by how much, rate that flips the decision, what is not comparable and the sensitivity |

JSON: `winner`, `runner_up`, `pv_difference`, `project_npv`, `indifference_rate_with_runner_up`,
`alternatives` (per alternative: `pv_cost`, `investor_npv`, `cae`, `after_tax_effective_rate`,
`notes`...), `assumptions` (the common format `[{parameter, value, origin, text}]`),
`project_flow_assumptions` (the project flow's own, from its `assumptions` or old `supuestos`),
`warnings`, `project_flow_regime`, `traceability` (the whole ASSUMPTIONS table), `sensitivity`.

Report: "X wins: it costs $N less in PV than Y", the indifference rate and which assumption could
flip the decision. No figure computed outside the script.

## Country notes

- **Chile (`country: CL`).** The CAE (*carga anual equivalente*, Law 20.555) is the effective
  annual cost of a loan with fees; the stamp tax (*impuesto de timbres*, DL 3.475: 0.066 % per
  month of term, capped at 0.8 %) goes in `loan_tax`; the CMF publishes the current and maximum
  conventional interest rates every month (a market reference for a loan rate, with its date);
  leasing installments are a lessee tax expense (art. 37 bis repealed in 2023); the Pro Pyme
  regime uses instant depreciation (`"depreciation": "instant"`), where buying deducts everything
  in year one and leasing loses its tax advantage. Sources in `SOURCES.md`.
- **Other countries.** The script models leasing as a lessee expense; where the lessee
  capitalizes the asset, model it as a loan (the script warns when `country` is not CL and there is
  a leasing). Loan taxes, if any, go in `loan_tax`; otherwise leave it out.

## Typical mistakes

- **Comparing the monthly installment.** A lower installment over a longer term is not cheaper;
  compare the after-tax PV cost.
- **Forgetting the tax shield.** Interest, leasing installments and rent reduce tax; loan principal
  does not.
- **Counting the purchase twice** when adding the loan to a flow that already carries the
  investment: that is why the script adds the difference against cash.
- **Mixing tax regimes.** A project flow at one tax rate with financing at another: the script
  warns; rerun economic-evaluation with the same regime and chain that output.
- **A tax saving without profits.** The model assumes the company has profits to use it; if not,
  the shield does not exist that year.
- **Effective rate with several sign changes.** The output warns; decide by the PV cost.

## Test

`python scripts/financial_evaluation.py --test` runs `tests/sample-case.json` against
`tests/expected.json` (checked by `tests/second_path.py`, closed formulas without the script),
the second-path identities, a project flow given as new and old economic-evaluation output, a case
with Spanish keys and a run with `language: en`, and ends in `OK` or `FAIL`.
