---
name: research-p2-es-cerrar-supuestos
description: "positive es for research; expects research"
tags: ["trigger", "research", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

Cierra los supuestos del caso: el valor residual de una camioneta 4x4 diésel a 5 años y el costo del permiso de circulación, cada uno con su fuente y su nivel de fiabilidad.
