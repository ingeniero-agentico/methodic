---
name: financial-evaluation-p5-en-investor-npv
description: "positive en for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

Take the project cash flow from the economic evaluation and add the financing: what's the investor NPV with 60 % of the investment on a loan at 9 % a year?
