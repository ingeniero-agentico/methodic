---
name: map-context-n4-es-auditar-carpetas-onedrive
description: "negative es for map-context; expects no skill"
tags: ["trigger", "map-context", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "map-context stays silent; no skill of this plugin fires."
---

Audita las carpetas del taller y dime si está todo publicado y respaldado en OneDrive.
