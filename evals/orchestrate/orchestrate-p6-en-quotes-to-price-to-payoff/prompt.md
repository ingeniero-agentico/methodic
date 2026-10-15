---
name: orchestrate-p6-en-quotes-to-price-to-payoff
description: "positive en for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

Here's the plant-expansion folder with the supplier quotes. Figure out the purchase plan, the selling price to the client and whether the expansion pays off, whatever steps it takes.
