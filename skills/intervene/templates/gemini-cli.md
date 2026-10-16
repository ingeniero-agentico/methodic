# Gemini CLI · what limits the agent

Checked on 16-10-2026 against `geminicli.com/docs/reference/configuration/` and
`geminicli.com/docs/reference/policy-engine/`. Only what those pages say is written here;
`intervene.py permissions` does not generate a file for Gemini CLI.

## What exists

- Settings: `~/.gemini/settings.json` (user) and `.gemini/settings.json` (project). Keys
  `tools.exclude` (tools removed from discovery), `tools.core` (allowlist of built-in tools),
  `tools.confirmationRequired` (always ask) and `tools.sandbox` with `tools.sandboxNetworkAccess`
  (default `false`).
- **Policy engine**: `.toml` files in `~/.gemini/policies/`, one `[[rule]]` per rule with
  `toolName`, `commandPrefix` (for `run_shell_command`), `argsPattern`, `decision`
  (`allow` · `deny` · `ask_user`) and `priority` (0 to 999).

```toml
[[rule]]
toolName = "run_shell_command"
commandPrefix = "rm"
decision = "deny"
priority = 100
```

## How it maps to the scope (a suggestion, not tested here)

| Scope | Closest Gemini CLI setting |
|---|---|
| deletions, network, installs, `git push` | one `deny` rule per command prefix |
| `write_with_ok` | `tools.confirmationRequired` with the file-writing tool, so each write asks |
| no web | `tools.exclude` with the web tools |

## What was not verified

- A per-path **read** deny (the `never` list): the pages read do not show one. There, the skill's
  rules and `intervene.py check` are the only barrier for reading.
- A prefix such as `rm` may also match `rmdir` (prefix matching); the page does not say so either way.
- The page describes the project-level policy tier as not working yet: use the user folder.
