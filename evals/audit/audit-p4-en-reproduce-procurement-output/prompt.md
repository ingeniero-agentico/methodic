---
name: audit-p4-en-reproduce-procurement-output
description: "positive en for audit; expects audit"
tags: ["trigger", "audit", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

Can the procurement output in cases/procurement-sample be reproduced? Re-run it in a temporary folder and compare it figure by figure.
