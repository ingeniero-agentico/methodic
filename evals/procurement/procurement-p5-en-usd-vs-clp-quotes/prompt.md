---
name: procurement-p5-en-usd-vs-clp-quotes
description: "positive en for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

One supplier quoted in USD and the other two in CLP. Line the three quotes up item by item and tell me which one is really cheapest for each line at 950 CLP per dollar.
