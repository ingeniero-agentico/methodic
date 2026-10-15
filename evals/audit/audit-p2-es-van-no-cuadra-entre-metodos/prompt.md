---
name: audit-p2-es-van-no-cuadra-entre-metodos
description: "positive es for audit; expects audit"
tags: ["trigger", "audit", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

¿Esto está bien calculado? El VAN del proyecto que usó la evaluación financiera no me cuadra con el que dio la evaluación económica.
