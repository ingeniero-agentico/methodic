---
name: procurement-n2-en-near-miss-pay-cash-or-lease
description: "negative en for procurement; expects financial-evaluation"
tags: ["trigger", "procurement", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "procurement stays silent; the neighbour financial-evaluation fires instead."
---

The dealer offers the excavator either cash at USD 180,000 or a 36-month financial leasing with a purchase option. Which way should we pay for it?
