---
name: map-context-n2-es-mapa-ruta-chillan
description: "negative es for map-context; expects no skill"
tags: ["trigger", "map-context", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "map-context stays silent; no skill of this plugin fires."
---

Hazme un mapa de cómo llegar desde Talca a Curicó evitando la Ruta 5.
