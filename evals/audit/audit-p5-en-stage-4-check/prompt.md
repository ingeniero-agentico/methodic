---
name: audit-p5-en-stage-4-check
description: "positive en for audit; expects audit"
tags: ["trigger", "audit", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

Stage 4: the executor agents finished. Check every archived output against a fresh run before anyone relies on it.
