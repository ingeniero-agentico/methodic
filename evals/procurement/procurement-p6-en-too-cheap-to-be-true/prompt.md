---
name: procurement-p6-en-too-cheap-to-be-true
description: "positive en for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

Supplier B is 40 % below everyone else on the butterfly valves. Before we award the order, help me check it's really the same product and decide how to split the purchase.
