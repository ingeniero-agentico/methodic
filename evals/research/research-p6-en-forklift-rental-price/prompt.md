---
name: research-p6-en-forklift-rental-price
description: "positive en for research; expects research"
tags: ["trigger", "research", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

Find the current market price of renting a 3-tonne forklift per day in Santiago, with source, date and an A-D reliability grade.
