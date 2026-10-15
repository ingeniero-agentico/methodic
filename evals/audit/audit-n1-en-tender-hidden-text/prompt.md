---
name: audit-n1-en-tender-hidden-text
description: "negative en for audit; expects no skill"
tags: ["trigger", "audit", "negative", "en", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "audit stays silent; no skill of this plugin fires."
---

Here's a tender document from a mining client. Check it for hidden white text or instructions aimed at an AI before we bid.
