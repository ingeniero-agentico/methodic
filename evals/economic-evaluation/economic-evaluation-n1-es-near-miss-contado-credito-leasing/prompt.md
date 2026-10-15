---
name: economic-evaluation-n1-es-near-miss-contado-credito-leasing
description: "negative es for economic-evaluation; expects financial-evaluation"
tags: ["trigger", "economic-evaluation", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "economic-evaluation stays silent; the neighbour financial-evaluation fires instead."
---

Ya decidimos comprar la grúa. ¿Nos conviene pagarla al contado, con crédito del banco o con un leasing a 36 cuotas?
