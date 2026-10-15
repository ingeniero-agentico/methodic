---
name: economic-evaluation-p2-es-ocupacion-minima
description: "positive es for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

Estoy pensando en abrir una línea de arriendo de grúas horquilla. ¿Con qué ocupación mínima se paga la inversión?
