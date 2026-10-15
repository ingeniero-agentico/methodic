---
name: map-context-n1-es-near-miss-buscar-huecos
description: "negative es for map-context; expects research"
tags: ["trigger", "map-context", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "map-context stays silent; the neighbour research fires instead."
---

El mapa dice que faltan la tasa de leasing vigente y el valor residual de la camioneta a 5 años. Búscalos con fuente y fecha.
