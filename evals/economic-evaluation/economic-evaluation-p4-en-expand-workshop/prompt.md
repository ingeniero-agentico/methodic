---
name: economic-evaluation-p4-en-expand-workshop
description: "positive en for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

Is it worth expanding the workshop? 60 million CLP of investment, 25 million a year of extra sales, 4 million of working capital. Give me NPV, IRR and payback.
