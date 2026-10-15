---
name: economic-evaluation-n2-en-near-miss-service-break-even
description: "negative en for economic-evaluation; expects cost-and-pricing"
tags: ["trigger", "economic-evaluation", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "economic-evaluation stays silent; the neighbour cost-and-pricing fires instead."
---

What's the break-even point of my consulting service if fixed costs are 1.2 million CLP a month and each billed hour brings 30,000 CLP of contribution?
