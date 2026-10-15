---
name: financial-evaluation-n3-es-hipotecario-o-apv
description: "negative es for financial-evaluation; expects no skill"
tags: ["trigger", "financial-evaluation", "negative", "es", "borderline"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "financial-evaluation stays silent; no skill of this plugin fires."
---

Tengo un crédito hipotecario y gano $1.500.000 líquidos. ¿Me conviene prepagar el dividendo o seguir ahorrando en el APV?
