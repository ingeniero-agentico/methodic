---
name: research-n2-es-near-miss-van-con-tasa-investigada
description: "negative es for research; expects economic-evaluation"
tags: ["trigger", "research", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "research stays silent; the neighbour economic-evaluation fires instead."
---

Con la tasa de 12 % que ya investigamos, calcula el VAN del proyecto de la grúa: inversión de $95 millones y flujos de $28 millones al año por 5 años.
