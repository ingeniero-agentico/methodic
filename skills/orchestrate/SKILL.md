---
name: orchestrate
description: "Use when someone brings a business task and it is not obvious where to start: a company or process nobody has documented yet (\"entiende mi negocio\", \"documenta cómo trabajamos\", \"estandariza esto\"), a change to make on the operator's computer that needs the context first, a task that needs more than one method in sequence (quotes, then purchase plan, then sale price; an investment, then whether it pays, then how to finance it), a folder or vague brief, or when the person asks to \"launch agents\", \"orchestrate\", \"lánzale agentes\", \"orquesta esto\", \"no sé por dónde partir\". Runs methodic's stages in order: map, interview, research only for gaps, document the manual, plan and ask, execute (intervene or a method), audit, consolidate. Reads the manual instead of asking again when one exists. Not for a single calculation whose method is clear and whose data is in the message (call that method directly), nor for one small change in an already documented process (call intervene)."
---

# Orchestrate a task

You run in the **main conversation**: you are the only one who can launch agents and the only one
who talks with the operator. The agents in `agents/` are workers of one stage; none of them
launches another. The contracts: `ARCHITECTURE.md` (stages, modes, `context/`) and
`docs/MANUAL-FORMAT.md` (the manual, the scope, the logbook). Read them if something here is not
enough.

**Three things you never do:** solve a number from memory (it comes from a method's script),
assume what the operator did not say (it is a gap or a `SUPUESTO`), and touch a file of the
operator without the intervention cycle.

## 0. Understand the task and find the data

1. Rewrite the task in one line: what has to be understood, decided or changed, and for whom.
2. Data folder: `--data` · `METHODIC_DATA` · `INGENIERO_DATOS` · `../methodic-data/` ·
   `../ingeniero-agentico-datos/`. Profile: `profiles/<company>.yaml` (then `perfiles/`). If there
   is more than one profile and the task does not say which, **ask**. No profile: copy
   `profiles/_template.yaml` with the operator in the first interview round.
3. The manual: `<data>/manual/<company>/`. **If it exists, read its index (`NEGOCIO.md` /
   `BUSINESS.md`) and only the process the task touches.** Nothing else from the manual. If it does
   not exist, run `skills/manual/scripts/manual.py init --company <company>`.
4. Classify the task:

| The task is… | Route |
|---|---|
| Understand or standardize a business or process | 2 interview → 4 document → 7 (no execution) |
| Change something on the operator's computer | process documented? (if not, 2 and 4 first) → 5 plan → 6 `intervene` |
| A decision with numbers | 5 plan → 6 method(s) and audit → 7 |

| The numbers ask… | Method |
|---|---|
| Who do I buy from, what is still to be quoted | `procurement` |
| How much did it cost, what do I sell at, how much do I make | `cost-and-pricing` |
| Is this project or investment worth it? | `economic-evaluation` |
| How do I finance it? | `financial-evaluation` |

Chains: quotes → `procurement` → `cost-and-pricing`. Investment → `economic-evaluation` → (if
NPV ≥ 0) `financial-evaluation`. If none fits, say so; do not force one. A method call ties to the
manual step that needs it (`→ \`procurement\`` in the page).

## 1. Map the context (cheap; only if there are folders)

Launch the `cartographer` agent on the folders the task touches and the scope allows. It returns
the **mode** (`first-run` or `reread`) and `context/MAP.md`. In a reread you read the map, its core
(at most 3 files) and what changed. Nothing else. The operator's word overrides the mode.

## 2. Interview (only what the manual does not answer)

Use the `interview` skill. Batches of 3 to 4 questions with options, one batch per turn, "don't
know" always available. `interview.py next` chooses the batch; `interview.py record` writes the
answers. Before asking, check the index: **a question the manual already answers is not asked
again.** Round 3 (limits) is mandatory before any intervention: without a scope nothing is touched.

## 3. Research (only for gaps that need outside data)

Only if a gap needs a datum the operator cannot give (a market rate, a norm, a price). Launch the
`researcher` agent with those gaps; every datum comes with source, date and reliability (A–D).

## 4. Document

Use the `manual` skill: write or update the index and the process page from the interview record,
the documents and the research, every step with its source. Then
`manual.py check --company <company>`: **a page with errors is not shown as done.** Show the
operator the page (or the diff) and ask whether it is right; their approval is
`manual.py revise <CODE> --approve --by <role>`. If the task was only to understand or standardize,
go to 7.

## 5. Plan and ask

Write `context/PLAN.md`:

```
Task: <one line>          Process: <CODE> (rev. <x>)          Mode: first-run | reread
Agents: N                 Estimated cost: low | medium | high

| # | Stage     | Who        | Skill                | Model  | Input             | Output         | Depends on |
|---|-----------|------------|----------------------|--------|-------------------|----------------|------------|
| 1 | Execute   | executor   | economic-evaluation  | sonnet | input.json        | output.json    | —          |
| 2 | Audit     | auditor    | audit                | opus   | everything above  | AUDIT.md       | 1          |
| 3 | Intervene | you        | intervene            | —      | plantilla-oc.xlsx | logbook line   | 2          |

Gaps still open: <list, or "none">        Assumptions that will be used: <list>
```

Rules: research only for gaps; reread → `haiku` or `sonnet` except the audit; the auditor never
below `sonnet` and always goes if someone will use the numbers; in parallel what does not depend
on each other. Cost: low ≤ 2 economical agents · medium 3 to 4 · high ≥ 5 or two `opus`.

**Show the plan and wait for the yes.** Launch nothing before. "Without agents" or a platform
without them: do each stage yourself, in order, in this conversation.

## 6. Execute and audit

- **Methods:** one `executor` per plan row, all agents of a wave in one message. Each gets its row,
  the path of `context/`, the profile and the case folder; it reads only its method's `SKILL.md`
  and leaves its manifest in `context/runs/<id>.json`. Then the `auditor` re-runs every script.
- **Interventions:** always you, in the main conversation, with the `intervene` skill: plan → OK of
  the operator for that one action → backup → execute → verify with a fact → logbook line. An
  intervention is never delegated to an agent: the OK has to come from the person.
- If an agent fails, you do not replace it with a calculation of your own: report it and propose
  the fix.

## 7. Consolidate

With `AUDIT.md` in view; a **NOT COMPLIANT** is the first line of the answer. In the conversation,
at most 150 words; the detail goes to a file.

1. **The result** in one sentence (what was documented, decided or changed).
2. **What decides it**: the two or three assumptions or gaps that would turn it around.
3. **Where** each output was left (manual page, logbook line, case output).
4. **What is missing** to ask whoever decides.

Then close the loop so the next session starts by reading, not asking:
- What the task taught goes into the manual (`manual.py revise <CODE> --change "…"`), and
  `manual.py check` passes.
- `map_context.py --out <context/> --mark-read`.

Outputs for a person follow the profile's `language` (`es` by default).

## Typical errors

- Asking again what the index already says: it wastes the operator's time and tokens.
- Reading the whole manual "to be sure": load the index and the one process.
- Intervening before round 3 (limits): without a scope, nothing is touched.
- Treating one OK as permission for the whole session: one OK covers one action.
- Giving the answer before the audit, or leaving the lesson only in the conversation.
- Writing `context/` or the manual inside the public repo: they live in the data folder.
