# Trigger evals · does each skill fire on the right request?

This suite answers one question per skill: **does it activate when it should, and stay silent when
it should not?** It does not grade the quality of the answer (the `--test` of each script does
that for the numbers). It runs with `claude plugin eval`, the Claude Code command that loads the
plugin in an isolated session, sends a prompt and grades what happened
([docs](https://code.claude.com/docs/en/plugin-evals)).

## Layout

```
evals/
├── README.md
├── .gitignore                  results/ stays out of git
├── tools/
│   ├── cases.json              the single source: every prompt, its owner skill and what should fire
│   ├── build_cases.py          writes the case folders from cases.json (--check only validates)
│   └── score.py                precision and recall per skill from a run's aggregate-result.json
├── procurement/                generated: one folder per case
│   └── procurement-p1-es-a-quien-le-compro/
│       ├── prompt.md           frontmatter (limits, tags) + the prompt
│       └── graders/
│           ├── fires-procurement.md
│           └── silent-<each other skill>.md
├── cost-and-pricing/ · economic-evaluation/ · financial-evaluation/
├── orchestrate/ · map-context/ · research/ · audit/
└── results/<timestamp>/        written by each run (aggregate-result.json, report.html)
```

**Do not edit the generated folders.** Edit `tools/cases.json` and run
`python evals/tools/build_cases.py` (it deletes and rewrites the eight skill folders).

## The cases (15-10-2026)

| Skill | Positive (es + en) | Negative | Near-misses among the negatives |
|---|---|---|---|
| procurement | 6 (3 + 3) | 4 | cost-and-pricing, financial-evaluation |
| cost-and-pricing | 6 (3 + 3) | 4 | procurement, economic-evaluation, "margins" of a Word file |
| economic-evaluation | 6 (3 + 3) | 4 | financial-evaluation, cost-and-pricing (break-even), research |
| financial-evaluation | 6 (3 + 3) | 4 | economic-evaluation (×2), research, personal mortgage |
| orchestrate | 6 (3 + 3) | 4 | a single NPV, amortization table or markup, "how do subagents work" |
| map-context | 6 (3 + 3) | 4 | research, a road map, a mind map, a folder-publishing audit |
| research | 6 (3 + 3) | 4 | map-context, economic-evaluation, academic writing |
| audit | 6 (3 + 3) | 4 | tender document audit, web security audit, recalculating, code review |

80 cases in total. Case names read `<owner>-<p|n><number>-<es|en>-<slug>`. Tags: `trigger`, the
owner skill, `positive` or `negative`, `es` or `en`, and `near-miss` or `borderline` where it applies.

A negative is not just "something else": when it belongs to a neighbour, the case expects the
neighbour to fire (for example the economic-evaluation negative "¿contado, crédito o leasing?"
expects financial-evaluation). So each case says which single skill should fire, or none.

## How it is graded

Every grader is `tool_used` on the `Skill` tool, so grading is free (no judge model):

| Grader | Passes when | Weight |
|---|---|---|
| `fires-<skill>` | the expected skill was invoked at least once | 7 |
| `silent-<skill>` | that skill was never invoked (`min: 0`, `max: 0`) | 1 each |

The match accepts `procurement` and the namespaced `ingeniero-agentico:procurement`, and also the
pre-v1.1 Spanish name (`adquisiciones`, `costo-y-precio`, `evaluacion-economica`,
`evaluacion-financiera`, `orquestar`, `cartografiar`, `investigar`, `auditar`) while the
translation is in progress. Remove the old names from `skills` in `cases.json` once it is merged.

Reading a case score: **1.00** exactly the right skill fired and nothing else · **0.50** the
expected skill did not fire, nothing else did · **0.93** it fired, plus one intruder · lower,
several intruders. A case that expects no skill scores 1/8 less per intruder.

**Exception:** a case that expects `orchestrate` only carries `fires-orchestrate`, because
orchestrate may load the skills of its chain afterwards. That is also why no negative of another
skill expects orchestrate.

## How to run it

Requirements: Claude Code 2.1.269 or later (`claude --version`), git 2.31 or later, logged in as
in your normal sessions. **Every run is a real model call on your account** (plan usage or API
bill). The suite grants no Bash, Write or WebFetch, so it needs no OS sandbox and runs on native
Windows.

From the plugin root (`ingeniero-agentico/`):

```bash
# Cheap pass: one run per case, no baseline arm (80 agent runs)
claude plugin eval . --ablation none --runs 1 --no-publish --model claude-sonnet-5

# One skill, or only the near-misses
claude plugin eval . --ablation none --runs 1 --tag financial-evaluation
claude plugin eval . --ablation none --runs 1 --tag near-miss

# Full pass: three runs per case (240 agent runs); add a ceiling if you want one
claude plugin eval . --ablation none --no-publish --max-cost-usd 30 --json evals/results/full.json
```

- **Use `--ablation none`.** The no-plugin baseline is meaningless for a trigger test: without
  the plugin no skill of it can fire, so every `fires-` grader fails and every `silent-` passes.
  It would only double the cost.
- **Pin `--model`** so a model change is not read as a description change. Compare runs only
  with the same model.
- The first run in a directory asks `Trust this plugin directory?`. Answer `y` in a terminal, or
  pass `--trust-plugin` in CI.
- Each run already gets its own temporary home and Claude Code configuration; your settings,
  memory, other plugins and `CLAUDE.md` do not load. Pointing `CLAUDE_CONFIG_DIR` at an empty
  folder isolates the parent process too, but that folder has no login, so the runs fail with
  "Invalid API key" unless `ANTHROPIC_API_KEY` is set.
- The progress line `has no mock and is NOT started` for the plugin's MCP server is expected:
  triggering does not need it.

## How to read the results

1. **The summary table** (`SCORE`, `PASS%` per case): any case below 1.00 is a trigger error.
   Open `report.html` (path printed at the end) to see, run by run, which grader failed.
2. **Precision and recall per skill:**

   ```bash
   python evals/tools/score.py                      # latest evals/results/<timestamp>/
   python evals/tools/score.py evals/results/full.json --md evals/results/trigger-report.md
   ```

   For each skill: TP (fired where expected), FN (did not fire where expected), FP (fired where it
   should not, in any case of the suite), TN. **Low recall** means the description does not catch
   the way people ask (look at the `missed:` lines, which say what fired instead). **Low precision**
   means it steals requests from a neighbour or from outside the plugin (`fired where it should
   not:` lines). Recall is also split by language, to catch a description that only works in
   English.
3. **What to change:** the skill's `description` in its `SKILL.md` (at most 1,024 characters).
   Add the phrasing it missed, add a `Not for ... (neighbour)` sentence for what it stole, run the
   same cases again with `--case` or `--tag`, and confirm with three runs before trusting it: one
   run is noisy.

`tool_used` counts every call in the run, not only the first. A run where orchestrate fires first
and then the right method shows up as a hit for the method and an intrusion for orchestrate,
which is the point: a single-method request should go straight to the method.

## Limits

- Each run starts in an empty folder. Prompts that mention a folder or a case describe it in
  words; the trigger decision is taken before Claude looks for it.
- The prompts are realistic but written by hand; they measure the descriptions against these
  phrasings, not against every phrasing.
- `borderline` cases (an accounting concept for an exam, a personal mortgage) are judgment calls:
  a fire there is a weaker signal than a fire on a clear negative.
- Validated on 15-10-2026: the suite loads and the plugin resolves (probe run with a temporary
  `CLAUDE_CONFIG_DIR` and an invalid key, cost $0.00). It has not been run against the model yet.
