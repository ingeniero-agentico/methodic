# MCP server · the methods in any client

`mcp/server.py` exposes the repo's methods over **MCP** (Model Context Protocol), to use them from
Claude Desktop, Claude Code, Codex, Cursor, Gemini CLI, Hermes Agent or any other MCP client. It is a
single file in standard Python (3.11 or newer), without the `mcp` SDK or any other dependency. It
speaks over **stdio**: the client launches it as a subprocess.

**The server does not compute.** It writes the input to a work folder, runs the method's script with
the same Python that runs the server and returns what the script left (JSON, Excel and assumptions).
The repo rule holds: every number comes from a script.

## What it exposes

### Tools

| Tool | What it does | Writes |
|---|---|---|
| `list_methods` | Each method and stage: what it solves (the first sentence of its `description`), what input it needs, which tool runs it and which options it accepts | No |
| `read_method(method, part)` | The text of `SKILL.md` (`skill`), `GUIDE.md` (`guide`), `GUIA.md` (`guia`, the Spanish guide), `templates/` (`template`) or `SOURCES.md` (`sources`) | No |
| `run_method(method, input, profile?, options?, case?, files?)` | Runs `procurement`, `cost-and-pricing`, `economic-evaluation` or `financial-evaluation`. Returns the output JSON, the Excel paths and the assumptions | Yes, in the work folder |
| `test_method(method)` | Runs the method's `--test` (also for `map-context`, `research` and `audit`) | No |
| `map_context(folders, out, exclude?, core?, mark_read?)` | Runs `skills/map-context/scripts/map_context.py`; returns the MODE, the core files and the path of `MAP.md` | Yes, in `out` |
| `validate_research(path, threshold?)` | Runs `skills/research/scripts/validate_research.py --json` | No |

Details of `run_method`:

- `input` is the case as a JSON object, shaped like the method's template (`read_method` with
  `part: "template"`). English keys are canonical; the Spanish keys of version 1.0 are still accepted
  by the scripts.
- `profile` is a name (looked up in `<data>/profiles/<name>.yaml`, then `<data>/perfiles/`) or the
  absolute path to a `.yaml`. Without a profile, the script applies its own search.
- `options` accepts only a whitelist: `--rate`, `--tax`, `--delta` and `--sweep` in
  `economic-evaluation`; `--rate`, `--tax` and `--project` in `financial-evaluation`. Any other one
  (`--out`, `--profile`, `--test`) is rejected. The 1.0 names (`--tasa`, `--impuesto`, `--barrer`,
  `--proyecto`) are translated.
- `files` carries text files that go with the input, as `{name: content}`; for example, the project
  cash flow CSV of `financial-evaluation`.
- `assumptions` is the method's own list, returned as-is: every method outputs
  `assumptions: [{parameter, value, origin, text}]`, with `origin` one of `input`, `profile`,
  `template`, `default`, `script` or `research:<id>`. An output from before v1.1 brings `supuestos`
  (keys `parametro`, `valor`, `origen`, `marca`): the server normalizes it to the same shape and says
  so in `assumptions_source`.
- Input keys are the English ones of each template (for example, procurement's `rejected`,
  `sale_unit.content`, `printed_subtotal`, `shortest_lead_time`; cost-and-pricing's
  `quantity_sold`, `unit_factor`, `global_markup`, `min_margin_alert`, `exchange_rates`,
  `breakeven`).

Version 1.0 tool and argument names (`listar_metodos`, `correr_metodo`, `metodo`, `entrada`, ...)
are gone from the tool list; the server still translates the old argument names if a client sends them.

### Resources

The `SKILL.md`, `GUIDE.md` and `GUIA.md` of each skill, with URIs `ingeniero://skills/<method>/SKILL.md`,
`ingeniero://skills/<method>/GUIDE.md` and `ingeniero://skills/<method>/GUIA.md` (`resources/list`,
`resources/read`).

## Where the outputs go

The data folder is found in the same order the scripts use:

1. `--data <folder>` when launching the server;
2. the `INGENIERO_DATOS` environment variable;
3. the sibling folder `../ingeniero-agentico-datos/`.

Each run lands in `<base>/<case>/<method>-<YYYYMMDD-HHMMSS>-<id>/`, with `input.json` and whatever
the script wrote. The base is, in order:

1. `--work <folder>`, if given;
2. `<data>/cases/` (or the older `<data>/casos/` if that is the one that exists), if there is a data folder;
3. `<user temp>/ingeniero-agentico-mcp/`.

**Never inside the repo.** The server refuses to start if the work folder falls inside the repo.

## Security

- **Paths.** Every path that arrives in an argument must be absolute, cannot contain `..` and must
  fall inside an allowed root:
  - it can **read** from the repo, the data folder, the work folder and the extra roots
    (`--root <folder>`, repeatable, or `INGENIERO_MCP_ROOTS` with folders separated by `;` on
    Windows or `:` on macOS and Linux; the 1.0 name `INGENIERO_MCP_RAICES` still works);
  - it can **write** to the same ones, except the repo.

  To map the folders of a task with `map_context`, those folders must be in a root. The input fields
  the script opens as a file (`profile`, and `project_flow` in `financial-evaluation`) go through the
  same validation.
- **Processes.** Each script runs with `sys.executable`, without `shell=True` and with standard input
  closed. There is a maximum time per run (`--max-time`, 300 s by default); past it, the process is
  stopped. `notifications/cancelled` stops it too.
- **Sizes.** The input and its files weigh at most 2 MB. A response has at most `--max-response`
  characters (40,000 by default, about 10,000 tokens): if the JSON does not fit, its path is returned.
- **Text is data.** What the server reads from a file is returned as content; it is never interpreted
  as an instruction.
- **Errors.** An unknown tool answers with the JSON-RPC error `-32602`. A badly given argument
  (unknown method, path with `..`, option not allowed) answers with an `isError: true` result and the
  reason, so the model can correct itself.

## Protocol

The server serves clients of **both MCP eras**:

- **Modern, 2026-07-28** (the current revision on 15-10-2026). There is no handshake. Every request
  carries `_meta["io.modelcontextprotocol/protocolVersion"]` and
  `_meta["io.modelcontextprotocol/clientCapabilities"]`. The server answers `server/discover`, puts
  `resultType: "complete"` and `serverInfo` in every result, and `ttlMs`/`cacheScope` in the lists. A
  version it does not support answers `-32022` with the list of versions it does.
- **Legacy, 2025-11-25, 2025-06-18, 2025-03-26 and 2024-11-05.** `initialize`, then
  `notifications/initialized` and `ping`. If the client asks for a version it does not know, it
  answers with 2025-11-25.

One JSON-RPC message per line (UTF-8). Only protocol goes to stdout; notices go to stderr.

Sources (read on 15-10-2026):

- Current specification: https://modelcontextprotocol.io/specification/2026-07-28
- Changes from 2025-11-25: https://modelcontextprotocol.io/specification/2026-07-28/changelog
- Versions and compatibility between eras: https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning
- `_meta` and error codes: https://modelcontextprotocol.io/specification/2026-07-28/basic/index
- `server/discover`: https://modelcontextprotocol.io/specification/2026-07-28/server/discover
- stdio transport: https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio
- Tools and resources: https://modelcontextprotocol.io/specification/2026-07-28/server/tools ·
  https://modelcontextprotocol.io/specification/2026-07-28/server/resources
- Legacy handshake: https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle

## Before configuring a client

1. **Python 3.11 or newer** and `openpyxl` (`python -m pip install -r requirements.txt`, the
   tested version); the scripts use it for the Excel file.
2. Check that it starts and see which roots it ended up with:

   ```
   python <path-to-repo>/mcp/server.py --check
   ```

3. End-to-end test (ends in `OK`):

   ```
   python <path-to-repo>/mcp/test_server.py
   ```

In the examples, `<path-to-repo>` is the absolute path of this repo and `<path-to-data>` that of your
data folder (the one with `profiles/` and `cases/`). If you have no data folder, delete the `env`
block and the outputs will go to the temp folder.

**On Windows:**

- In JSON, write paths with forward slashes (`D:/projects/ingeniero-agentico`) or with a double
  backslash (`D:\\projects\\ingeniero-agentico`).
- If `python` is not on the client's PATH (or opens the Microsoft Store), put the absolute path to
  `python.exe` in `command`, or use `"command": "py"` with `"args": ["-3", "<path-to-repo>/mcp/server.py"]`.

**On macOS and Linux**, the command is usually `python3`.

The ready-made templates are in `mcp/examples/`. `test_server.py` reads each one and launches the
server the way the client would.

## Configuration per client

### Claude Desktop

- File `claude_desktop_config.json`; open it from Settings → Developer → Edit Config.
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Add the entry under `mcpServers` and restart the application completely.
- Template: `mcp/examples/claude-desktop.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "command": "python",
      "args": ["<path-to-repo>/mcp/server.py"],
      "env": { "INGENIERO_DATOS": "<path-to-data>" }
    }
  }
}
```

Logs go to `%APPDATA%\Claude\logs\mcp-server-ingeniero-agentico.log` (macOS: `~/Library/Logs/Claude/`).
Source: https://modelcontextprotocol.io/docs/develop/connect-local-servers

### Claude Code

By command (everything after `--` passes untouched to the server):

```
claude mcp add --transport stdio --scope project ingeniero-agentico -- python <path-to-repo>/mcp/server.py
```

- `--scope project` writes `.mcp.json` at the project root. `local` (the default) and `user`
  write to `~/.claude.json`.
- To pass the data folder, add `--env INGENIERO_DATOS=<path-to-data>` before `--transport`. If the
  server name comes right after `--env`, the CLI reads it as another `KEY=value` pair.
- `claude mcp list` shows the status and `claude mcp get ingeniero-agentico` the details. The first
  time it is used, a server from `.mcp.json` asks for approval in the interactive session.
- `.mcp.json` accepts `${VAR}` and `${VAR:-default}`.
- `.mcp.json` template: `mcp/examples/claude-code.mcp.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "type": "stdio",
      "command": "python",
      "args": ["<path-to-repo>/mcp/server.py"],
      "env": { "INGENIERO_DATOS": "<path-to-data>" }
    }
  }
}
```

Source: https://code.claude.com/docs/en/mcp

### Codex (OpenAI)

- File `~/.codex/config.toml`, or `.codex/config.toml` in a project marked as trusted.
- Section `[mcp_servers.<name>]`.
- By command: `codex mcp add ingeniero-agentico --env INGENIERO_DATOS=<path-to-data> -- python <path-to-repo>/mcp/server.py`.
- Template: `mcp/examples/codex.config.toml`.

```toml
[mcp_servers.ingeniero-agentico]
command = "python"
args = ["<path-to-repo>/mcp/server.py"]
startup_timeout_sec = 20
tool_timeout_sec = 300

[mcp_servers.ingeniero-agentico.env]
INGENIERO_DATOS = "<path-to-data>"
```

`tool_timeout_sec` is 60 by default; `map_context` over large folders can take longer, so the
template raises it to 300. In TOML, a Windows path in double quotes needs `\\`: use `/` or single quotes.
Source: https://developers.openai.com/codex/mcp (redirects to https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

### Cursor

- File `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global). Restart Cursor after changing it.
- Accepts `${workspaceFolder}`, `${userHome}` and `${env:NAME}`.
- Template: `mcp/examples/cursor.mcp.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "type": "stdio",
      "command": "python",
      "args": ["<path-to-repo>/mcp/server.py"],
      "env": { "INGENIERO_DATOS": "<path-to-data>" }
    }
  }
}
```

Source: https://cursor.com/docs/context/mcp

### Gemini CLI

- File `~/.gemini/settings.json` (user) or `.gemini/settings.json` (project).
- Key `mcpServers`. `timeout` is in milliseconds (600000 by default).
- By command: `gemini mcp add -s user -e INGENIERO_DATOS=<path-to-data> ingeniero-agentico python <path-to-repo>/mcp/server.py`.
  The default scope is `project`. Server arguments that start with a hyphen go after `--`.
- `/mcp` shows the status.
- Template: `mcp/examples/gemini.settings.json`.

```json
{
  "mcpServers": {
    "ingeniero-agentico": {
      "command": "python",
      "args": ["<path-to-repo>/mcp/server.py"],
      "env": { "INGENIERO_DATOS": "<path-to-data>" },
      "timeout": 300000
    }
  }
}
```

Source: https://geminicli.com/docs/tools/mcp-server/ (the notice on that page says that since
18-06-2026 Antigravity CLI replaces Gemini CLI on the free plan and on Google One).

### Hermes Agent (Nous Research)

- The `config.yaml` file in the Hermes folder:
  - Windows: `%LOCALAPPDATA%\hermes\config.yaml`
  - Linux and macOS: `~/.hermes/config.yaml`
- Key `mcp_servers`. If it already exists, add the entry to it.
- Template: `mcp/examples/hermes.config.yaml`.

```yaml
mcp_servers:
  ingeniero-agentico:
    command: "python"
    args: ["<path-to-repo>/mcp/server.py"]
    env:
      INGENIERO_DATOS: "<path-to-data>"
    enabled: true
    timeout: 300          # seconds per tool call
    connect_timeout: 60   # seconds to start and list tools
```

- By command:
  `hermes mcp add ingeniero-agentico --command python --env INGENIERO_DATOS=<path-to-data> --args <path-to-repo>/mcp/server.py`.
  `--args` goes last, because it takes everything that follows.
- `hermes mcp test ingeniero-agentico` tests the connection and `/reload-mcp` reloads the configuration.
- Tools show up as `mcp__ingeniero_agentico__<tool>`.
- The `protocol` key (`auto`, the default, `stateless` or `legacy`) picks the era. With `auto` it
  tries `initialize` first, and this server answers it.

Sources: https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference. Also checked in
the installed Hermes Agent code: `tools/mcp_tool_config.py` reads `mcp_servers`,
`tools/mcp_tool_transport.py` uses `command`, `args`, `env` and `cwd`, and `hermes_cli/subcommands/mcp.py`
defines `hermes mcp add`.

### Summary

| Client | Configuration file | Template | Source |
|---|---|---|---|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` · `~/Library/Application Support/Claude/claude_desktop_config.json` | `claude-desktop.json` | modelcontextprotocol.io/docs/develop/connect-local-servers |
| Claude Code | `.mcp.json` (project) · `~/.claude.json` (local, user) | `claude-code.mcp.json` | code.claude.com/docs/en/mcp |
| Codex | `~/.codex/config.toml` · `.codex/config.toml` | `codex.config.toml` | developers.openai.com/codex/mcp |
| Cursor | `.cursor/mcp.json` · `~/.cursor/mcp.json` | `cursor.mcp.json` | cursor.com/docs/context/mcp |
| Gemini CLI | `.gemini/settings.json` · `~/.gemini/settings.json` | `gemini.settings.json` | geminicli.com/docs/tools/mcp-server |
| Hermes Agent | `%LOCALAPPDATA%\hermes\config.yaml` · `~/.hermes/config.yaml` | `hermes.config.yaml` | hermes-agent.nousresearch.com/docs/reference/mcp-config-reference |

Any other MCP client with stdio works the same: command `python`, argument `<path-to-repo>/mcp/server.py`
and, if needed, the `INGENIERO_DATOS` variable.

## Server options

| Option | What it does |
|---|---|
| `--data <folder>` | Data folder (`profiles/` and `cases/`). Wins over `INGENIERO_DATOS` and the sibling folder |
| `--work <folder>` | Where the runs go. Wins over the data folder |
| `--root <folder>` | Extra read and write root (repeatable). Also `INGENIERO_MCP_ROOTS` |
| `--max-time <s>` | Maximum seconds per script run (300) |
| `--max-response <n>` | Maximum characters of a response (40,000) |
| `--check` | Shows the configuration, the tools and the resources, then exits |

The 1.0 flags (`--datos`, `--trabajo`, `--raiz`, `--tiempo-max`, `--max-respuesta`, `--comprobar`)
are still accepted as hidden aliases.

## Known limits

- **The default profile is chosen by the script.** Without `profile`, each script searches on its own
  in `INGENIERO_DATOS` and in the sibling folder `../ingeniero-agentico-datos/`, even if the server
  was launched with another `--data`. To avoid depending on that, pass `profile` explicitly.
- **Roots are fixed when the server starts.** It does not use the client's *roots* (revision
  2026-07-28 deprecated them): a new folder is added with `--root` and restarting the server.
- **A run blocks until it finishes.** It does not use the tasks extension or report progress. The
  default maximum time is 300 s, and some clients cut earlier (Codex, 60 s by default).
- **`audit` is only tested.** `rerun.py` compares archived runs and is driven by the auditor agent;
  it has no tool of its own in the server.
- **No HTTP.** Only stdio, the transport every client in the table launches.
