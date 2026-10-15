# Procurement · sources

The method is cited; course material is not reproduced.

## Courses it comes from

| Course | What it brings to the method |
|---|---|
| **Operations Management** (Gestión de Operaciones) | sourcing: supplier selection, comparison of offers, partial coverage, lead times and delivery terms |
| **Optimization** (Optimización) | the allocation as a linear problem: minimize Σ cost × quantity subject to covering each item's demand and not exceeding each supplier's availability |
| **Accounting and Costs** (Contabilidad y Costos) | acquisition cost: effective net price (after discounts), VAT apart from cost, the leftover bought is charged to the material cost |

## Why the cascade is the right decision (and when it stops being so)

Without fixed costs per order, each item is a separable linear problem: minimize
Σ cᵢ·xᵢ with Σ xᵢ = demand and 0 ≤ xᵢ ≤ availableᵢ. The optimal solution is to allocate in
increasing order of unit cost until the demand is covered (the same argument as the fractional
knapsack). The cascade is that optimum, not an approximation.

It stops being optimal when something appears that is not linear in the quantity, and then the
problem becomes mixed-integer:

- a fixed cost per order or per delivery (it pays to concentrate on fewer suppliers);
- minimum purchases, or volume discounts that depend on the order total;
- whole sale units (lengths, boxes): the cascade rounds up and declares the leftover, which is a
  reasonable heuristic but not always the minimum.

This version does not model those cases: it leaves them to human review (SKILL.md, "Review before
issuing").

## Bibliography

- Monczka, R. M.; Handfield, R. B.; Giunipero, L. C.; Patterson, J. L. *Purchasing and Supply Chain
  Management*. 7th ed. Cengage Learning, 2021. Chapters on supplier evaluation and selection, and on
  purchasing cost management.
- van Weele, A. J. *Purchasing and Supply Chain Management: Analysis, Strategy, Planning and
  Practice*. 7th ed. Cengage Learning, 2018. The purchasing process: specification, selection,
  contracting and ordering.
- Chopra, S.; Meindl, P. *Supply Chain Management: Strategy, Planning, and Operation*. 7th ed.
  Pearson, 2019. Chapter on sourcing decisions and total cost.
- Heizer, J.; Render, B.; Munson, C. *Operations Management: Sustainability and Supply Chain
  Management*. 13th ed. Pearson, 2020. Chapter on supply chain management.
- Hillier, F. S.; Lieberman, G. J. *Introduction to Operations Research*. 11th ed. McGraw-Hill,
  2021. Linear programming, the transportation problem and integer programming.
- Horngren, C. T.; Datar, S. M.; Rajan, M. V. *Cost Accounting: A Managerial Emphasis*. 16th ed.
  Pearson, 2018. Materials costing and cost allocation.

## Country-specific notes (Chile, `country: CL`)

- IVA (19 %) is Chile's value added tax: with an invoice, the purchase tax is recovered as tax
  credit, so it stays apart from cost.
- The supplier's tax identifier is the RUT, issued by the SII (Chile's tax service).

## Where the judgement came from

From real purchases of an industrial SME (private data, outside this repo). The hard rules in
`SKILL.md` (unit price derived from the total, reconciliation against the printed subtotal, buying
in the supplier's unit, rejection declared and not deleted, exchange rate set by whoever pays) were
born from errors that happened in those purchases. The script reproduces to the cent the
allocation of a real case with 64 items and 5 suppliers.
