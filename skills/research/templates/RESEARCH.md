# Research · <task in a few words> · DD-MM-YYYY

- **Stage:** 1 · Research, mode <first-run | new gap in a reread>.
- **Origin of the gaps:** <context/MAP.md · context/PLAN.md · task>.
- **Machine-readable data:** `research-data.json` (this page summarizes it).
- **Validation:** `python validate_research.py <case>/context/research-data.json` → **OK**
  (N gaps, N data, 0 errors, N warnings).

## Short answer

Three to five lines: what was closed (with the figure and its source), what stayed without data
and whether the decision changes.

## Gaps

| Id | Question | Precision the calculation needs | For which field | Status | Chosen datum |
|---|---|---|---|---|---|

## Obtainability sweep (before researching)

| Id | Source | Access | Gaps | Note |
|---|---|---|---|---|

Access: `open` · `person_fetches` (login, CAPTCHA, payment, page that does not load without a
browser) · `no_public_source` · `no_response`.

## Data

Paste the output of `validate_research.py --table`. No figure is copied by hand.

Notes that change the reading of a datum: <only the ones that matter>.

## Contradictions

| Data | Prevails | Why |
|---|---|---|

## Calculation chain

Only if there are `calculated` data: link by link, with the id of each input and its reliability.

## What the person has to fetch or ask for

1. <concrete action that closes a gap without data>

## What would change in the case

If there is already a calculation: whether the datum moves the decision, against the threshold
the calculation declared. If it was recalculated, the copy of the input and its output are in
`sensitivity/`; the case's input and output are not touched.

## Validator warnings

- <code · datum · what it means>
