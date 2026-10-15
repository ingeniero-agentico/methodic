---
name: financial-evaluation-p6-en-zero-interest-leasing
description: "positive en for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

The dealer says the leasing is 'zero interest' if we finance with them, but then we lose the 3 million discount for paying cash. What does that leasing really cost us after tax?
