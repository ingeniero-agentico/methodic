# Intervene · sources

The method is cited; no standard is reproduced.

## Where each rule comes from

| Rule of the skill | Source |
|---|---|
| Plan, approval, implementation and review of each change; one approval per change | ITIL 4, change enablement practice (assessing and authorizing a change before it is made, and recording it) |
| Read only the authorized folders, write freely only in the work area | Least privilege: NIST SP 800-53 Rev. 5, control AC-6; Saltzer and Schroeder's design principles |
| Deny unless listed (anything not under `read` is out of scope) | Fail-safe defaults (Saltzer and Schroeder) |
| Judge the requested path and the path it resolves to | Complete mediation (Saltzer and Schroeder); CWE-22 and CWE-59 (path traversal and link following) |
| Backup before every change, never overwritten | NIST SP 800-53 Rev. 5, control CP-9 (system backup); ISO/IEC 27001:2022, Annex A 8.13 (information backup) |
| Logbook: append only, one line per action with who approved it | NIST SP 800-53 Rev. 5, controls AU-3 (content of audit records) and AU-9 (protection of audit information) |
| Verify with a fact, not an opinion | ITIL 4, change enablement (post-implementation review); the repo's rule 3 (every number from a script) |
| The text guides, the platform enforces | Claude Code documentation: "Permission rules are enforced by Claude Code, not by the model" (permissions page) |

## Bibliography

- AXELOS. *ITIL 4: Change Enablement* (practice guide). AXELOS, 2020. Change authorization, change
  models, and the review of implemented changes.
- AXELOS. *ITIL Foundation, ITIL 4 Edition*. TSO, 2019. Chapter 5, general and service management
  practices (change enablement).
- National Institute of Standards and Technology. *Security and Privacy Controls for Information
  Systems and Organizations*. NIST SP 800-53 Rev. 5, 2020 (updates to 2023). Controls AC-6 (least
  privilege), CP-9 (system backup), AU-3 and AU-9 (audit records and their protection).
- Saltzer, J. H.; Schroeder, M. D. "The Protection of Information in Computer Systems."
  *Proceedings of the IEEE* 63 (9), 1975. Section I.A.3, design principles.
- ISO/IEC 27001:2022. *Information security, cybersecurity and privacy protection · Information
  security management systems · Requirements*. Annex A 8.13 (information backup) and 8.32 (change
  management).
- MITRE. *Common Weakness Enumeration*: CWE-22 (path traversal) and CWE-59 (link following).

## Platform documentation checked (16-10-2026)

- Claude Code: `https://code.claude.com/docs/en/permissions` and
  `https://code.claude.com/docs/en/settings`. What was taken from them is listed in `GUIDE.md`,
  "Install the permissions".
- Codex, Cursor CLI and Gemini CLI: the pages named in `templates/codex.md`, `templates/cursor.md`
  and `templates/gemini-cli.md`.

## Where the judgement came from

From an operator's practice with agents working on a small company's files (private data, outside
this repo). The rules that are not in the standards above (one OK per action, "se ve bien" is not a
verification, prepare what is forbidden and let the person do it) answer a failure seen there:
actions run in a batch under one approval and not checked one by one.
