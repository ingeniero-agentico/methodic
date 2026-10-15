---
name: map-context-p2-es-volvi-que-cambio
description: "positive es for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

Volví al tema del arriendo de camionetas después de dos semanas. ¿Qué cambió en la carpeta desde la última vez que la revisamos?
