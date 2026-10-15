---
name: cost-and-pricing-p6-en-markup-per-item
description: "positive en for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

Set sale prices for these five items with a markup on cost (not the same markup for all of them) and show me the real margin on sales for each one.
