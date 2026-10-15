---
name: orchestrate-n4-en-how-subagents-work
description: "negative en for orchestrate; expects no skill"
tags: ["trigger", "orchestrate", "negative", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate stays silent; no skill of this plugin fires."
---

Explain how Claude Code subagents work and when it makes sense to launch several of them in parallel.
