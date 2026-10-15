---
name: procurement
description: "Use when supplier quotes for the same purchase must become a purchase decision, before any purchase order exists: comparing prices line by line, deciding who gets which items when each supplier covers only part of the quantity, flagging what nobody quoted, or checking that a quote adds up to its printed subtotal. Also when quotes come in different currencies (USD and CLP at a given exchange rate), a supplier discounts only the line total, or sells in whole units (6 m lengths, boxes of 10). Use it even for two or three quotes: the script gives the traceable allocation. Triggers: \"who do I buy from?\", \"compare these quotes\", \"line up the USD and CLP quotes\", \"¿a quién le compro?\", \"compara las cotizaciones\", \"¿cuadra esta cotización?\". Not for the real cost or sale price once purchase orders exist (cost-and-pricing), nor for how to pay for an asset (financial-evaluation). Compares quotes and allocates the purchase in cascade, every number traced to its quote and line."
---

# Procurement · compare quotes and allocate the purchase

**The cheapest does not win: the allocation wins.** Suppliers quote partial quantities. The one
with the lowest unit price sells what it has, the balance goes to the next one, and whatever nobody
covers stays **TO QUOTE**. Requiring a single supplier to cover everything sends whole lines to the
expensive one over two missing units.

The agent sets the judgement (which line of each quote matches which requested item, and whether
the specification fits). The script does all the arithmetic: reconciliation, effective unit price,
currency conversion, allocation, totals and the Excel workbook.

```bash
python scripts/procurement.py input.json --out PROCUREMENT.xlsx [--profile profile.yaml] [--company name]
python scripts/procurement.py --test      # the fictitious case must end in OK
```

Empty input: `templates/input.json` (it carries help for each field in `_help`). Spanish input
keys (`requerimiento`, `cotizaciones`, `lineas`, `total_linea`, `unidad_venta`, `descarte`…) and
the old Spanish flags (`--salida`, `--perfil`, `--empresa`, `--probar`) still work.

## When to use it

- Two or more quotes arrived for the same purchase and you must decide whom to buy what from.
- One supplier seems to win by far and you must confirm it is the same product.
- Someone asked "where does this price come from?" and the comparison does not say.

It needs the quotes already read. **This version neither reads PDFs nor issues purchase orders**:
extraction and issuing are manual steps described in `GUIDE.md` (steps 1 and 6).

## The profile rules

The script reads from the company profile: `company.currency`, `company.currency_decimals`,
`company.vat` and `purchasing.tie_break`. It looks for it in this order:

1. `--profile <path or name>`.
2. The environment variable `INGENIERO_DATOS` (a file, or a folder with `profiles/` or `perfiles/`).
3. The repo's sibling folder, `../ingeniero-agentico-datos/profiles/` (then `perfiles/`). If there
   are several profiles, pick one with `--company`.
4. If there is none, `profiles/_template.yaml` (then `perfiles/_plantilla.yaml`), and **everything
   taken from it is listed as an assumption**.

A real profile without `currency` or `vat` aborts: it is asked, never invented. Spanish profile
keys (`empresa.moneda`, `compras.desempate: mayor_disponibilidad`…) are accepted.

**Output language.** Excel sheet names and labels, console text and the assumption marker follow
the profile's `language` (`es` by default, so existing cases reproduce the same workbook):

| `language` | Sheets | Marker |
|---|---|---|
| `es` (default) | `RESUMEN` · `ASIGNACION` · `COMPARATIVA` · `PROVEEDORES` · `VERIFICACION` | `SUPUESTO` |
| `en` | `SUMMARY` · `ALLOCATION` · `COMPARISON` · `SUPPLIERS` · `VERIFICATION` | `ASSUMPTION` |

The output JSON always has English keys.

## What the agent decides (before running)

1. **Match each line to its item** (`item` = the `n` of the requirement). Every supplier names the
   same product differently. **Check the specification before the price: an item 4× cheaper is
   almost always another product** (another pressure rating, size, joint type or material).
2. **Reject what does not fit**, with `rejected: "<reason>"` on the line. Never delete the line or
   leave it "for reference": a deleted line cannot be told apart from an omission, and without
   `rejected` it competes and wins. The script takes it out of the allocation and lists it in
   VERIFICATION.
3. **The supplier's unit.** If it sells lengths, bars or boxes, `quantity` goes in that unit and
   `sale_unit.content` says how much of the item each one holds (6 m per length). Copy the
   document's text into `verbatim`: it is the proof of where the number came from.
4. **What is available.** If the supplier declared it delivers less than it quoted, it goes in
   `available`. If it did not declare it, the quoted amount is assumed and listed as an
   assumption. **If it did not quote an item, leave the line out: never load 0.**
5. **The currency.** If it is not the profile's, `exchange_rate` and `exchange_rate_date` are
   required. The rate is set by whoever pays (what their bank charges), never a website.
6. **Your own assumptions** go in `assumptions` (a text, or `{parameter, value, source}`): they
   reach the output with origin `input`.

## What the script computes

| Step | Rule |
|---|---|
| Reconciliation | The lines of each quote add up to its `printed_subtotal`. If not, it **aborts**: a line is missing, one is extra, or a total was copied wrong |
| Unit price | `line_total ÷ (quantity × content)`. **Never the printed one**: some print list prices and discount only in the total. Lines with printed ≠ effective are listed |
| Currency | Converted with the declared `exchange_rate`; the trace keeps the original |
| Allocation | Cascade by unit price. Tie: `purchasing.tie_break` in the profile (`highest_availability` = fewer orders; `shortest_lead_time`) |
| Whole units | Bought in the supplier's unit, rounding up without exceeding what is available. **The leftover is paid for** and declared |
| Counteroffer | Same item, same supplier and salesperson in two quotes: the one with the newest `date` replaces the old one. Without different dates, it aborts |
| Assumptions | The JSON always carries `assumptions`: profile fields taken from the template or from a default, values the script assumed, and the ones you declared, each with its `origin` (`template` · `default` · `script` · `input`) |

## How to read the output

The workbook has five sheets and a JSON with the same content (names below with `language: es`;
the English ones are in the table above):

| Sheet | What it answers |
|---|---|
| `RESUMEN` | net total, VAT and total; how much goes to each supplier; what is missing; the assumptions |
| `ASIGNACION` | what is bought from whom, in which unit and at what price. **Every row carries its trace**: quote, line and the division that gave the unit price. Yellow = split item |
| `COMPARATIVA` | each supplier's effective unit price per item, with best, worst and difference |
| `PROVEEDORES` | each quote: currency, exchange rate, sum of lines against printed subtotal, allocated amount |
| `VERIFICACION` | quantity check, rejections, printed ≠ effective, counteroffers, lines without item (freight), assumptions and warnings. **Read it before issuing** |

## Review before issuing

The script allocates by price. A person decides this:

- **Split balances.** If the cheap one covers 25 of 40, asking it for the balance at the same price
  usually beats sending 15 to the expensive one.
- **What is missing.** Quote it elsewhere or change the specification.
- **Quotes about to expire.** The allocation assumes current prices.
- **Lines without item** (freight, packing). They stay out of the allocation; included freight is
  not a discount.
- **A small order is not a problem in itself.** Do not drop a supplier for a few units unless the
  user declares an order-handling cost.

## Typical errors

| Symptom | Cause |
|---|---|
| One supplier comes out twice as expensive as everyone | Its list unit price was read (the script uses the effective one; check that `line_total` is what it charges) |
| One supplier comes out ~900 times cheaper | It quotes in another currency and the quote does not declare `currency` |
| Something wins that it cannot deliver | `available` is missing |
| Something wins that it did not quote | A line was loaded at 0 instead of being left out |
| It wins by far on one item | It is another specification: it goes with `rejected` |
| "NO CUADRA" / "MISMATCH" | A line is missing in the extraction. **Do not go on until it is found** |
| Material is left over on site | Correct: it is bought in the supplier's unit and the leftover is declared |

## Files

`GUIDE.md` (the method for a person, with the fictitious case; Spanish version in `GUIA.md`) ·
`templates/input.json` · `tests/` (`sample-case.json` + `expected.json`) · `SOURCES.md`.
