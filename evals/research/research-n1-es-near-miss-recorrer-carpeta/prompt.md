---
name: research-n1-es-near-miss-recorrer-carpeta
description: "negative es for research; expects map-context"
tags: ["trigger", "research", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "research stays silent; the neighbour map-context fires instead."
---

Antes de buscar nada afuera, recorre la carpeta del encargo y dime qué archivos hay y qué cambió desde la última vez.
