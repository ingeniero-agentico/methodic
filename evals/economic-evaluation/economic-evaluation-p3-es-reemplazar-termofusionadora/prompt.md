---
name: economic-evaluation-p3-es-reemplazar-termofusionadora
description: "positive es for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

Evalúa si conviene reemplazar la termofusionadora vieja por una nueva de $8,5 millones: ahorra $2,1 millones al año en mantención y dura 7 años.
