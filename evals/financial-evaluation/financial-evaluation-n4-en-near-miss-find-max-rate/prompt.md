---
name: financial-evaluation-n4-en-near-miss-find-max-rate
description: "negative en for financial-evaluation; expects research"
tags: ["trigger", "financial-evaluation", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "financial-evaluation stays silent; the neighbour research fires instead."
---

Find the current maximum conventional interest rate that the CMF publishes for consumer loans in Chile and cite the source and date.
