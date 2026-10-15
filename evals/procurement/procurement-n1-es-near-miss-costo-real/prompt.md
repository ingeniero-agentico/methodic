---
name: procurement-n1-es-near-miss-costo-real
description: "negative es for procurement; expects cost-and-pricing"
tags: ["trigger", "procurement", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "procurement stays silent; the neighbour cost-and-pricing fires instead."
---

Ya emití las órdenes de compra del trabajo de Constructora Sur. Ahora necesito saber cuánto me costó realmente cada ítem y a qué precio se lo vendo al cliente con un recargo de 25 %.
