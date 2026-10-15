---
name: research-p5-en-contradicting-sources
description: "positive en for research; expects research"
tags: ["trigger", "research", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

Two sources give different residual values for the excavator after 5 years. Put them side by side and pick one with an explicit reason.
