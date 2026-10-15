---
name: economic-evaluation-p6-en-irr-two-sign-changes
description: "positive en for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

Our IRR came out weird because the cash flows change sign twice: -50 million CLP today, then +30, +30, -20 (a major overhaul) and +40 million over the next four years, at a 12 % discount rate. Redo the project evaluation and run a sensitivity on the year-4 inflow to find where NPV hits zero.
