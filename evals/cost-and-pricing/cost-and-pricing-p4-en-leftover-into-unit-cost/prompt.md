---
name: cost-and-pricing-p4-en-leftover-into-unit-cost
description: "positive en for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

We buy cable in 100 m rolls but sell it by the metre, and the last job left 37 m over. How do I carry that leftover into the unit cost before I quote the client?
