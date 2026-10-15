---
name: audit-n4-en-review-npv-function
description: "negative en for audit; expects no skill"
tags: ["trigger", "audit", "negative", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "audit stays silent; no skill of this plugin fires."
---

Review this Python function for bugs: def npv(rate, flows): return sum(f / (1 + rate) ** i for i, f in enumerate(flows))
