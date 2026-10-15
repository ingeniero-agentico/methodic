# Guide · research

How to close the gaps of a calculation with data that can stand a question ("where does that
number come from?"), step by step, with the sample case in `tests/sample-case.json`. A Spanish
version lives in `GUIA.md`.

## The question

**Ferretería Andes** (a fictitious company) is evaluating buying an electric forklift cash or with
leasing. The calculation (`financial-evaluation`) is ready, but it is missing four numbers:

| Gap | Question | Precision |
|---|---|---|
| H1 | Monthly leasing rate for an SME, warehouse equipment, 36 months | ±0.05 points |
| H2 | Legal maximum rate for operations of that amount | exact |
| H3 | Sale value of the forklift in year 5 | ±15% |
| H4 | Deed and registration costs of the contract | ±$20,000 |

The precision is not decoration: it says when to stop. If the calculation tolerates ±15%,
searching for the third decimal is a waste of time.

## Step 1 · The obtainability sweep, before searching

For each gap, which sources exist and which can be opened:

| Source | Access | Gap |
|---|---|---|
| Monthly certificate of the regulator (fictitious) | open | H2 |
| Equipment auction portal | the person fetches it (asks for a registered account) | H3 |
| Bank leasing rates | no public source (they are quoted) | H1 |
| Registry fee schedule | open | H4 |

**What sits behind a login or a CAPTCHA is not bypassed:** it is noted for the person. And the
fact that nobody publishes the leasing rate is also a datum: it says the gap is closed by asking
for quotes, not by searching.

Why before? Because relevance and access are independent: the most useful source is often the
least accessible. If access is checked at the end, the search is done twice.

## Step 2 · One concrete datum per gap

For H1 three figures arrive:

| Datum | Value | Source | Reliability |
|---|---|---|---|
| F1 | 1.45% monthly | quote Supplier A | C |
| F2 | 1.62% monthly | quote Bank B (includes insurance) | C |
| F3 | 1.10% monthly | a forum | D |

Each one carries value, unit, data date, source, retrieval date and reliability (full card in
`templates/datum-card.md`). F3 is D: **it orients, but it does not enter the calculation** unless
marked as an assumption. And if a figure was read in a search-engine summary and not in the
original, it stays `to_confirm`, even if it comes from an official body.

## Step 3 · Contradictions, together and with a reason

F1 and F2 measure the same thing and F2 is 11.7% higher: it exceeds the 10% threshold. They are not
averaged. They are put together and one is chosen with a reason someone can review:

> F1 prevails: F1 and F2 are quotes for the same equipment; F2 carries an insurance inside the
> rate. F3 is a forum and does not compete.

The typical reasons: the current datum over the previous one, the primary source over the press,
the measured over the theoretical, the exact segment over the general average. When two figures
**seem** to answer the same thing but measure different things (an average of the whole system
against that of a bracket), the reason is to say what each one measures.

## Step 4 · The calculation chain, audited too

H2 comes annual (30% linear, F4) and the calculation asks for it monthly. The monthly figure is not
written by hand: it is a `calculated` datum with its formula, `F5 = F4 / 12 = 2.5%`. The validator
recomputes it and checks that it does not have a better reliability than its worst input: a
calculation is never more reliable than the weakest datum it uses.

## Step 5 · What was not found is declared

H3 has no open source: it stays `no_data`, with the action that closes it ("ask two used-equipment
dealers for a written appraisal"). A declared gap costs less than a false datum; the calculation
continues with its assumption and the person knows what to ask for.

H4 mixes: the official registration fee (F7, A) enters as a datum; the notary only has a forum
(F6, D), and enters as an assumption.

## Step 6 · Validate and write

```
python scripts/validate_research.py tests/sample-case.json
```

The validator checks the fields, the reliability levels, the dates, that each gap has a datum or
an action, that no D enters without being an assumption, the calculation chain and the
contradictions. It ends in `OK` or lists the errors. In the sample case it gives OK with four
warnings: the fee is more than a year old, the fee has a single source, the notary has no date and
the auction portal has to be opened by the person.

Only with `OK` is `RESEARCH.md` written (format in `templates/`), pasting the tables that `--table`
prints. The executor and the auditor read the same file: `--json` gives them, per gap, the chosen
data with `reliability` and `usage` (`yes`, `ASSUMPTION`, `no`). In the case, H4 enters with F7
(`yes`) and F6 (`ASSUMPTION`).

## Step 7 · Does the decision change?

If the calculation already exists and declared a threshold ("leasing wins if the money yields more
than X%"), the research ends by saying whether the datum found crosses that threshold. If it has
to be recalculated, run the method's script on a **copy** of the input in `context/sensitivity/`:
the case's input and output are not touched until the person decides.

## Checklist

- [ ] Each gap has a question, precision, method and target field (`for`).
- [ ] The sweep was done before searching and says what the person has to fetch.
- [ ] Each datum has value, unit, date, source, retrieval date and reliability.
- [ ] No D nor `to_confirm` enters the calculation without being an assumption.
- [ ] The contradictions are together and with a reason.
- [ ] Derived numbers are `calculated` data with a formula, not sums in a note.
- [ ] The validator ends in `OK`.
- [ ] `RESEARCH.md` says whether the decision changes.
