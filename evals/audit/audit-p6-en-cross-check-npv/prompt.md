---
name: audit-p6-en-cross-check-npv
description: "positive en for audit; expects audit"
tags: ["trigger", "audit", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

Cross-check that the project NPV the financial evaluation read is the same one the economic evaluation produced.
