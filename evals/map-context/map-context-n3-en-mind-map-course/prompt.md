---
name: map-context-n3-en-mind-map-course
description: "negative en for map-context; expects no skill"
tags: ["trigger", "map-context", "negative", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "map-context stays silent; no skill of this plugin fires."
---

Draw me a mind map of the chapters of my operations management course.
