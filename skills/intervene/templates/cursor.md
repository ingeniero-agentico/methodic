# Cursor CLI · what limits the agent

Checked on 16-10-2026 against `cursor.com/docs/cli/reference/permissions`. Only what that page says
is written here; `intervene.py permissions` does not generate a file for Cursor.

## What exists

- Files: `~/.cursor/cli-config.json` (global) and `<project>/.cursor/cli.json` (project).
- A `permissions` object with `allow` and `deny` lists. **Deny wins over allow.**
- Tokens: `Shell(commandBase)` (the first word of the command), `Read(pathOrGlob)`,
  `Write(pathOrGlob)`, `WebFetch(domainOrPattern)`, `Mcp(server:tool)`. Globs take `**`, `*` and
  `?`; relative paths are scoped to the workspace and absolute paths reach outside it.

## How it maps to the scope (a suggestion, not tested here)

```json
{
  "permissions": {
    "allow": ["Read(C:/Users/usuario/Documents/FerreteriaAndes/**)"],
    "deny": [
      "Read(C:/Users/usuario/Documents/FerreteriaAndes/Sueldos/**)",
      "Write(C:/Users/usuario/Documents/FerreteriaAndes/Sueldos/**)",
      "Shell(rm)", "Shell(del)", "Shell(curl)", "Shell(wget)", "Shell(pip)", "Shell(npm)",
      "Shell(winget)", "Shell(choco)", "Shell(msiexec)"
    ]
  }
}
```

## What was not verified

- An **ask** list (prompt before a write in `write_with_ok`): the page shows only allow and deny.
  The OK per action is then a rule of the skill, not of Cursor.
- How a Windows path with a drive letter is written in a rule: the example above follows the page's
  wording ("absolute paths"), not a test.
- `Shell(commandBase)` matches the first word only: `Shell(git)` cannot deny `git push` alone.
