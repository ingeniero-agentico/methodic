---
name: research-p1-es-de-donde-sale-la-tasa
description: "positive es for research; expects research"
tags: ["trigger", "research", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

¿De dónde sale ese 1,1 % mensual de la tasa de leasing? Búscame la tasa vigente con fuente y fecha antes de calcular nada.
