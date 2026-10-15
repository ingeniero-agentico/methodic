---
name: financial-evaluation-n2-es-near-miss-sucursal-chillan
description: "negative es for financial-evaluation; expects economic-evaluation"
tags: ["trigger", "financial-evaluation", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "financial-evaluation stays silent; the neighbour economic-evaluation fires instead."
---

¿Conviene abrir una sucursal en Talca? Son $40 millones de inversión y esperamos vender $30 millones al año con un margen de contribución de 35 %.
