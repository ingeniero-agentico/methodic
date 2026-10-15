---
name: map-context-p4-en-first-run-or-reread
description: "positive en for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

Map the context for this task: walk the pump-station job folder and tell me whether this is a first run or a reread.
