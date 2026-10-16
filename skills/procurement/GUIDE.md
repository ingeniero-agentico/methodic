# Procurement · step-by-step guide

The same method as `SKILL.md`, for a person. It walks through the fictitious case in
`tests/sample-case.json`: **Constructora Sur** needs six items for the water network of a work
site and received three quotes (Supplier A, B and C). Spanish version: `GUIA.md`.

**What the script does and what it does not.** This first version **compares and allocates**. Two
steps stay outside the script and are done by hand: **reading the quotes** (step 1) and **issuing
the purchase orders** (step 6). They are described here so the method is complete.

## 0 · The company profile

Copy `profiles/_template.yaml` to `methodic-data/profiles/<company>.yaml` and fill in at
least `currency`, `currency_decimals`, `vat` and `purchasing.tie_break`. Set `language: en` if you
want the workbook in English (`es` is the default). Without a profile, the script uses the template
and lists everything it took from it as an assumption: good for testing, not for buying.

## 1 · Read each quote (outside the script)

For each document, transcribe **all** its lines into the input (`templates/input.json`):

| Field | What goes in |
|---|---|
| `line` | the number the supplier gives it in its document |
| `quantity` | in the unit the supplier sells |
| `line_total` | what it charges for the line, discount included |
| `printed_unit_price` | what it prints as unit price (reference only) |
| `printed_subtotal` | the document's net subtotal, once per quote |

Three things that slip through:

- **A line that appears twice is transcribed twice.** It happens when the product came in two
  batches. If you read only the first, the supplier seems to cover less than it does.
- **Freight and what nobody asked for are transcribed too**, with `item: null`. Without them the
  sum does not reach the printed subtotal.
- **The sale unit is copied verbatim.** "x 6 Mts" or "length 5.8 mts" goes in
  `sale_unit.verbatim`; it is what later reveals that one supplier sells shorter lengths than the
  rest.

In the case: Supplier B prints the elbow at **4,000** but the line charges **112,000 for 40**. The
unit price that counts is 2,800. Read from the printed figure, B looked the most expensive; it is
the cheapest.

## 2 · Match and reject

For each line, write in `item` the number of the requirement it belongs to. Before the price, the
specification: size, pressure rating, material, joint type. **An item much cheaper than the rest
is almost always another product.**

In the case: **4"** pressure gauges are requested; Supplier B quotes a **2.5"** one. The line stays
in the input with `rejected: "2.5\" dial; 4\" is required."`. That way it does not compete, and the
reason is written down.

## 3 · Run

```bash
python scripts/procurement.py input.json --out PROCUREMENT.xlsx --profile <profile.yaml>
```

If a quote does not match its printed subtotal, the script stops and says which one. Go back to
step 1: a line is missing, one is extra, or a total was copied wrong.

## 4 · Read the allocation

What comes out for Constructora Sur (all computed by the script; see `tests/expected.json`):

| Item | What happened |
|---|---|
| 1 · Pipe 2", 104 m | B sells it at 9,500 per metre in 5.8 m lengths and has 10 lengths (58 m). The 46 m balance goes to A, at 10,000 per metre in 6 m lengths: **8 lengths = 48 m, 2 m left over** (paid for) |
| 2 · Elbow 2", 40 pc | B (2,800) has 30; the 10 missing go to A (3,000). C (3,200) does not get in |
| 3 · Valve 1", 12 pc | B at 8,400 against A at 8,500 |
| 4 · Coupling 2", 60 pc | A at 2,000 against C at 2,100 |
| 5 · Gauge 4", 4 pc | **TO QUOTE**: the only offer was rejected |
| 6 · Cap 2", 10 pc | A and C tie at 1,500. C wins because it has 10 and A only 6 (tie-break by highest availability: one order fewer) |

Net total 1,380,800; with the template's VAT, 1,643,152. Three orders: B 735,800, A 630,000,
C 15,000. C's delivery charge (25,000) stays out of the allocation: it appears in VERIFICATION as
a line without item, to be decided separately.

Each row of the allocation sheet says where its unit price came from, for example
`B-202 line 4: 551,000 CLP ÷ 58 (10 × 5.8) = 9,500.00 per m`.

## 5 · Review before issuing

Read the whole verification sheet. Then the decisions that belong to a person:

- **Item 2 is split.** B was 10 elbows short. Asking it for those 10 at the same price saves the
  unit price difference on those 10 units and one line in A's order (if it works out, correct
  `available` and run again: the number comes from the script).
- **Item 5 is uncovered.** Quote it elsewhere, or confirm whether the 2.5" one will do (that is
  changing the specification, not the price).
- **Item 1 has a leftover.** The extra 2 m reach the site and are paid for. If it matters, ask A to
  cut, or accept it.
- **Expiry.** B expires in 7 days: its order goes first.

## 6 · Issue the purchase orders (outside the script)

One order per supplier, with what the allocation sheet says:

- **In the supplier's unit.** A is asked for 8 lengths of 6 m, not 48 m. If the order goes in
  metres, it invoices lengths and the difference shows up later.
- **In the supplier's currency.** If it quoted in another currency, the order goes in that one; the
  converted value is only for comparing.
- **With its tax ID.** Without it the order is not issued: the suppliers sheet marks it MISSING.

Before sending them, someone who did not build them compares every line of every order against the
original quote.

## Errors the method catches

| Error | Where it is caught |
|---|---|
| A line forgotten when transcribing | reconciliation against the printed subtotal (aborts) |
| A list unit price taken as the price | derived from the total; VERIFICATION lists the printed ones that differ |
| Another currency taken as local | without `exchange_rate`, it aborts |
| Half a pipe in the order | bought in whole supplier units |
| A rejected offer that wins anyway | `rejected` takes it out of the allocation |
| The gap nobody sees | TO QUOTE in the summary, allocation and verification sheets |

## Country-specific notes (Chile, `country: CL`)

- `vat` is the IVA (19 %). It is shown apart from the net: for a company that recovers the tax
  credit, IVA is neither cost nor profit.
- The supplier's tax ID is the RUT; without it a purchase order cannot be invoiced.
