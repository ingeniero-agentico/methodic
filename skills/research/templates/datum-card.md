# Datum card

Each datum of `research-data.json` is an object with these fields. The validator
(`scripts/validate_research.py`) requires the mandatory ones. The executor and the auditor read
the same fields (see "The format" in `SKILL.md`).

| Field | Required | What goes |
|---|---|---|
| `id` | yes | unique in the research (`D01`, `D02`…) |
| `gap` | yes | id of the gap it answers (`H1`…) |
| `description` | yes | what it is, in one line, with the exact segment (term, bracket, region) |
| `quantity` | yes | what it measures, as a short key (`leasing_rate`, `registration_fee`). Two data with the same quantity and unit are compared with each other |
| `value` | yes | a number, or a text if the datum is qualitative ("purchase option = one rent"); `null` only if `status` is `not_found` |
| `range` | no | `[minimum, maximum]` when the source gives a range; if `value` is a number, it falls inside |
| `unit` | yes | `% monthly`, `% annual linear`, `CLP`, `UF`, `fraction of the price`… |
| `data_date` | yes | `DD-MM-YYYY`: the date the value corresponds to (validity, publication, measured month) or `undated` |
| `source` | yes, except `calculated` | `{"url": "https://…"}` and/or `{"document": "name, number, date, point"}` |
| `retrieval_date` | yes | `DD-MM-YYYY`: when it was read |
| `reliability` | yes | `A` norm, law, official body, client's document · `B` book, paper, manufacturer's manual · `C` supplier, quote, specialized press · `D` blog, forum, AI without a source |
| `status` | yes | `verified` (read in the original) · `to_confirm` (read in a summary or aggregator) · `calculated` (comes from `formula`) · `not_found` (searched and not there) |
| `usable` | yes | `true` if it can enter a calculation |
| `assumption` | yes | `true` if it enters as an ASSUMPTION. Mandatory for a usable D or `to_confirm` |
| `formula` | if `calculated` | arithmetic with ids of other data: `D01 / 12`, `D22 * (1 - D23)` |
| `tolerance` | no | relative tolerance of the recomputation (default 0.001) |
| `type` | no | `norm` for laws, decrees and fees in force: they do not age by date nor ask for a second source |
| `note` | no | what changes the reading of the datum (what it does not measure, why it was not opened) |

**Usage** is not written: it is derived. `yes` = usable and not an assumption · `ASSUMPTION` =
usable and an assumption · `no` = not usable. That is the column the executor and the auditor read.

Gaps carry `id`, `question`, `precision`, `method`, `for` (the input field it goes to), `status`
(`has_data` · `no_data`) and, with data, `chosen` and `choice_reason`; without data,
`how_to_close`. Sweep sources carry `id`, `source`, `url`, `access` (`open` · `person_fetches` ·
`no_public_source` · `no_response`), `gaps` and `note`. Contradictions carry `data`, `prevails`
and `reason`.

A file written before v1.1 uses the Spanish keys (`hueco`, `descripcion`, `magnitud`, `valor`,
`unidad`, `fecha_dato`, `fuente`, `fecha_consulta`, `nivel`, `estado`, `supuesto`…); the validator
accepts it unchanged.

## Example

```json
{"id": "D01", "gap": "H1", "description": "Leasing rate quoted by Supplier A, 36 months",
 "quantity": "leasing_rate", "value": 1.45, "unit": "% monthly", "data_date": "10-03-2030",
 "source": {"document": "quote Supplier A No. 101, point 3"}, "retrieval_date": "12-03-2030",
 "reliability": "C", "status": "verified", "usable": true, "assumption": false}
```

## Rules the validator enforces

1. A usable D or `to_confirm` goes with `assumption: true`.
2. A `calculated` datum has no better reliability than its worst input and inherits the
   assumption of its inputs.
3. Two data of the same quantity and unit that differ more than the threshold go together in
   `contradictions`, with the one that prevails and the reason.
