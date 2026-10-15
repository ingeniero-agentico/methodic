---
name: map-context-p5-en-delta-since-last-map
description: "positive en for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

What's changed in the job folder since you last mapped it? Just give me the delta, don't reread everything.
