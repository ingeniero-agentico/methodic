---
name: cost-and-pricing-n2-en-near-miss-van-to-rent-out
description: "negative en for cost-and-pricing; expects economic-evaluation"
tags: ["trigger", "cost-and-pricing", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "cost-and-pricing stays silent; the neighbour economic-evaluation fires instead."
---

If I buy a second van for 22 million CLP to rent it out at 45,000 CLP per day, is the investment worth it over five years?
