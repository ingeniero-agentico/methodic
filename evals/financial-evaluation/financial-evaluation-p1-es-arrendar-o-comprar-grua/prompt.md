---
name: financial-evaluation-p1-es-arrendar-o-comprar-grua
description: "positive es for financial-evaluation; expects financial-evaluation"
tags: ["trigger", "financial-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The financial-evaluation skill fires; no other skill of the plugin does."
---

¿Me conviene arrendar o comprar la grúa? El arriendo sale $1,8 millones al mes y comprarla cuesta $95 millones.
