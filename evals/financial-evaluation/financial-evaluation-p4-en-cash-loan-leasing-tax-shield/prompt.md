---
name: financial-evaluation-p4-en-cash-loan-leasing-tax-shield
description: "positive en for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

We've already decided to buy the truck. Compare paying cash, a French-amortization loan and a financial leasing with purchase option, including the interest tax shield.
