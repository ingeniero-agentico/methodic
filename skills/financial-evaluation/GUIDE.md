# Guide · financial evaluation

How to decide whether an asset is paid cash, with a loan, with a leasing or rented, step by step,
with the fictitious case in `tests/`. (Spanish version: `GUIA.md`.)

> It is a calculation method, not personalized financial advice.

## The question

**Transportes del Valle** (a fictitious company) needs a $24,000,000 (net) van. It already knows
the van pays for itself (its pure project flow gives NPV $5,291,023 at 12 %). Now the question is
different: **how does it pay for it?**

| Alternative | Terms |
|---|---|
| Cash | $24,000,000 today |
| Loan 36 months | 20 % down payment, 1.5 % monthly, French amortization, $250,000 of fees, insurance $8,000 a month, loan stamp tax 0.066 % per month capped at 0.8 % |
| Loan 36 months (German) | the same with fixed principal |
| Leasing 36 months | 1.3 % monthly, initial installment and purchase option equal to one installment |
| Rental 60 months | $620,000 a month, one month's deposit; includes maintenance and insurance |

Profile: tax 27 %, discount rate 12 %, horizon 5 years, straight-line depreciation over 7 years.
Sale value of the van in year 5: $9,000,000 (ASSUMPTION).

## Step 1 · Separate the project from the financing

The project (is the van worth it?) is evaluated without debt: that is `economic-evaluation`. This
method starts from that flow and only adds what changes with each way of paying. The bridge is a
file (`tests/sample-project-flow.csv`, columns `year,flow`, or the economic-evaluation output
JSON), not copied figures. With the JSON the script also checks that both use the same tax regime.

## Step 2 · Normalize the offers

Before comparing, all must refer to the same asset, the same period of use and the same value at
the end. What cannot be equalized is declared: the rental includes maintenance and insurance; the
others do not. That fact is not averaged, it is written next to the result.

## Step 3 · The amortization table

**French installment** (fixed installment): C = L · i / (1 − (1 + i)^−n). With L = $19,200,000,
i = 1.5 % and n = 36, the installment is **$694,126**. Each month the interest is balance × i and
the rest of the installment pays down principal. **German amortization**: principal is fixed
(L / n) and the installment falls month by month; it starts at $821,333.

The table must tie: the sum of principal is exactly the amount borrowed, and the formula's
installment is the table's. The last installment absorbs the rounding to the peso.

**Effective annual cost (CAE in Chile)**: the rate that equates what really reaches the borrower
(amount − fees − loan tax) with everything paid (installments + insurance), monthly × 12. Here it
is **20.37 %**, although the agreed rate is 1.5 % × 12 = 18 %. Loans are compared by this cost,
not by the rate.

**Leasing**: the price equals initial installment + 36 installments + purchase option in month 37,
discounted at the leasing rate. Installment: **$794,063**.

## Step 4 · The tax effect

Each alternative reduces taxes differently:

- **Cash**: depreciation of the van ($24,000,000 / 7 a year).
- **Loan**: depreciation + interest + fees + insurance. Principal does not reduce tax.
- **Leasing** (Chilean rule): the initial installment and every installment are an expense; the van
  is capitalized when the option is exercised, at the option's value, and depreciated from there.
- **Rental**: the rent is an expense; there is no asset and no sale value.

When selling at the end, tax is paid on the difference between the sale price and the book value.
In the leasing the book value is almost zero (the option), so it pays more tax when selling.

## Step 5 · The investor cash flow

Investor flow = project flow + (asset flow with the alternative − asset flow in cash).

For the loan, that is the same as the classic layout: project + loan − installments + tax saving
on interest. Subtracting cash avoids counting the purchase twice, because the project flow already
carries the investment.

## Step 6 · Compare and decide

| Rank | Alternative | After-tax PV cost | After-tax effective cost | Investor NPV |
|---|---|---|---|---|
| 1 | Leasing 36 months | $15,250,911 | 10.22 % | $5,924,574 |
| 2 | Cash | $15,884,462 | | $5,291,023 |
| 3 | Loan 36 months (German) | $16,905,972 | 16.55 % | $4,269,514 |
| 4 | Loan 36 months | $16,948,620 | 16.38 % | $4,226,865 |
| 5 | Rental 60 months | $21,291,354 | 21.53 % | $−115,868 |

How to read it:

1. **Leasing wins by $633,551 in present value** over cash.
2. **The after-tax effective cost** of the leasing (10.22 %) is below the discount rate (12 %):
   financing that way costs less than what its own money earns. The loan (16.38 %) costs more than
   12 %, which is why it loses against cash.
3. **Between the two loans**, German amortization is cheaper: since the debt costs more than the
   discount rate, it pays to return it sooner.
4. **The rate that flips the decision is 10.22 %**: if the company's money earns less than that,
   cash wins. The sensitivity confirms it: at 9 % cash wins, and with 0 % tax too (without a tax
   shield the leasing loses its advantage).
5. **The rental** is the most expensive, but it includes maintenance and insurance: before ruling
   it out, subtract what those services cost in the other alternatives.

## The discount rate: WACC and CAPM (reference)

A small company can use its **opportunity cost**: what its money earns in its best real
alternative. The two classic tools are these, as reference, not mandatory:

- **WACC** (weighted average cost of capital):
  WACC = E/(D+E) · kₑ + D/(D+E) · k_d · (1 − t). It weights what the owners require (kₑ) and what
  debt costs after tax. It discounts the project flow when the company keeps a stable mix of debt
  and equity.
- **CAPM** (capital asset pricing model): kₑ = r_f + β · (r_m − r_f). The return the owner
  requires is the risk-free rate plus a premium for systematic risk (β). A small company without
  traded shares has no β of its own: take that of comparable companies in the industry, unlever
  it and relever it with the company's debt, and add a size and liquidity premium. That is why,
  for a small company, it is a reference and not a required calculation.

The script takes a single rate (the profile's or `--rate`) and gives the indifference rate, so
the discussion becomes "does the owner's money earn more or less than X %?".

## Country notes

- **Chile (`country: CL`).** The CAE is the legal name of the effective annual cost (Law 20.555);
  the stamp tax goes in `loan_tax`; the CMF certificate of current interest is a dated market
  reference for the loan rate (check it is the one in force); leasing installments are a lessee
  expense; under Pro Pyme use `"depreciation": "instant"`.
- **Other countries.** Same steps; the loan tax, if any, in `loan_tax`; if the lessee capitalizes
  the leasing, model it as a loan.

## Run the case

```
python scripts/financial_evaluation.py --test
python scripts/financial_evaluation.py --case tests/sample-case.json --profile tests/sample-profile.yaml
```

`--test` compares with `tests/expected.json` and checks by a second path that the annuity
formula's installment is the table's, that principal adds up to the amount to the peso and that
the investor NPV is the project NPV plus the advantage over cash. `expected.json` was checked with
`tests/second_path.py`, which recomputes everything with closed formulas (annuities, balance by
formula, yearly shields) without the script: the largest difference is 6 pesos, from rounding
installments and interest to the peso.
