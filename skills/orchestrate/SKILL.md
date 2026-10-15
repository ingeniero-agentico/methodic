---
name: orchestrate
description: "Use when a business or engineering task needs more than one method in sequence (quotes, then purchase plan, then sale price; an investment, then whether it pays, then how to finance it), when it arrives as a folder or a vague brief and it is not obvious which method applies, or when the person asks to \"launch agents\", \"orchestrate\", \"research and calculate\", \"lánzale agentes\", \"orquesta esto\", \"no sé por dónde partir\". Maps the environment first, decides between a first run (with research) and a cheap reread, proposes a plan of agents with one skill per stage, waits for approval, launches them in parallel where possible, audits and consolidates one traceable answer. Not for a single calculation whose method is clear and whose data is in the message (an NPV, an amortization table, a markup): call that method directly. Receives the task, maps the context, proposes the agent plan, launches it with approval and delivers one audited answer."
---

# Orchestrate a task

You run in the **main conversation**: you are the only one who can launch agents. The agents in
`agents/` are workers of one stage; none of them launches another. The full contract is in
`ARCHITECTURE.md` (repo root): read it if something here is not enough.

**You do not solve from memory.** Every number comes from a method's script, and every external
datum from the research with its source.

## 0. Understand the task and find the data

1. Rewrite the task in one line: which decision has to be made and for whom.
2. Company profile: `INGENIERO_DATOS` → `../ingeniero-agentico-datos/profiles/` (then
   `perfiles/`) → template. If there is more than one profile and the task does not say which,
   **ask**.
3. Case folder: `<data>/cases/<method>-<case>/` (an existing `casos/` folder is used as it is;
   create the case if it is new). `context/` lives there.
4. Choose the method or the chain:

| The task asks… | Method |
|---|---|
| Who do I buy from, what is still to be quoted | `procurement` |
| How much did it cost, what do I sell at, how much do I make | `cost-and-pricing` |
| Is this project or investment worth it? | `economic-evaluation` |
| How do I finance it? | `financial-evaluation` |

Chains: quotes → `procurement` → `cost-and-pricing`. Investment → `economic-evaluation` →
(if NPV ≥ 0) `financial-evaluation`. If none fits, say so; do not force one.

## 1. Map the context (always, it is cheap)

Launch the `cartographer` agent on the folders the task touches (the case's, the ones the person
named, the profile). It returns the **mode** and the path of `context/MAP.md`.

- `first-run`: there was no map, or more than the threshold changed.
- `reread`: there is a map and little changed. From here on **you read the map, not the
  folders**: the map, its "Core · always read" section (at most 3 files) and the files the
  cartographer listed as changed. Nothing else.

The person can force the mode ("do it as a reread", "research from scratch"). Their word rules.
A map written before v1.1 says `primera-vez` (= `first-run`) or `relectura` (= `reread`) and
lives in `contexto/MAPA.md`: read it the same way.

## 2. Plan and ask

With the map (and without opening more files than needed), write `context/PLAN.md`:

```
Task: <one line>
Mode: first-run | reread        Agents: N        Estimated cost: low | medium | high

| # | Stage    | Agent      | Skill                | Model   | Input              | Output             | Depends on |
|---|----------|------------|----------------------|---------|--------------------|--------------------|------------|
| 1 | Research | researcher | research             | opus    | gaps of the map    | RESEARCH.md        | —          |
| 2 | Execute  | executor   | economic-evaluation  | sonnet  | input.json         | output.json        | 1          |
| 3 | Execute  | executor   | financial-evaluation | sonnet  | output.json of 2   | result.json        | 2          |
| 4 | Audit    | auditor    | audit                | opus    | everything above   | AUDIT.md           | 2, 3       |

Gaps that justify researching: <list, or "none">
Assumptions that will be used if there is no research: <list>
```

Plan rules:
- **Research only if there are gaps** the calculation needs. In a reread, by default not.
- **Models:** reread → `haiku` or `sonnet` everywhere except the audit. First run → `opus` in
  research and audit. The auditor never goes below `sonnet`.
- **In parallel** what does not depend on each other; in sequence what is chained.
- **The auditor always goes** if there are numbers someone will use.
- Cost: low ≤ 2 economical agents · medium 3 to 4 · high ≥ 5 or two `opus`.

**Show the plan to the person and wait.** They answer "yes", change a row or ask for another mode.
Launch no agent before that. If the person says "without agents" or the environment does not
allow them, do each stage yourself, in order, in this conversation.

## 3. Launch

- Launch in **one single message** all the agents of a wave with no pending dependencies.
- To each one you pass: its plan row, the path of `context/`, the profile, the case folder and
  what to return. Nothing else: it reads the rest from the map. Tell the executor **which method**
  it runs: it reads only that `SKILL.md` (the four are not preloaded).
- If there is research, the executor and the auditor read the same `context/research-data.json`
  (`chosen`, `reliability`, usage `yes` · `ASSUMPTION` · `no`; format in
  `skills/research/SKILL.md`). Do not summarize it for them in other words.
- Each executor leaves its manifest in `context/runs/<id>.json` (command with `{OUT}`, outputs,
  decisive figure and assumptions). Without a manifest there is no audit: if it is missing, ask for
  it before launching the auditor.
- When a wave ends, check that the output exists before launching the next one. If an agent fails,
  you do not replace it with a calculation of your own: report it and propose the fix.

## 4. Consolidate

With `AUDIT.md` in view. If there is a **NOT COMPLIANT**, that is the first line of the answer.

1. **The decision** in one sentence (what is worth it and by how much).
2. **The assumptions that decide it**: the two or three that turn it around, with their threshold.
3. **Where** each output was left.
4. **What is missing** to ask whoever decides.

When closing, run `map_context.py --out <context/> --mark-read`: it empties the changes and leaves
the fingerprints up to date. The next time on the same case will be a reread.

Outputs for a person (`PLAN.md`, the answer) follow the profile's `language` (`es` by default).

## Typical errors

- Reading the full folders in a reread "to be sure": it cancels the saving. If the map is not
  enough, the fix is to improve the map, not to skip it.
- Launching the researcher out of habit: only with declared gaps.
- Giving the answer before the audit.
- Writing `context/` inside the public repo: it always goes in the data folder.
