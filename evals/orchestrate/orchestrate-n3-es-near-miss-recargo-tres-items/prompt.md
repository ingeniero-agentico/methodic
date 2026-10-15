---
name: orchestrate-n3-es-near-miss-recargo-tres-items
description: "negative es for orchestrate; expects cost-and-pricing"
tags: ["trigger", "orchestrate", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate stays silent; the neighbour cost-and-pricing fires instead."
---

Ponle un recargo de 30 % sobre costo a estos tres ítems y muéstrame el margen real de cada uno: válvula $12.000, brida $8.500, codo $3.200.
