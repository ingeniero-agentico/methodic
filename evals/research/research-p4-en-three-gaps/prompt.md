---
name: research-p4-en-three-gaps
description: "positive en for research; expects research"
tags: ["trigger", "research", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

The plan lists three gaps: the current SME leasing rate, the corporate tax rate under Pro Pyme, and the tax useful life of a pickup truck. Research them one datum at a time.
