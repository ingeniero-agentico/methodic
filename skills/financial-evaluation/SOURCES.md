# Sources · financial-evaluation

The method is cited; course material is not reproduced.

## Courses (Industrial Engineering)

| Course | What it brings to the method |
|---|---|
| Finance (2026-1) | valuation, CAPM and beta (unlevered and levered), capital structure and cost of capital; portfolio theory as the basis of systematic risk |
| Finance (2026-2) | time value of money, equivalent rates, annuities (a loan installment), NPV; fixed income (the flow of a debt and its internal rate) |
| Technical Project Evaluation workshop | the pure project cash flow as input; separation between project and financing |

## Bibliography

- Sapag Chain, N., Sapag Chain, R. and Sapag Puelma, J. M. *Preparación y evaluación de proyectos*
  (6th ed.). McGraw-Hill, 2014. Ch. 1 and 2 (the project as an investment decision); the chapters
  on building cash flows (project flow and investor flow with a loan, interest as an expense and
  principal after tax) and on the discount rate (cost of debt, cost of equity, weighted cost).
  The course hands out ch. 1 and 2; the edition of that extract is not verified.
- Blank, L. and Tarquin, A. *Ingeniería económica* (7th ed., Spanish edition of *Engineering
  Economy*). McGraw-Hill, 2012. ISBN 978-607-15-0761-7. Ch. 2 (factors; P/A and A/P, basis of the
  French installment), ch. 4 (nominal and effective rates; monthly to annual), ch. 7 (rate of
  return and multiple roots), ch. 10 (project financing: cost of debt and equity, debt-equity mix
  and weighted average cost), ch. 16 (depreciation), ch. 17 (after-tax analysis: after-tax flow
  and the effect of depreciation on tax).
- Támara Ayús, A. L., Chica Arrieta, I. E. and Montiel Ensuncho, A. «Metodología de cálculo del
  beta: beta de los activos, beta apalancado y beta corregido por cash». *Revista Espacios*,
  vol. 38, no. 34, 2017, p. 15. Finance course note for the CAPM in the GUIDE.

## Country notes · Chile (`country: CL`)

- Law 18.010, art. 6 and 6 bis: current interest and maximum conventional interest (the CMF
  publishes the certificate every month in the Diario Oficial). Market reference for a loan rate;
  check the certificate in force on the date of the case.
- Law 20.555 and its regulation: the CAE (*carga anual equivalente*) as the annual cost of a loan
  with fees included.
- DL 3.475, stamp tax (*impuesto de timbres y estampillas*): 0.066 % per month of term capped at
  0.8 % (SII, Circular 17 of 2015). Goes in the case's `loan_tax`.
- Income Tax Law (DL 824), art. 31: interest, leasing installments and rents as expenses; art. 31
  no. 5 and 5 bis: normal and accelerated depreciation; art. 14 letter D: Pro Pyme regime
  (instant depreciation, expense on what is actually paid).
- Law 21.540 (15-02-2023) and SII, Circular 14 of 2023: repeal art. 37 bis (leasing as an asset of
  the lessee); the leasing installment is again an expense. If a country treats leasing as an
  asset, the case is modeled as a loan.

Other countries: their own rules on loan taxes, interest ceilings and leasing treatment take the
same places (`loan_tax`, the loan rate's `source`, loan instead of leasing).

The tax rate, the discount rate and the horizon are **not** written here: each company's profile
gives them.
