# Security policy

`ingeniero-agentico` ships skills, agents, commands, an installer and an MCP server that other
people's AI agents load and run. The owner's rule is short: **nobody slips malicious skills or code
into the source or into an installed copy, nothing in the repo helps anyone exploit an account,
and no data leaks from the repository.** This file says what we defend against, how, what the owner
must switch on in GitHub, and how to report a problem.

## Report a vulnerability

**Never in a public issue, PR, discussion or commit message.** That includes a malicious skill, a
prompt injection that works, a leaked secret or leaked private data.

- While the repo is **public**: use **Security → Report a vulnerability**
  (`https://github.com/ingeniero-agentico/ingeniero-agentico/security/advisories/new`). Only the
  owner sees it.
- While the repo is **private**, private vulnerability reporting does not exist (GitHub offers it for
  public repositories only); collaborators write to the owner directly through GitHub
  (`@camiloalonsomerino-spec`), with the file, the line and what it lets an attacker do, and no copy of
  the leaked datum itself.

Expect an answer within 7 days. A leaked secret is revoked first and removed from history second.

## Threat model

| # | Threat | How it would happen | Controls | What remains |
|---|---|---|---|---|
| T1 | Malicious PR | A contributor adds a script that phones home, a `shell=True`, an obfuscated payload, or a SKILL.md line that tells the agent to send data | `security/scan.py` in CI and in the hooks (network, execution, obfuscation, hidden Unicode, injection rules); CODEOWNERS; PR checklist; workflows never run fork code with a write token or secrets | Logic that looks honest and computes a wrong number: only review and the `--test` cases catch it |
| T2 | Poisoned skill | A SKILL.md, agent or command gains hidden instructions (white text, HTML comments, bidi or tag characters), a `hooks:` frontmatter, an agent gains tools beyond its role, the plugin gains `hooks`, `monitors`, `bin/` or a foreign MCP server | `inject-*`, `unicode-*`, `agent-*` rules; per-agent tool allowlist in `security/policy.json`; plugin and marketplace checks; `claude plugin validate` in CI | A new attack phrasing the patterns do not know: the rules are a list, not understanding |
| T3 | Tampered install copy | Someone (or a program) edits the files in `~/.claude/skills`, `~/.agents/skills`, the plugin cache, or the source tree before installing | `security/MANIFEST.sha256` + `security/manifest.py`; the installer refuses a tree that does not verify (see below); `verify_copy` checks an installed copy | Malware that rewrites the files **and** the manifest **and** `manifest.py` on your machine: the manifest is only as trusted as the commit it came from (see "Trust anchor") |
| T4 | Prompt injection via researched web pages | A page the `researcher` agent reads says "ignore your instructions and…" | Only `researcher` has `WebFetch`/`WebSearch`; its output is data (`research-data.json`) validated by `validate_research.py` (one figure per gap with source, date and A–D reliability); executors never fetch; scripts never touch the network; no agent may hide anything from the user | The model reading the page can still be influenced while it reads it. Treat every fetched page as data, never as instructions (the researcher guide must say so explicitly) |
| T5 | Data leakage | A real company, client, supplier, RUT, plate, email, price or local path ends up in a commit, an example, a test or a file name | `private-*` rules (RUT with valid check digit, plates, emails, phones, user paths), the **private denylist** (below), `file-*` rules (no `.env`, keys, Excel/PDF/ZIP, `context/`, company profiles), gitleaks over the full history in CI | A real datum that matches no pattern and is not in the denylist. Keep the denylist current |
| T6 | MCP abuse | An agent uses the MCP server to read or write outside the task, or to run arbitrary code | The server runs only the repo's own scripts, with an allowlist of options per method, inside declared read/write roots (`mcp/server.py`); the plugin declaration must be `python ${CLAUDE_PLUGIN_ROOT}/mcp/server.py` and nothing else (`agent-plugin-mcp`) | Whatever the roots you pass with `--root` contain is readable by the agent |

## Controls

### `security/scan.py` (the primary gate)

Standard library only. `python security/scan.py` scans what git would take (tracked plus untracked
not ignored); `--staged` scans the staged version (pre-commit); `--all-files` walks a folder;
`--json` for machines; `--list-rules` prints every rule; `--test` seeds one sample of each finding
class in a temporary tree, checks that each is detected, that the report masks every secret and
private term, that the allowlist works, and that a clean sample produces nothing.

**HIGH blocks (exit 1).** MEDIUM is printed for review. LOW is counted.

- **No script in `skills/`, `mcp/` or `install/` touches the network.** Imports of `socket`,
  `urllib.request`, `http.client`, `requests`, `httpx`, `aiohttp`, `ftplib`, `smtplib`,
  `webbrowser` and friends, and subprocess calls to `curl`, `wget`, `Invoke-WebRequest`, `iwr`,
  `irm`, `bitsadmin`, `certutil -urlcache` are HIGH. `urllib.parse` is not network and is fine.
- Dynamic execution (`eval`, `exec`, `compile`, `__import__`), `os.system`, `shell=True`,
  pickle/marshal/shelve loads, `ctypes`, recursive deletes of variable paths, references to
  credentials and agent config (`~/.ssh`, `.env`, `.claude.json`, browser profiles) or persistence
  targets (`settings.json`, `.bashrc`, crontab, Run keys) in distributable code.
- Obfuscation: long base64/hex blobs, rot13, decode-and-exec chains, minified lines.
- Hidden Unicode in any text file: bidi controls, zero-width characters, tag and variation-selector
  payloads, mixed-script identifiers.
- Prompt injection in instruction files (`SKILL.md`, agents, commands, guides, `AGENTS.md`,
  `ARCHITECTURE.md`, `docs/`): override phrases, secrecy towards the user, exfiltration,
  fetch-and-run, pointers to credentials, hidden HTML, URLs outside `doc_domains`.
- Secrets (AWS, GCP, Azure, GitHub, Anthropic, OpenAI, Slack, private keys, JWTs, high-entropy
  `KEY=value`, passwords in URLs) and private data. **Nothing matched is ever printed in full**:
  findings show `file:line` and a masked hint.

Exceptions go in `security/allowlist.json`: `rule`, `path` glob, optional `match`, and a mandatory
`reason`. An entry without a reason fails the scan. It ships empty. Policy (documentation domains,
agent tool allowlists, documented install targets, fixtures) lives in `security/policy.json`. Both
files are covered by CODEOWNERS and by the manifest.

### The private denylist

`ingeniero-agentico-datos/security/denylist.txt`, **outside the repo**, one term per line: the real
company, people, suppliers, clients, RUTs and case names of the private cases. The scanner reads it
from `--denylist`, else `$INGENIERO_DATOS/security/denylist.txt`, else the sibling folder
`../ingeniero-agentico-datos/security/denylist.txt`. Matching is case- and accent-insensitive, on whole
words, in file contents and file names. It never prints a term: only `file:line` and the first letter
with the length. A denylist found inside the scanned tree is itself a HIGH finding. CI has no copy
(by design): the hooks on the owner's machine are where it acts.

### `security/manifest.py` and `security/MANIFEST.sha256`

SHA-256 of every distributable file: `skills/`, `agents/`, `commands/`, `mcp/`, `install/`,
`.claude-plugin/`, `profiles/_template.yaml`, `ARCHITECTURE.md`, `AGENTS.md`, and the checker itself
(`security/scan.py`, `security/manifest.py`, `security/policy.json`, `security/allowlist.json`).
Generated files are excluded with exactly the patterns the installer excludes; if
`install/platforms.json` ever excludes more, `verify` fails, because a file the manifest ignores
but the installer copies would be unverified. Text files are hashed with CRLF normalised to LF, so a
Windows checkout verifies like a Linux one.

```
python security/manifest.py write     # after any change to a distributable file; commit the manifest with it
python security/manifest.py verify    # exit 1 on any added, removed or changed file
```

**The installer refuses to install from a tree whose manifest does not verify, and `--force` never
bypasses it.** `--force` only allows overwriting a previous installation; it has no say over
integrity. The installer calls `verify_tree(repo)` before copying anything, and `verify_copy` on
what it copied. The MCP server calls `verify_tree` on the folder it serves from before it accepts a
tool call. If a check fails, the message lists the files; the fix is to restore them from git or,
if the change is yours, regenerate the manifest and commit it.

**Trust anchor.** The manifest proves that a tree matches the manifest next to it. It does not
prove the manifest is the owner's: anyone who can rewrite both on your disk wins. What makes a
manifest trustworthy is the reviewed commit it came from (CI, CODEOWNERS, and optionally signed
commits or tags). Install from a clone of the official repository, at a commit that passed CI.

### Git hooks (`.githooks/`)

```
git config core.hooksPath .githooks
```

Once per clone. `pre-commit` scans the staged files (denylist included when it is found) and blocks
on HIGH; it also reminds you to regenerate the manifest when distributable files change.
`pre-push` exports every commit being pushed (`git archive`) to a temporary folder, scans it in
full and verifies its manifest; it blocks on any HIGH finding or mismatch. Both work in Git for
Windows (`sh`) and on macOS and Linux, and look for `py -3`, `python3` or `python` (3.11 or newer).
`git commit --no-verify` skips the hooks: CI is the backstop, and it is only a gate where GitHub
enforces required checks (see the settings below).

### CI (`.github/workflows/`)

- `security.yml`: the scanner and manifest on Linux, Windows and macOS with Python 3.11 and 3.13;
  **gitleaks** 8.30.1 (checksum-verified binary) over the full history as a second secrets layer;
  **`claude plugin validate .`** with Claude Code 2.1.292 installed by exact version from npm; and
  `skills-ref validate` (the Agent Skills reference validator, pinned to a commit; informational,
  because its own README says it is for demonstration only).
- `tests.yml`: every `--test` (`security/run_tests.py`), `mcp/test_server.py` and
  `install/install.py --test`, same matrix, openpyxl installed with `--require-hashes`.
- Both: `permissions: contents: read` at the top, triggers `push` (main) and `pull_request` only,
  never `pull_request_target`, no secrets, every action pinned by full commit SHA, checkout with
  `persist-credentials: false`. The scanner itself fails a workflow that breaks any of these
  (`agent-workflow`).
- `dependabot.yml` proposes updates for the pinned actions and the hashed pip requirements.

Cost note: GitHub Actions is free on public repositories with standard runners. On a private
repository the plan includes 2,000 minutes a month, and macOS minutes are billed at about ten times
the Linux rate ($0.062 against $0.006 per minute,
https://docs.github.com/en/billing/concepts/product-billing/github-actions): the macOS legs are the
expensive ones while the repo is private.

## GitHub settings the owner must enable

The repo lives in the organization **`ingeniero-agentico`** (owner and only member:
`camiloalonsomerino-spec`), on the **GitHub Free** plan for organizations. Availability is marked:

- **FREE** = available on Free, private repository included.
- **PUBLIC** = available free only once the repository is public.
- **PAID** = on a private repository it needs GitHub Team (or Enterprise); free once public where noted.

Plain answer: **while the repository is private on Free, GitHub enforces almost nothing for you.**
Branch protection, rulesets, required reviews and code owners are listed under GitHub Team for
private repositories (https://docs.github.com/en/get-started/learning-about-github/githubs-plans);
secret scanning on private organization repositories needs GitHub Secret Protection on Team or
Enterprise (https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning);
private vulnerability reporting is for public repositories
(https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository).
Until the repo is public (or on Team), the local hooks and the installer's manifest check are the
real gates, and CI is a signal you read, not a lock.

### Organization level (Organization → Settings)

Path to every item: profile picture → **Organizations** → `ingeniero-agentico` → **Settings**.

| Setting | Where and what to choose | Availability | Docs |
|---|---|---|---|
| Members: only the owner | **People**: one member, `camiloalonsomerino-spec`, role Owner. Invite nobody else; add contributors per repository, never as org members | FREE | https://docs.github.com/en/organizations/managing-membership-in-your-organization |
| Require 2FA | **Authentication security** → "Require two-factor authentication for everyone in your organization" → Save | FREE ("Two-factor authentication enforcement" is in Free for organizations) | https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization |
| Base permissions: No permission | **Member privileges** → Base permissions → **No permission** → confirm | FREE | https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization |
| Members cannot create repositories | **Member privileges** → Repository creation → uncheck Public and Private → Save | FREE | https://docs.github.com/en/organizations/managing-organization-settings/restricting-repository-creation-in-your-organization |
| No forks of private repositories | **Member privileges** → Repository forking → leave "Allow forking of private repositories" **unchecked** (the default for new organizations) | FREE | https://docs.github.com/en/organizations/managing-organization-settings/managing-the-forking-policy-for-your-organization |
| Actions: only the pinned actions | **Actions → General → Policies** → "Allow ingeniero-agentico, and select non-ingeniero-agentico, actions and reusable workflows" → uncheck "Allow actions created by GitHub" and "Allow Marketplace actions by verified creators" → in "Allow or block specified actions and reusable workflows" put `actions/checkout@*, actions/setup-python@*, actions/setup-node@*` → check **"Require actions to be pinned to a full-length commit SHA"** → Save. (The `@*` pattern plus the SHA requirement lets Dependabot bumps through without reopening the list; to freeze exact commits instead, list `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1, actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97, actions/setup-node@820762786026740c76f36085b0efc47a31fe5020`) | FREE (the docs state no plan restriction) | https://docs.github.com/en/organizations/managing-organization-settings/disabling-or-limiting-github-actions-for-your-organization |
| Default workflow permissions read-only | **Actions → General → Workflow permissions** → "Read repository contents and packages permissions" (the restricted setting); leave "Allow GitHub Actions to create and approve pull requests" **unchecked** → Save | FREE | same page |
| Approval for workflows from outsiders (public repos) | **Actions → General → Approval for running fork pull request workflows from contributors** → **"Require approval for all external contributors"** (GitHub's name for people who are not members of the organization; there is no option literally called "outside collaborators") | PUBLIC (applies to public repositories) | same page |
| Fork PR workflows (private repos) | **Actions → General → Fork pull request workflows**: leave "Run workflows from fork pull requests" **unchecked**; if you ever enable it, keep "Send write tokens…" and "Send secrets…" unchecked and check "Require approval for fork pull request workflows" | FREE (private repositories only) | same page |
| Third-party access | **Third-party Access → OAuth application policy**: keep access restricted; approve nothing you did not install yourself. Review **GitHub Apps** installed on the org | FREE | https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/about-oauth-app-access-restrictions |

### Repository level (`ingeniero-agentico/ingeniero-agentico` → Settings)

| Setting | Where and what to choose | Availability | Docs |
|---|---|---|---|
| Ruleset on `main` | **Rules → Rulesets → New ruleset → New branch ruleset**: name `main`, Enforcement **Active**, target "Include default branch"; rules **Restrict deletions**, **Block force pushes**, **Require a pull request before merging** (with "Require review from Code Owners"), **Require status checks to pass before merging** with the checks of `security` and `tests` (add them after their first run), optionally **Require signed commits**. Bypass list: see the note below | PAID on private · FREE once public | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository |
| (Alternative) Branch protection on `main` | **Branches → Add branch protection rule** with the same choices | PAID on private · FREE once public | https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches |
| CODEOWNERS enforced | `.github/CODEOWNERS` is in the repo; it takes effect through the ruleset's "Require review from Code Owners" | PAID on private · FREE once public | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners |
| Secret scanning + push protection | **Advanced Security** → Secret Protection: **Enable**, then Push protection: **Enable** | PUBLIC (free on public repositories) · PAID on private (Secret Protection on Team or Enterprise) | https://docs.github.com/en/code-security/secret-scanning/enabling-secret-scanning-features/enabling-push-protection-for-your-repository |
| Push protection for yourself | Personal **Settings → Code security → Push protection for yourself**: keep it enabled (on by default). It blocks your pushes of secrets to **public** repositories | FREE (protects pushes to public repos) | https://docs.github.com/en/code-security/secret-scanning/working-with-secret-scanning-and-push-protection/push-protection-for-users |
| Private vulnerability reporting | **Advanced Security → Private vulnerability reporting → Enable** | PUBLIC only | https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository |
| Dependabot alerts and security updates | **Advanced Security → Dependabot alerts: Enable; Dependabot security updates: Enable**. Version updates come from `.github/dependabot.yml` | FREE | https://docs.github.com/en/code-security/dependabot |
| Actions in the repository | **Actions → General**: the org policy applies; check that Workflow permissions show read-only and "Require approval for all external contributors" once public | FREE | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository |
| Collaborators | **Collaborators and teams**: add outside contributors with **Read** or **Triage** only; nobody else gets Write, Maintain or Admin | FREE | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository |

**Note on the sole owner.** GitHub does not let the author of a pull request approve it, and a
code owner's own PR does not count as code-owner review. With one maintainer, "Require review from
Code Owners" blocks every PR of the owner unless the owner is on the ruleset's **bypass list**
("Organization admin", mode "For pull requests only"). That keeps force-push and deletion blocked and
the status checks visible, while outside PRs still need the owner's review.

## Wiring for the installer and the MCP server

```python
import sys
sys.path.insert(0, str(REPO / "security"))
from manifest import verify_tree, verify_copy

ok, problems = verify_tree(REPO)               # install.py: before copying anything, --force or not
ok, problems = verify_copy(dest, "skills/<name>/", REPO)   # install.py: after each copy
ok, problems = verify_tree(REPO, parts=("skills/", "agents/", "commands/", "mcp/", ".claude-plugin/"))
                                                # mcp/server.py at start-up (plugin ZIPs ship only these parts)
```

## What this does not do

- It does not understand intent: a script that computes a plausible wrong figure passes every rule.
- It does not stop a determined local attacker who can rewrite the repo, the manifest and the
  checker on your own disk.
- While the repository is private on GitHub Free, nothing on GitHub prevents a direct push to
  `main`; the hooks and your own review do.
