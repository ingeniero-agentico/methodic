---
name: economic-evaluation-p1-es-camioneta-para-arrendar
description: "positive es for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

¿Me conviene comprar una camioneta de $22 millones para arrendarla a $45.000 el día? Calcula el VAN y la TIR a 5 años con una tasa del 12 %.
