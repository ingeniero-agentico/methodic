---
name: cost-and-pricing-p2-es-le-puse-30
description: "positive es for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

Le puse 30 % a todo en la cotización al cliente, pero el contador dice que mi margen no es 30. ¿Cuánto estoy ganando de verdad?
