---
name: audit-p1-es-auditar-caso-camioneta
description: "positive es for audit; expects audit"
tags: ["trigger", "audit", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

Audita el caso de la camioneta: vuelve a correr los scripts y dime si las cifras del Excel archivado salen iguales.
