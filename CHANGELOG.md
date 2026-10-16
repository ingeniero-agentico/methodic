# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/).

## [2.0.0] · 16-10-2026

methodic. The repo stops being a box of methods and becomes a methodical documenter: it
understands a business by asking, writes a traceable manual and only then intervenes on the
operator's computer. The methods stay, as its tools.

### Added
- `interview`: batches of 3 to 4 questions with options from a fixed question bank (three rounds:
  the business, the process that hurts, the limits); "don't know" becomes a dated gap; a form mode
  for operators who prefer to fill a round at once.
- `manual`: the index (≤ 400 words) and one page per process (≤ 800 words, SIPOC on top, steps
  below); every step with a code, a responsible, a tool and its source (interview, document,
  observed or assumption); status, revision and history. `manual.py check` verifies caps and
  traceability.
- `intervene`: plan → OK of the operator per action → backup → execute → verify → logbook line;
  scope check that resolves links before deciding; a generator of the permissions file for the
  operator's agent, because a skill's text alone does not enforce.
- `docs/MANUAL-FORMAT.md`: the single contract of the manual, the scope and the logbook.
- Repo rule 8: no script touches an operator's file outside the intervention cycle.

### Changed
- **Renamed to `methodic`** (repo, plugin, marketplace, MCP server). The GitHub organization stays
  `ingeniero-agentico`. Reinstall: `/plugin marketplace add ingeniero-agentico/methodic`.
- Data folder `methodic-data/` and variable `METHODIC_DATA`; the legacy `ingeniero-agentico-datos/`
  and `INGENIERO_DATOS` are still read, so existing data keeps working without moving it.
- `orchestrate` runs the new stages: understand → map → interview → research (only for gaps) →
  document → plan and ask → execute and audit (interventions never delegated) → consolidate, writing
  the lesson back into the manual. `ARCHITECTURE.md` version 3.0.

## [1.1.3] · 16-10-2026

### Changed
- The MCP server's default `--max-response` drops from 400,000 to 40,000 characters (about 10,000
  tokens). Every tool call is paid by the operator's own model account, so a smaller cap keeps the
  server usable on plans without large limits. The largest real output measured (an economic
  evaluation) is about 26,500 characters, so normal results still arrive whole; a larger one
  returns the path of its JSON instead.

## [1.1.2] · 15-10-2026

### Fixed
- Frontmatter of every skill, agent and command is now valid strict YAML: descriptions are
  double-quoted. Five descriptions contained ': ' unquoted, which Claude Code tolerates but the
  Agent Skills reference validator (and stricter platforms) reject.
- The four in-repo frontmatter readers (install, MCP server, map-context, security scan) unquote
  double- and single-quoted values correctly.

### Added
- `install.py` rejects an unquoted value containing ': ' or ' #' before installing anything.
- The `skills-ref validate` CI job now blocks instead of only reporting.

## [1.1.1] · 15-10-2026

### Changed
- Skill descriptions tell the agent to use the method even for a quick calculation (an
  amortization table, an NPV of given flows, a break-even, a markup), and add the trigger phrases
  that the first trigger evals missed: quotes in USD and CLP, an IRR that "came out weird", "I'm
  back, what changed?", a price page behind a login, sources that disagree, the maximum
  conventional rate. Trigger evals: precision 100 % on all 80 cases; the 10 missed positives now fire.
- Two eval cases now carry the data they ask about (a markup per item, a two-sign-change IRR).

### Fixed
- Install and MCP self-tests resolve temp paths (Windows 8.3 short names, macOS `/private/var`).

## [1.1.0] · 15-10-2026

### Changed
- English is now the base language of the repo: skills, agents, scripts, docs and identifiers.
  Spanish lives alongside (`README.es.md`, `GUIA.md` in every skill) and script outputs follow the
  profile `language` (`es` by default).
- Skills renamed: `procurement`, `cost-and-pricing`, `economic-evaluation`, `financial-evaluation`,
  `orchestrate`, `map-context`, `research`, `audit`. Every pre-1.1 Spanish flag, input key, profile
  key and `contexto/` file name is still accepted.
- Skill descriptions carry trigger phrases in English and Spanish and a "Not for…" boundary.
- The repo moved to the `ingeniero-agentico` GitHub organization.

### Added
- One assumptions format for every method: `assumptions: [{parameter, value, origin, text}]`.
- One research data format shared by research, executor and auditor.
- `audit` reads archived pre-1.1 outputs through an output-key alias map.
- `map-context` leaves out of the core a file that another one declares replaced.
- `financial-evaluation` warns when the project flow and the financing use different tax regimes.
- Security layer: `security/scan.py` (network, dangerous execution, obfuscation, hidden Unicode,
  prompt injection, secrets, private data), `security/MANIFEST.sha256` verified by the installer
  and the MCP server before they do anything, git hooks, CI on Linux, Windows and macOS with
  actions pinned by SHA, gitleaks, `SECURITY.md`, `CODEOWNERS`.
- Trigger evals for every skill (`evals/`, 80 cases).
- Multi-platform install (`install/install.py`): Claude Code, Claude Desktop, Codex, Cursor,
  Gemini CLI, Hermes and any Agent Skills agent. MCP server (`mcp/server.py`).
- `requirements.txt` pins `openpyxl`.

## [1.0.0] · 15-10-2026

### Added
- Four methods with skill, guide, templates, script and a test checked by a second path:
  procurement, cost and pricing, economic evaluation, financial evaluation.
- Multi-agent orchestration in six stages with first-run and reread modes.
- Claude Code plugin.
