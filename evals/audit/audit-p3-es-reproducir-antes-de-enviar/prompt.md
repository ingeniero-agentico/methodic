---
name: audit-p3-es-reproducir-antes-de-enviar
description: "positive es for audit; expects audit"
tags: ["trigger", "audit", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The audit skill fires; no other skill of the plugin does."
---

Antes de mandarle el informe al cliente, verifica que la salida de adquisiciones se pueda reproducir con la misma entrada.
