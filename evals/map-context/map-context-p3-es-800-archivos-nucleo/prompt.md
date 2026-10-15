---
name: map-context-p3-es-800-archivos-nucleo
description: "positive es for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

La carpeta del proyecto tiene como 800 archivos y no quiero que los leas uno por uno. Hazme un mapa barato y dime cuáles son los 3 que hay que leer sí o sí.
