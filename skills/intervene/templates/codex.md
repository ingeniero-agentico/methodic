# Codex · what limits the agent

Checked on 16-10-2026 against the Codex documentation (`developers.openai.com/codex/config-reference`
and `developers.openai.com/codex/rules`, which now redirect to `learn.chatgpt.com/docs/`). Only what
those pages say is written here; `intervene.py permissions` does not generate a file for Codex.

## What exists

- **Sandbox** (`~/.codex/config.toml`): `sandbox_mode = "read-only" | "workspace-write" |
  "danger-full-access"`. With `workspace-write`, `sandbox_workspace_write.network_access` turns
  outbound network on or off and `sandbox_workspace_write.writable_roots` adds writable folders.
- **Approvals**: `approval_policy = "on-request" | "never"` (or a `granular` table).
- **Rules** (experimental, per the page): `.rules` files under `~/.codex/rules/` with
  `prefix_rule(pattern = [...], decision = "allow" | "prompt" | "forbidden")`. They control commands
  that run **outside the sandbox**; the most restrictive matching decision applies.

## How it maps to the scope (a suggestion, not tested here)

| Scope | Closest Codex setting |
|---|---|
| `write_with_ok` | `sandbox_mode = "workspace-write"` with those folders in `writable_roots`, and `approval_policy = "on-request"` |
| work folder | start Codex in it, or add it to `writable_roots` |
| no network | `sandbox_workspace_write.network_access = false` |
| deletions, installs, `git push` | `prefix_rule(..., decision = "forbidden")` for each command |

## What was not verified

- A per-path **read** deny (the `never` list): the pages read do not show one. There, the skill's
  rules and `intervene.py check` are the only barrier for reading.
- Whether `writable_roots` asks before each write: it allows; the OK per action stays a rule of the
  skill.
