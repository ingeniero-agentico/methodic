---
name: economic-evaluation-n3-en-personal-savings
description: "negative en for economic-evaluation; expects no skill"
tags: ["trigger", "economic-evaluation", "negative", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "economic-evaluation stays silent; no skill of this plugin fires."
---

I'm 23 and have 3 million CLP saved. Should I put it in a mutual fund or a term deposit?
