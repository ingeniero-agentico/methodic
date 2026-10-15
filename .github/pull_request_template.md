## What this changes

<!-- One or two sentences. Which skill, script or document, and why. -->

## Security checklist

Every box is a claim the reviewer will check. Leave a box unticked and say why if it does not apply.

- [ ] `python security/scan.py` reports **0 HIGH** on this branch (CI runs it too).
- [ ] No script in `skills/`, `mcp/` or `install/` touches the network, a shell (`shell=True`, `os.system`), `eval`/`exec`, pickle, or the user's home and config folders. If one must, `security/allowlist.json` has an entry with the reason.
- [ ] No new URL outside `doc_domains` in `security/policy.json`, and no fetch-and-run instruction (`curl … | sh`, `iex (irm …)`).
- [ ] `SKILL.md`, agent and command files contain no instruction to hide something from the user, send data anywhere, or read credentials, tokens, `.env`, `~/.ssh`, browser profiles or agent config.
- [ ] Agent `tools:` lines stay within the role allowlist in `security/policy.json` (no new agent without an entry there).
- [ ] Zero real data: no real company, client, supplier, person, RUT, plate, email, phone, price or local path. Examples use the fictitious cases.
- [ ] No `.env`, key, certificate, Excel, PDF, ZIP, `context/` folder or company profile added.
- [ ] `python security/manifest.py write` was run and `security/MANIFEST.sha256` is part of this PR if distributable files changed; the manifest diff lists only the files this PR says it changes.
- [ ] Every changed script still ends its `--test` in `OK` (`python security/run_tests.py`).
- [ ] Workflows (if touched): `permissions: contents: read`, actions pinned by full commit SHA, no `pull_request_target`, no secrets.

## Not a vulnerability report

Security problems are reported privately, never in a PR or issue: see `SECURITY.md`.
