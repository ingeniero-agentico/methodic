---
name: cost-and-pricing
description: "Use when the purchase is made (purchase orders or awarded quotes exist) and the real cost of what a company sells must be known before pricing it: an item bought from several suppliers (weighted cost), in the supplier's unit (lengths, rolls) and sold by the metre, in a foreign currency, or loaded with overhead. Also to price by markup on cost with the real margin, and for contribution margin and the break-even point of a service or product (hours, units or kits per month to cover fixed costs). Use it even for a quick break-even or markup: the script gives the traceable number. Triggers: \"how much did it really cost us?\", \"what price do I sell it at?\", \"I put 30 on it, what margin is that?\", \"break-even point of my service\", \"¿cuánto me costó de verdad?\", \"¿a cuánto lo vendo?\", \"le puse 30\", \"punto de equilibrio\". Not for choosing among quotes (procurement) nor for whether an investment pays off over years (economic-evaluation). Computes real cost, price by markup with its margin, and break-even."
---

# Cost and pricing

**What it solves.** How much each item of a job really cost and what to sell it at, with every
number traced back to the purchase order line it came from.

**The naming rule, which is not negotiable.** The price is set with a **MARKUP on cost**
(0.30 = cost × 1.30). Next to it the **REAL MARGIN on sales** is shown
((price − cost) ÷ price). A 30 % markup is a 23.1 % margin. One word is never used for the other:
writing "30" in a column that computes cost ÷ (1 − 0.30) gives ×1.43 instead of ×1.30, a 10 %
overprice with no warning at all.

## When

- A job already has purchase orders (or awarded quotes) and the client must be quoted.
- An item was bought split between suppliers and nobody knows what the unit cost.
- It was bought in lengths, rolls or boxes and is sold by the metre or unit: material is left over.
- A purchase came in a foreign currency.
- You need to know how much of a service to sell to cover the month's fixed costs.

## What you (the agent) decide and what the script computes

| You decide | `scripts/cost_pricing.py` computes |
|---|---|
| Which purchase line goes to which sale item (`item`) | Direct cost per item, weighted by quantity |
| The unit factor (6 m length sold by the metre = 6) | Leftover and cost per unit **sold** |
| Whether two supplier descriptions are the same product | Currency conversion with the declared exchange rate |
| The exchange rate, with date and source (the user gives it) | Overhead on direct cost |
| Markup per item or global; manual price if the user sets it | Price, real margin, effective markup, profit |
| Fixed and variable costs of a service | Contribution margin, break-even point, variable vs absorption |

**Do not propose a flat markup** if the user did not ask for one: some items bear more than others.
If the profile has `default_markup`, use it as a starting point and say so.

**Two different descriptions may be the same product** (each supplier writes its own way). If the
specification numbers match, ask before merging them into a single `item`: merging two different
products invents an average cost that does not exist.

## How to run it

```
python scripts/cost_pricing.py <case.json> --profile <company> --out cost.xlsx [--json summary.json]
python scripts/cost_pricing.py --test
```

The input is a JSON shaped like `templates/case.json`: `purchases` (one row per purchase order
line, in the supplier's unit and currency), `items` (what is sold), `exchange_rates`, optional
`breakeven`, and optional `assumptions` (your own, as a text or `{parameter, value, source}`).
Spanish keys (`compras`, `tipos_de_cambio`, `precio_unit`, `factor_unidad`, `recargo`,
`equilibrio`, `supuestos`…) and the old Spanish flags (`--perfil`, `--salida`, `--probar`) still
work.

**The profile** is looked up like this: `--profile` (path or name) · the case's `profile` field ·
`$METHODIC_DATA/profiles/`, then the legacy `$INGENIERO_DATOS/profiles/` (then `perfiles/`) ·
`../methodic-data/profiles/`, or the legacy `../ingeniero-agentico-datos/` when the new one does not
exist (then `perfiles/`); with a name it looks for `<name>.yaml`, without one it takes the only profile there
(`--company` if there are several) · and if there is none, `profiles/_template.yaml` (then
`perfiles/_plantilla.yaml`), and everything taken from it is an assumption. From the profile it
reads `company.currency`, `company.currency_decimals`, `pricing.default_markup` and
`pricing.overhead`. The case can override the last two. Spanish profile keys are accepted.

**Output language.** Sheet names, labels, console text and the assumption marker follow the
profile's `language` (`es` by default, which reproduces the existing workbooks):

| `language` | Sheets | Marker |
|---|---|---|
| `es` (default) | `COSTO Y PRECIO` · `TRAZABILIDAD` · `EQUILIBRIO` · `SUPUESTOS` | `SUPUESTO` |
| `en` | `COST AND PRICE` · `TRACEABILITY` · `BREAK-EVEN` · `ASSUMPTIONS` | `ASSUMPTION` |

The JSON always has English keys.

## What it computes, in order

1. **Cost of each line** in local currency: quantity × unit price × exchange rate.
2. **Weighted cost** of the item: Σ costs ÷ Σ units bought (in sale units). Weighted, not simple:
   100 pc at $1,000 and 2 pc at $2,000 cost $1,019.61 each, not $1,500.
3. **Direct cost per unit sold**: Σ costs ÷ units sold. If 7 lengths of 6 m (42 m) were bought and
   40 m are installed, the 2 m left over are paid for anyway and go into the cost per metre.
4. **Total cost per unit** = direct cost × (1 + overhead).
5. **Price** = total cost × (1 + markup), rounded to the currency's decimals (half up, like a
   spreadsheet's `ROUND`). With `manual_price`, that price rules and the real markup is
   recomputed.
6. **Real margin** = (price − total cost) ÷ price, net against net.
7. **Break-even**: contribution margin = price − variable cost; break-even point = fixed costs ÷
   contribution margin. With units produced and sold, profit under variable and under absorption
   costing, and the difference (the fixed cost left in inventory).

## How to read the output

Excel with four sheets (the third only if there is `breakeven`; names below with `language: es`):

| Sheet | What |
|---|---|
| `COSTO Y PRECIO` | One item per row: quantity sold and bought, leftover, weighted cost, cost per unit sold, overhead, markup and its origin, price, real margin, sales, profit and the `doc:line` it came from. At the foot, effective markup and overall real margin. Blue background: bought from more than one supplier |
| `TRAZABILIDAD` | One row per purchase line: document, line, supplier, supplier unit, factor, original price, currency, exchange rate, local total and its weight in the item |
| `EQUILIBRIO` | Contribution margin, break-even in units and in sales, safety margin, and variable vs absorption |
| `SUPUESTOS` | Every parameter with its origin (case, profile or assumption), your declared assumptions, and the warnings. Orange = assumption |

The JSON (`--json`) carries the same numbers plus `parameters`, `assumptions` (each with its
`origin`: `template` · `default` · `input`) and `warnings`.

Before delivering, **read the warnings out loud** to the user: assumed overhead, leftovers,
exchange rate without source, large cost differences between suppliers.

The workbook carries costs and suppliers: **it is not sent to the client**. Only the price goes to
the client.

## Typical errors

| Symptom | Cause |
|---|---|
| `the purchase does not cover the sale` | `quantity_sold` larger than what was bought: a purchase order is missing or the unit factor is wrong |
| `declares no exchange rate for USD` | There is a line in another currency: ask for the rate with date and source, do not assume it |
| The price comes out 43 % over cost when 30 was asked | Someone treated the 30 as a margin. Here the field is `markup` |
| The cost per metre is higher than the length ÷ 6 | Correct if material is left over: the leftover is charged to what is sold |
| One item appears twice with different costs | Two suppliers describe it differently. If it is the same product, a single `item` |
| Overhead in orange | It came neither from the user nor from the profile: 0 % was used. Ask for it |
| Overall real margin differs from the markup asked | Normal: margin and markup are different things, and rounding the price moves tenths |

## Files

`GUIDE.md` (the method for a person, with the fictitious case; Spanish version in `GUIA.md`) ·
`templates/case.json` · `tests/` (Ferretería Andes: `sample-case.json`, `sample-profile.yaml`,
`expected.json`) · `SOURCES.md`.
