---
name: orchestrate-n2-en-near-miss-amortization-table
description: "negative en for orchestrate; expects financial-evaluation"
tags: ["trigger", "orchestrate", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate stays silent; the neighbour financial-evaluation fires instead."
---

Build an amortization table for a 15 million CLP loan at 1 % a month over 24 months, French system.
