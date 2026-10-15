---
name: cost-and-pricing-n3-es-margenes-de-word
description: "negative es for cost-and-pricing; expects no skill"
tags: ["trigger", "cost-and-pricing", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "cost-and-pricing stays silent; no skill of this plugin fires."
---

Ajusta los márgenes de este documento de Word para que el informe quepa en una sola página.
