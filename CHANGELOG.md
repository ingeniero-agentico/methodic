# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/).

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
