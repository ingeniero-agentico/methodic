---
name: financial-evaluation-p2-es-tabla-amortizacion-cae
description: "positive es for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

El banco me ofreció un crédito de $20 millones a 36 meses con tasa de 1,1 % mensual y $350.000 de gastos. Ármame la tabla de amortización y dime cuál es la CAE.
