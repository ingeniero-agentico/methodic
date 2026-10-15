---
name: cost-and-pricing-p5-en-real-cost-with-overhead
description: "positive en for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

How much did the Constructora Sur job really cost us per item once you add 12 % overhead? I have the three purchase orders, and one of them is in USD.
