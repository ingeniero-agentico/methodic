---
name: audit-n3-es-near-miss-recalcular-tabla
description: "negative es for audit; expects financial-evaluation"
tags: ["trigger", "audit", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "audit stays silent; the neighbour financial-evaluation fires instead."
---

Recalcula la tabla de amortización del crédito de $20 millones a 36 meses con la tasa nueva que nos dio el banco: 0,95 % mensual.
