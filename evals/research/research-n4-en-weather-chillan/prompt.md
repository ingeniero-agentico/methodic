---
name: research-n4-en-weather-chillan
description: "negative en for research; expects no skill"
tags: ["trigger", "research", "negative", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "research stays silent; no skill of this plugin fires."
---

What's the weather forecast for Talca this weekend?
