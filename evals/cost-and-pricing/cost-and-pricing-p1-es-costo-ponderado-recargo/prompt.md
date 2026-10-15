---
name: cost-and-pricing-p1-es-costo-ponderado-recargo
description: "positive es for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

Compré la tubería repartida entre dos proveedores: 120 m a $4.200 y 100 m a $4.650. ¿Cuál es el costo unitario real y a cuánto la vendo con 30 de recargo?
