---
name: cost-and-pricing-p3-es-horas-para-cubrir-fijos
description: "positive es for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

Cobro las asesorías a $35.000 la hora; tengo $1.200.000 de costos fijos al mes y $5.000 de costo variable por hora. ¿Cuántas horas tengo que vender al mes para no perder plata?
