---
name: cost-and-pricing-n4-en-gross-vs-ebitda-class
description: "negative en for cost-and-pricing; expects no skill"
tags: ["trigger", "cost-and-pricing", "negative", "en", "borderline"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "cost-and-pricing stays silent; no skill of this plugin fires."
---

For my accounting exam tomorrow, explain the difference between gross margin and EBITDA margin with a tiny made-up example.
