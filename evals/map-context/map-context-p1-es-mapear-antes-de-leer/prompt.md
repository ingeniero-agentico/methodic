---
name: map-context-p1-es-mapear-antes-de-leer
description: "positive es for map-context; expects map-context"
tags: ["trigger", "map-context", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The map-context skill fires; no other skill of the plugin does."
---

Antes de leer nada, mapea las carpetas del trabajo de Constructora Sur: qué archivos hay, de cuándo son y qué enlaza con qué.
