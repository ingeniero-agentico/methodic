# Guide · economic evaluation of a project

For a person who wants to know whether a project is worth doing, step by step, with the fictitious
case in `tests/`: **Transportes del Valle** evaluates buying a van to rent it out by the day.
(Spanish version: `GUIA.md`.)

This method asks one question: **is the business worth doing by itself?** It is evaluated as if
the company paid for it in full with its own money (the "pure project"). If afterwards you must
decide how to pay for it (loan, leasing, cash), that is another method: see
`financial-evaluation`, which starts from the flow produced here.

## 1. Draw the line around what changes

Write down only what appears or disappears **if the project is done**. For the van:

| Changes | Does not change (stays out) |
|---|---|
| rental revenue, washing, insurance, maintenance, registration, GPS | owner's salary, office, accountant |

Decide also whether amounts go **net of VAT** (the company recovers the VAT) and whether they are
in **today's money** (then the rate is real). Transportes del Valle: net, today's money. Write it
in the input `note`: it reaches the assumptions sheet, marked.

## 2. Gather the numbers and mark the assumptions

| Item | Value | Where from? |
|---|---|---|
| Rate | $45,000 per day | competitors |
| Days available | 360 a year | calendar |
| Occupancy | 55 % (198 days) | management **ASSUMPTION** |
| Washing and wear | $6,000 per rented day | workshop **ASSUMPTION** |
| Insurance · maintenance · registration · GPS | $900,000 · $600,000 · $250,000 · $180,000 a year | quotes |
| Van | $18,000,000, tax useful life 7 years | list price |
| GPS unit | $160,000, useful life 3 years | quote |
| Salvage value of the van in year 5 | $7,000,000 | **ASSUMPTION** (used-van listings) |
| Working capital | $1,000,000 | **ASSUMPTION** |
| Rate · tax · horizon | 12 % · 27 % · 5 years | company profile |

Everything that does not come from a document is written down anyway, but **marked as an
assumption and with its reason**. The sensitivity will tell later which ones matter.

## 3. Build the cash flow (year 1)

```
  Revenue              45,000 × 198            8,910,000
− Variable costs        6,000 × 198           −1,188,000
− Fixed costs                                 −1,930,000
− Depreciation   18,000,000/7 + 160,000/3     −2,624,762
= Profit before tax                            3,167,238
− Tax (27 %)                                    −855,154
= Net profit                                   2,312,084
+ Depreciation (does not leave the cash box)   2,624,762
= Flow of year 1                               4,936,846
```

Depreciation is subtracted to pay less tax and added back because it is not money that leaves.
Year 0 is the investment: −18,000,000 − 160,000 − 1,000,000 = **−19,160,000**.

Year 5 adds three more things: the sale of the van ($7,000,000) minus its book value
($18,000,000 − 5 × 2,571,429 = $5,142,857) pays tax on the gain; the book value is added back;
and the working capital is recovered. Flow of year 5: **12,421,017**.

## 4. Compute the indicators

| Indicator | Result | Reading |
|---|---|---|
| NPV at 12 % | **$2,873,792** | worth it: it leaves $2.9 million of today above the required 12 % |
| IRR | 17.08 % | the project's own return; the flow changes sign once, so it is unique |
| Payback | 3.88 years (4.59 discounted) | recovered within the horizon |
| NPV index | 0.150 | each peso invested leaves 15 cents of NPV |

The **NPV** decides. The IRR is for communicating, unless the flow changes sign more than once
(then there may be several and it does not help).

## 5. Sensitivity: which assumption decides

One variable moves at a time, looking for the value that makes NPV zero:

| Variable | Base | Critical value | Room |
|---|---|---|---|
| Rate per day | $45,000 | $39,484 | −12.3 % |
| Occupancy | 55 % | 47.2 % (170 days) | −14.1 % |
| Van price | $18,000,000 | $21,516,694 | +19.5 % |
| Discount rate | 12 % | 17.08 % (the IRR) | +42 % |

Reading: the project **depends on occupancy and the rate**. If the van is rented fewer than 170
days a year, or the rate must drop more than 12 %, it stops being worth it. The first thing to
validate is not the insurance price: it is how many days it will be rented.

## 6. Decide and leave the trail

The recommendation states the NPV, the deciding variable, its critical value and the room
against what was assumed. And it leaves the assumptions visible so that someone can argue them.

With the agent: fill `templates/input.json` and run

```
python scripts/evaluate.py input.json --profile <company> --sweep "revenues[0].occupancy=0.4,0.5,0.6"
```

The output workbook has four sheets, named by the profile `language`: SUPUESTOS · FLUJO ·
INDICADORES · SENSIBILIDAD (es, the default) or ASSUMPTIONS · CASH FLOW · INDICATORS ·
SENSITIVITY (en), with the origin of every number.

## Country notes

- **Chile (`country: CL`).** The tax useful life comes from the SII table (a van: 7 years normal,
  2 accelerated). If the company recovers the IVA (input VAT), amounts go net; if not, the IVA on
  the purchase is part of the investment. The income tax rate depends on the regime (general or
  Pro Pyme) and goes in the profile.
- Elsewhere: the same steps with the local tax rate, depreciation table and VAT rule.

## Next step

If it is worth it and you must decide how to pay for it, see `financial-evaluation`.
