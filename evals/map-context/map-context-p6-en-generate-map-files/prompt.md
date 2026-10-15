---
name: map-context-p6-en-generate-map-files
description: "positive en for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

Generate context/MAP.md, graph.json and fingerprints.json for the folders of this new task before anyone starts reading.
