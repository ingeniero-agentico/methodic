# Installing ingeniero-agentico

Version 1.1.0 · checked against each platform's documentation on 15-10-2026.

The repo installs in two ways: as a **plugin** (Claude Code, Claude Desktop and claude.ai) or by
copying its skills into the folder each agent reads, with `install/install.py`. The skills follow
the [Agent Skills](https://agentskills.io/specification) standard, so the same `SKILL.md` works on
all of them; what changes is where they go, whether there are subagents and how the private data
arrives.

## Summary

| Platform | Command | Where the skills end up | Orchestration |
|---|---|---|---|
| Claude Code | `/plugin marketplace add ingeniero-agentico/ingeniero-agentico` and `/plugin install ingeniero-agentico@ingeniero-agentico` | plugin cache (`~/.claude/plugins/`) | with agents |
| Claude Code without the plugin | `python install/install.py --platform claude-code` | `~/.claude/skills/` | with agents |
| Claude Desktop and claude.ai | `python install/install.py --platform claude-desktop` and upload the ZIPs | your account (Customize) | chat: in sequence · Cowork: with agents |
| Codex | `python install/install.py --platform codex` | `~/.agents/skills/` | TOML subagents or in sequence |
| Cursor | `python install/install.py --platform cursor` | `~/.cursor/skills/` | subagents or in sequence |
| Gemini CLI | `python install/install.py --platform gemini` | `~/.gemini/skills/` | subagents or in sequence |
| Hermes Agent | `python install/install.py --platform hermes` | `%LOCALAPPDATA%\hermes\skills\` (Windows) · `~/.hermes/skills/` | `delegate_task` or in sequence |
| Any other Agent Skills agent | `python install/install.py --platform agents` | `~/.agents/skills/` | in sequence |

Before any of them: Python 3.11 or newer with `openpyxl`. The tested version is pinned in
`requirements.txt` at the repo root: `python -m pip install -r requirements.txt`. To clone the repo
while it is not public, you need permission on GitHub and git credentials on your computer.

The full table of paths, with the URL that backs each one, is in `install/platforms.json`.

## Private data, on every platform

The scripts look for the company profile in this order: `--profile` · the `INGENIERO_DATOS`
variable · the sibling folder `ingeniero-agentico-datos/` · the repo template (everything comes out
as an assumption). Inside the data folder they look in `profiles/` first and then in the older
`perfiles/`; cases go in `cases/` or the older `casos/`. The sibling folder depends on where the
script was installed:

| Installation | «Sibling folder» the script looks for |
|---|---|
| Cloned repo or `--link` | next to the repo: `<repo folder>/../ingeniero-agentico-datos/` |
| Copy in Claude Code, Codex, Cursor, Gemini or `agents` | `~/ingeniero-agentico-datos/` |
| Copy in Hermes (Windows) | `%LOCALAPPDATA%\ingeniero-agentico-datos\` |
| Claude Code plugin | none that helps (it lands inside the cache): use `INGENIERO_DATOS` |
| claude.ai (sandbox) | does not exist: upload the profile to the chat and pass it with `--profile` |

**The safe choice is to set `INGENIERO_DATOS`** to the path of your data folder. Never put a real
profile inside the repo or inside the installed skills folder.

The profile field `language: es | en` decides the language of the script outputs (Excel labels,
the `SUPUESTO` / `ASSUMPTION` marker, console text). It defaults to `es`, so profiles written for
version 1.0 keep producing the same files. Spanish profile keys (`empresa`, `compras`, `precios`,
`finanzas`) are still accepted.

---

## Claude Code

### As a plugin (recommended)

Inside a Claude Code session:

```
/plugin marketplace add ingeniero-agentico/ingeniero-agentico
/plugin install ingeniero-agentico@ingeniero-agentico
```

Since version 2.1.275 one line is enough: `/plugin install ingeniero-agentico --marketplace ingeniero-agentico/ingeniero-agentico`.
From the terminal, the same with `claude plugin marketplace add ...` and `claude plugin install ...`.

- **Repo access.** Claude Code clones with your computer's git and without asking for a password.
  If the repo is not public for you, first run `gh auth login` and `gh auth setup-git` (HTTPS), or
  load an SSH key in `ssh-agent`. Without an SSH key, set `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`.
- **Branch.** The catalog is read from the default branch (`main`).
- **Names.** Skills get a prefix: `/ingeniero-agentico:orchestrate`,
  `/ingeniero-agentico:new-task`; agents, `ingeniero-agentico:cartographer`, etc.
- **Updates.** `plugin.json` pins `"version": "1.1.0"`: whoever installed does not receive changes
  until the version goes up. Every new release bumps the version. Users update with
  `/plugin marketplace update ingeniero-agentico`.
- **Data.** In `~/.claude/settings.json`: `"env": { "INGENIERO_DATOS": "<path to ingeniero-agentico-datos>" }`.

**The MCP server comes included.** `plugin.json` declares the `mcp/server.py` server in `mcpServers`
(details in `docs/MCP.md`), so `/plugin install` registers it by itself, as
`plugin:ingeniero-agentico:ingeniero-agentico`. It is launched with `${CLAUDE_PLUGIN_ROOT}/mcp/server.py`
and three plugin options (`userConfig`), changed with `/plugin configure ingeniero-agentico@ingeniero-agentico`
or at install time with `--config KEY=value`:

| Option | Default | What it is |
|---|---|---|
| `python` | `python` | The command that launches the server. On Windows `python` (if it is on the PATH) or `py`; on macOS and Linux, `python3`; or the absolute path to the executable |
| `data` | empty | Data folder; passed to the server as `INGENIERO_DATOS`. Empty: the server uses the environment variable or the temp folder |
| `roots` | empty | Extra folders the server can read and write (`INGENIERO_MCP_ROOTS`), separated by `;` on Windows and `:` on macOS and Linux |

Version 1.0 called the last two options `datos` and `raices`. After updating to 1.1.0, set them
again with `/plugin configure`.

Example from the terminal: `claude plugin install ingeniero-agentico@ingeniero-agentico --config python=py --config data=D:/ingeniero-agentico-datos`.
The server requires absolute paths inside an allowed root (the plugin, `data`, the work folder and
`roots`): to map the folders of a task with `map_context`, add them to `roots`.

`claude plugin validate .` (from the repo root) checks the manifest; the root `CLAUDE.md` is not
loaded as plugin context (it is for whoever develops the repo, not for whoever uses it).

### Without the plugin

```
python install/install.py --platform claude-code
```

Copies `skills/` to `~/.claude/skills/`, `agents/` to `~/.claude/agents/`, `commands/` to
`~/.claude/commands/` and the profile template to `~/.claude/profiles/_template.yaml`. It respects
`CLAUDE_CONFIG_DIR`. Do not install both routes at once: you would see every skill twice. This route
does not register the MCP server: if you want it, add it with `claude mcp add` (see `docs/MCP.md`).

**What works:** everything. It is the only platform where orchestration was designed and tested with agents.

---

## Claude Desktop and claude.ai

```
python install/install.py --platform claude-desktop
```

Leaves in `install/output/claude-desktop/` (ignored by git):

- one ZIP per skill (`orchestrate.zip`, `procurement.zip`, ...), each with the `<skill>/` folder as
  its only top level, which is what claude.ai requires;
- `ingeniero-agentico-plugin.zip`, the whole plugin in an `ingeniero-agentico/` folder (it includes
  `mcp/`, because `plugin.json` declares the MCP server).

Upload them in one of these ways:

1. **One skill at a time:** Customize > Skills > upload the ZIP, and turn it on.
2. **The whole plugin:** Customize > Plugins > Add > Upload plugin > `ingeniero-agentico-plugin.zip`.
3. **From GitHub:** Customize > Plugins > Add > Add marketplace with the repo URL (claude.ai must be
   able to read the repo; if it cannot, use option 2).

Requirements: Pro, Max, Team or Enterprise plan, with **code execution turned on**: without it the
scripts do not run and the method delivers no numbers.

**What works and what does not:**

| | Chat | Cowork |
|---|---|---|
| Skills and scripts | yes, in the code execution sandbox | yes |
| `commands/` | loaded as a skill (there is no `/new-task`) | yes |
| `agents/` | ignored: `orchestrate` runs **in sequence** | loaded |
| The plugin's MCP server (local) | ignored | starts if the session runs on your computer |
| Data folder | does not exist | the one on your computer, if Cowork runs locally |

**Private data:** the sandbox does not see your disk. Upload the YAML profile and the case files to
the chat and run the scripts with `--profile <path of the uploaded file>`. A single skill's ZIP does
not carry the profile template (the scripts look for it three folders up, outside the skill), so
**always pass `--profile`**: without a profile or template, `financial-evaluation` stops with a
«profile not found» error. For `audit`, pass the scripts with an absolute path. What is generated stays
in the sandbox: download it, because it does not persist between conversations.

**Description length:** claude.ai and the standard accept up to 1,024 characters per skill
`description`. `install.py --test` warns about any skill above that; if an upload is rejected,
shorten that `SKILL.md`.

Sources: [Create custom skills](https://claude.com/docs/skills/how-to) ·
[Plugin structure and testing](https://claude.com/docs/plugins/build) ·
[Plugin support by app](https://claude.com/docs/plugins/platform-support).

---

## Codex (OpenAI)

```
python install/install.py --platform codex
```

- Skills in `~/.agents/skills/` (the user folder Codex reads; Cursor and Gemini read it too).
- Agents converted to TOML in `~/.codex/agents/` (respects `CODEX_HOME`): each one with `name`,
  `description` and `developer_instructions` (the body of the `.md`). No `model`: they inherit the session's.
- Invoked with `$orchestrate` or from `/skills`; Codex also picks a skill by itself from its description.
- When it opens the repo, Codex reads `AGENTS.md` (neutral instructions and the «without agents» mode).

**What works:** skills and scripts in full. Codex launches subagents when the instruction asks for
it, so `orchestrate` can delegate; if it does not, it runs the stages in sequence with the plan's
approval as the gate. `/new-task` does not exist: use `$orchestrate`. The converted agents were not
tested inside Codex; the installer checks that the TOML parses.

**Data:** set `INGENIERO_DATOS` in the environment before opening Codex, or use `~/ingeniero-agentico-datos/`.

Sources: [Skills](https://developers.openai.com/codex/skills) ·
[Subagents](https://developers.openai.com/codex/subagents) ·
[AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

---

## Cursor

```
python install/install.py --platform cursor
```

- Skills in `~/.cursor/skills/`; agents in `~/.cursor/agents/` with only `name` and `description`
  (Claude Code's tools and models are not valid in Cursor, so they inherit the session's).
- Cursor also reads `~/.claude/skills/`, `~/.codex/skills/` and `~/.agents/skills/`: if you already
  installed for Claude Code or Codex, do not repeat (you avoid duplicates).
- Invoked by typing `/orchestrate` in the agent chat. It reads `AGENTS.md` when it opens the repo.

**What works:** skills, scripts and subagents. There is no `/new-task` (Cursor is moving commands
to skills). Not tested inside Cursor.

Sources: [Skills](https://cursor.com/docs/context/skills) ·
[Subagents](https://cursor.com/docs/context/subagents) · [Rules and AGENTS.md](https://cursor.com/docs/context/rules).

---

## Gemini CLI

```
python install/install.py --platform gemini
```

- Skills in `~/.gemini/skills/`; agents in `~/.gemini/agents/` with only `name` and `description`.
- Gemini asks for permission the first time it activates a skill (`activate_skill`): accept it.
- Gemini reads `GEMINI.md`, not `AGENTS.md`. The repo's `GEMINI.md` only imports `AGENTS.md`
  (`@./AGENTS.md`), so there is a single source of instructions.
- Gemini also reads `~/.agents/skills/` (with precedence): if you installed for Codex, it already has them.

**What works:** skills, scripts and subagents (a subagent does not launch another, same as in Claude
Code). No `/new-task`. Not tested inside Gemini.

Sources: [Agent Skills](https://geminicli.com/docs/cli/skills/) ·
[Subagents](https://geminicli.com/docs/core/subagents/) · [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) ·
[Imports](https://geminicli.com/docs/reference/memport/).

---

## Hermes Agent (Nous Research)

```
python install/install.py --platform hermes
```

Copies the skills to `HERMES_HOME/skills/` (on Windows `%LOCALAPPDATA%\hermes\skills\`; on macOS and
Linux `~/.hermes/skills/`; respects `HERMES_HOME`) and the template to `HERMES_HOME/profiles/`. Hermes
searches the whole folder for `SKILL.md`, so no category is needed. Each skill becomes a command:
`/orchestrate`, `/procurement`, etc.

**Alternative without copying** (skills are read from the repo and update with `git pull`): add the
repo's `skills/` folder in `config.yaml`. The installer does not touch `config.yaml`; you edit it:

```yaml
skills:
  external_dirs:
    - <path to the repo>/skills
```

- **Context:** when it opens the repo, Hermes loads a single project file, the first one it finds
  (`.hermes.md`, `AGENTS.md`, `CLAUDE.md`, ...). It loads `AGENTS.md`, not `CLAUDE.md`.
- **Delegation:** Hermes does not read agent files; it delegates with the `delegate_task` tool
  (generic children with `goal` and `context`). `orchestrate` can pass each stage's `agents/` file as
  context, or run in sequence.
- **Curator:** the Hermes curator only maintains skills created by the agent itself; these have
  «no origin mark» and it does not archive them. But if the agent uses `skill_manage` it can edit
  them wherever they are: reinstalling puts them back as they are in the repo.
- **Data:** set `INGENIERO_DATOS` in the system environment (Hermes keeps its `.env` for secrets),
  or pass `--profile`.
- **MCP:** see `docs/MCP.md`.

**What works:** skills and scripts; checked against the installed code (v0.21.4): `get_skills_dir()`
is `HERMES_HOME/skills` and the `SKILL.md` search is recursive.

Sources: [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) ·
[Delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) ·
[Context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files).

---

## Any other agent compatible with Agent Skills

```
python install/install.py --platform agents
```

Copies only the skills to `~/.agents/skills/`, the shared folder Codex, Cursor and Gemini CLI read.
If your agent uses another folder, pass your user folder with `--target` or copy `skills/<name>/`
by hand: each folder is self-contained except for the profile template (which goes in
`<configuration folder>/profiles/_template.yaml`). No subagents: `orchestrate` runs in sequence.

---

## `install.py`

```
python install/install.py --platform <p> [--target <folder>] [--link] [--force]
python install/install.py --platform <p> --uninstall [--target <folder>]
python install/install.py --list [--platform <p>] [--target <folder>]
python install/install.py --test [--no-scripts]
```

| Option | What it does |
|---|---|
| `--target` | Replaces your user folder: installs into `<target>/.claude/...`, `<target>/.agents/...`. Use it to test without touching your configuration. On `claude-desktop` it is the ZIP folder |
| `--link` | Instead of copying, links each skill to the repo (junction on Windows, symlink on macOS and Linux): a `git pull` updates the installation. Agents and commands are copied anyway |
| `--force` | Replaces a same-name skill this installer did not install. Without it, it stops before writing anything |
| `--uninstall` | Removes only what its manifest lists. From a link it removes the link, it never goes into the repo. What it shares with another installation (codex and agents use `~/.agents/skills`) is kept |
| `--list` | What is in the repo and what was installed on each platform |
| `--test` | Installs into a temporary HOME for each platform, checks every `SKILL.md`, the agent formats and the ZIP structure, runs each method's `--test` **from the installed copy**, uninstalls and checks nothing is left |

The version 1.0 Spanish flags (`--plataforma`, `--destino`, `--enlazar`, `--forzar`,
`--desinstalar`, `--listar`, `--probar`, `--sin-scripts`) still work as hidden aliases, and
manifests written by 1.0 are still read.

`--test` runs each method with your real user environment (only `INGENIERO_DATOS` is removed, so
nothing reaches your data folder): the Microsoft Store Python only launches with the real user
profile, and overriding it broke `audit` in 1.0.

It never edits `settings.json`, `config.yaml` or `config.toml`. It leaves a manifest in
`<configuration folder>/.ingeniero-agentico/<platform>.json`.

**What gets installed.** Each whole `skills/<name>/`, with `tests/`, because every `SKILL.md` says
to run `--test` and the auditor uses it to confirm the method works where it landed. Generated files
are excluded: `__pycache__`, `*.pyc` and `outputs/` (also the older `salidas/`). Two additions that
are not inside the skills:

- `profiles/_template.yaml` in `<configuration folder>/profiles/`: the scripts look for it three
  folders above `scripts/`. Without it, `financial-evaluation` does not run, nor does its test.
- `ARCHITECTURE.md` inside `orchestrate/`: `orchestrate`, `research` and `map-context` cite it as
  «repo root», which does not exist in a copy.

### `--test` result (15-10-2026, Windows, Python 3.14.4 and Microsoft Store Python 3.11.9)

```
Installer test (temporary HOME, nothing touches the real configuration)
Each method's script: run with --test from the installed copy

  claude-code        .claude\skills                     OK
  claude-desktop     9 ZIP                              OK
  codex              .agents\skills                     OK
  cursor             .cursor\skills                     OK
  gemini             .gemini\skills                     OK
  hermes             AppData\Local\hermes\skills        OK
  agents             .agents\skills                     OK
  agents --link      junction                           OK
  codex + agents     shared folder                      OK

OK
```

## What does not work on each platform

| Platform | Does not work or changes |
|---|---|
| Claude Code (plugin) | The sibling data folder does not help (use `INGENIERO_DATOS`). Names with the `ingeniero-agentico:` prefix |
| claude.ai chat | No agents (orchestration in sequence). No `/new-task`. No disk: profile and case are uploaded; outputs are downloaded. No profile template in single-skill ZIPs. Without code execution there are no numbers |
| Cowork | Loads agents; the data folder depends on whether the session runs on your computer |
| Codex | No `/new-task` (use `$orchestrate`). Converted agents without their own tools or model |
| Cursor | No `/new-task`. Agents without their own tools or model |
| Gemini CLI | No `/new-task`. Agents without their own tools or model. Asks for permission when activating each skill |
| Hermes | No agent files (delegates with `delegate_task`). Reads `AGENTS.md`, not `CLAUDE.md` |
| Generic `agents` | Skills only: orchestration in sequence |

On all of them, `orchestrate` in sequence does the six stages in the same conversation, with the plan
as the gate (nothing runs before the «yes») and the audit declared «in the same conversation».

## Sources

- Claude Code: [Plugin manifest](https://code.claude.com/docs/en/plugins-reference) ·
  [Create a marketplace](https://code.claude.com/docs/en/plugin-marketplaces) ·
  [Marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference) ·
  [Host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace) ·
  [Skills](https://code.claude.com/docs/en/skills) · [Subagents](https://code.claude.com/docs/en/sub-agents)
- Claude Desktop and claude.ai: [Create custom skills](https://claude.com/docs/skills/how-to) ·
  [Plugin structure and testing](https://claude.com/docs/plugins/build) ·
  [Plugin support by app](https://claude.com/docs/plugins/platform-support)
- Codex: [Skills](https://developers.openai.com/codex/skills) · [Subagents](https://developers.openai.com/codex/subagents) ·
  [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- Cursor: [Skills](https://cursor.com/docs/context/skills) · [Subagents](https://cursor.com/docs/context/subagents) ·
  [Rules](https://cursor.com/docs/context/rules)
- Gemini CLI: [Agent Skills](https://geminicli.com/docs/cli/skills/) · [Subagents](https://geminicli.com/docs/core/subagents/) ·
  [GEMINI.md](https://geminicli.com/docs/cli/gemini-md/) · [Imports](https://geminicli.com/docs/reference/memport/)
- Hermes Agent: [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) ·
  [Delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) ·
  [Context files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) ·
  installed code v0.21.4 (`hermes_constants.py`, `agent/skill_utils.py`)
- Standard: [Agent Skills specification](https://agentskills.io/specification)
