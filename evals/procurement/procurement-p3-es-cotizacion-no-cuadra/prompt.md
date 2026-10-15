---
name: procurement-p3-es-cotizacion-no-cuadra
description: "positive es for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

Antes de comparar esta cotización con las otras dos, dime si le puedo creer: las líneas suman $1.284.000 pero el subtotal impreso dice $1.248.000, y el descuento de 8 % aparece solo en el total de cada línea, no en el precio unitario.
