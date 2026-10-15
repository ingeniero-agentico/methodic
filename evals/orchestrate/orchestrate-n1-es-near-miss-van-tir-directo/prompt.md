---
name: orchestrate-n1-es-near-miss-van-tir-directo
description: "negative es for orchestrate; expects economic-evaluation"
tags: ["trigger", "orchestrate", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate stays silent; the neighbour economic-evaluation fires instead."
---

Calcula el VAN y la TIR de estos flujos: -10.000.000, 3.000.000, 4.000.000 y 5.000.000, a una tasa del 10 %.
