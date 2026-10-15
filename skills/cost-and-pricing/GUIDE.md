# Cost and pricing · guide for a person

This method answers two questions that look like one: **how much did what I sell cost me** and
**what do I sell it at**. It walks through a fictitious case: **Ferretería Andes** (a hardware
store) quotes an irrigation network to **Constructora Sur**. Every figure in this guide comes from
`python scripts/cost_pricing.py --test` (case in `tests/sample-case.json`). Spanish version:
`GUIA.md`.

Everything is **net**: value added tax is neither cost nor profit when the company recovers the
tax credit, so it does not enter any margin calculation.

## 1. Gather the purchase lines as the supplier wrote them

One row per purchase order line (or awarded quote line), **in the supplier's unit and currency**.
If the order says "7 lengths of 6 m at $21,900", that is what goes in; not "42 m at $3,650". The
document rules because it is what will be invoiced.

| Doc | Line | Supplier | Sale item | Qty | Unit | Unit price | Currency |
|---|---|---|---|---|---|---|---|
| PO-101 | 1 | Supplier A | VAL-50 | 30 | pc | 18,500 | CLP |
| PO-101 | 2 | Supplier A | TEF-34 | 24 | pc | 1,150 | CLP |
| PO-102 | 1 | Supplier B | VAL-50 | 10 | pc | 21.40 | USD |
| PO-103 | 1 | Supplier C | TUB-110 | 7 | 6 m length | 21,900 | CLP |
| PO-103 | 2 | Supplier C | COD-110 | 12 | pc | 3,450 | CLP |

The **sale item** column is the only judgement call in this step: it says which thing being sold
each purchase is charged to. The valve (VAL-50) was bought from two suppliers, and each one
describes it differently ("Bronze ball valve 2 in." and "Ball valve bronze 2""). If the
specification is the same, they go to the same item. If in doubt, ask: merging two different
products invents a cost that does not exist.

## 2. Declare the exchange rate

Supplier B's valve came in dollars. The exchange rate **is declared** with date and source (in the
case: 945.30 CLP per USD on 01-10-2026, given by the user). Without it, the script stops. In a
foreign currency, always two decimals: USD 21.40, not USD 21.

## 3. Weighted cost: what the unit really cost

The valve cost 18,500 from one supplier and 20,229.42 from the other (21.40 × 945.30). The real
cost is not the average of the two prices: it is the **quantity-weighted average**.

- Supplier A: 30 pc, $555,000.
- Supplier B: 10 pc, $202,294.20.
- Total $757,294.20 ÷ 40 pc = **$18,932.36 per unit**.

The simple average overweights the expensive supplier exactly when little was bought from it,
which is the normal case (the expensive one sells the balance the cheap one did not have).

The traceability sheet shows each line's weight in the item: PO-101 explains 73.3 % of the
valve's cost.

## 4. If it was bought in the supplier's unit, the leftover is paid for too

The pipe is sold by the metre and bought by the 6 m length (`unit_factor: 6`). 40 m are installed;
6.67 lengths are not bought, 7 are: **42 m, 2 m left over**.

- Weighted cost per metre bought: $153,300 ÷ 42 = **$3,650**.
- Cost per metre **sold**: $153,300 ÷ 40 = **$3,832.50**.

The difference is the cost of the leftover ($7,300), which reaches the site and is paid for
anyway. If the price is computed on $3,650, that leftover is given away.

## 5. Overhead: the cost that is in no purchase order

Rent, administrative salaries, vehicle, accountant: they are not bought for a particular job, but
sales pay for them. Here they are charged as a **share of direct cost** (8 % in the case). The
metre of pipe goes from $3,832.50 to **$4,139.10**.

This is **absorption costing** in its simplest form: the indirect cost is spread in proportion to
direct cost. It works well when all jobs look alike. It fails when a job is almost all expensive
material and little management (it absorbs too much indirect cost) or the reverse. Then it pays to
spread by labour hours or by activity (see `SOURCES.md`).

If nobody declares the overhead, the script uses 0 % and marks it as an assumption: a price
without overhead is a price that does not cover the office.

## 6. Price by markup, and next to it the real margin

**Markup** is what is added **on top of cost**. **Margin** is what is left **of the sale**.

```
price        = cost × (1 + markup)
real margin  = (price − cost) ÷ price
margin       = markup ÷ (1 + markup)        markup = margin ÷ (1 − margin)
```

The pipe, with a 30 % markup: $4,139.10 × 1.30 → **$5,381** per metre (rounded to pesos), with a
**real margin of 23.1 %**. The elbow carries its own 40 % markup: price $5,216, real margin 28.6 %.

Why the price is set with a markup: it is what is said out loud ("I put 30 on it") and what is
negotiated. Why the margin is shown: it is what really stays. The classic error is writing 30 in a
spreadsheet that computes `cost ÷ (1 − 30 %)`: it gives ×1.43 and not ×1.30, a 10 % overprice
nobody notices looking at the PDF.

**Manual price.** If the market sets the price (PTFE tape sells at $1,990 everywhere), write
`manual_price` and the script returns the markup that means: 60.2 % markup, 37.6 % real margin.

## 7. Read the total

| | Ferretería Andes case |
|---|---:|
| Direct cost | $979,594.20 |
| Total cost (with overhead) | $1,057,961.74 |
| Sales | $1,388,832 |
| Profit | $330,870.26 |
| Effective markup | 31.3 % |
| Overall real margin | 23.8 % |

The effective markup is not 30 % because each item has its own (the elbow 40 %, the tape 60.2 %).

## 8. Contribution margin and break-even of a service

The store also sells **installation hours**: $28,000 per hour, with $12,500 of variable cost per
hour (technician per hour, consumables, travel) and $1,860,000 of fixed costs per month.

- **Contribution margin** = price − variable cost = **$15,500 per hour**. It is what each hour
  contributes to pay the fixed costs (contribution ratio 55.4 %).
- **Break-even point** = fixed costs ÷ contribution margin = **120 hours per month**
  ($3,360,000 in sales). Below that, money is lost.
- With 160 expected hours, profit is $620,000 and the **safety margin** is 25 %: sales can drop by
  a quarter before losing money.

## 9. Variable costing and absorption costing

Both ways of costing give **the same total cost for the period**; what changes is **when** the
fixed production cost is recognized.

- **Variable costing**: the fixed production cost is an expense of the month, whether what was
  produced is sold or not. The product only carries its variable cost.
- **Absorption costing**: the fixed production cost is spread over the units produced. What stays
  in the warehouse takes its share of the fixed cost, and that fixed cost only becomes an expense
  when it is sold.

The case brings an **assembled irrigation kit**: 500 produced, 400 sold, price $45,000, variable
$27,000, fixed production costs $900,000 and fixed operating costs $360,000.

| | Variable | Absorption |
|---|---:|---:|
| Unit cost of the kit | $27,000 | $28,800 |
| Profit of the month | $5,940,000 | $6,120,000 |
| Ending inventory (100 kits) | $2,700,000 | $2,880,000 |

The profit difference, $180,000, is exactly the fixed production cost left in the 100 kits in the
warehouse. That is why absorption can **inflate profit by overproducing**, and why short-term price
and volume decisions look at the contribution margin.

In a **service** there is no inventory (an installation hour cannot be stored): both profits
coincide and the discussion comes down to the break-even point.

## 10. Before delivering

1. Read the assumptions sheet: what is in orange came from nobody.
2. Check the warnings: leftovers, large differences between suppliers, exchange rate without
   source.
3. The workbook has costs and suppliers: **it does not leave the company**. Only the price goes to
   the client.

## Country-specific notes (Chile, `country: CL`)

- The value added tax is the IVA (19 %). With an invoice the purchase IVA is recovered as tax
  credit (DL 825), which is why margins are computed net against net.
- CLP has no decimals: prices round to whole pesos; foreign currencies keep two decimals.
