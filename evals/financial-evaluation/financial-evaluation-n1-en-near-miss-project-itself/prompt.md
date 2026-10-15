---
name: financial-evaluation-n1-en-near-miss-project-itself
description: "negative en for financial-evaluation; expects economic-evaluation"
tags: ["trigger", "financial-evaluation", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "financial-evaluation stays silent; the neighbour economic-evaluation fires instead."
---

Before we even think about how to pay for it: does buying a second excavator to rent out make sense at all? Give me the NPV and IRR of the project itself.
