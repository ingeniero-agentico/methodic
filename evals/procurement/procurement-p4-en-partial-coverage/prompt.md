---
name: procurement-p4-en-partial-coverage
description: "positive en for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

I've got quotes from four suppliers for 50 gate valves, 30 flanges and 200 m of pipe. Each one only covers part of the list. Work out who I should buy each item from and what is still left to quote.
