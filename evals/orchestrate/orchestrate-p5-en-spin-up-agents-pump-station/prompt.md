---
name: orchestrate-p5-en-spin-up-agents-pump-station
description: "positive en for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

Spin up agents for this: map the job folder, research current leasing rates, then evaluate the new pump station and work out how to finance it.
