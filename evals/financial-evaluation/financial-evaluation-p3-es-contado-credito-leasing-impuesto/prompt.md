---
name: financial-evaluation-p3-es-contado-credito-leasing-impuesto
description: "positive es for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

¿Contado, crédito o leasing para la camioneta? La empresa paga 25 % de impuesto y quiero saber cuánto cambia el resultado después de impuesto con cada opción.
