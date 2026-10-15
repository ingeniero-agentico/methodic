---
name: orchestrate-p4-en-idea-end-to-end
description: "positive en for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

I have a project idea: a mobile pipe-welding service. Research what's missing, run the numbers end to end and give me one audited answer.
