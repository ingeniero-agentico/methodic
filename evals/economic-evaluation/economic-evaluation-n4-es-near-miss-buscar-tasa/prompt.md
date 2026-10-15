---
name: economic-evaluation-n4-es-near-miss-buscar-tasa
description: "negative es for economic-evaluation; expects research"
tags: ["trigger", "economic-evaluation", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "economic-evaluation stays silent; the neighbour research fires instead."
---

Busca la tasa de leasing vigente para pymes en Chile, con fuente y fecha, para usarla después en la evaluación.
