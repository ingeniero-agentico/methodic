---
name: orchestrate-p1-es-carpeta-cotizaciones-lanzar-agentes
description: "positive es for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

Tengo una carpeta con cotizaciones de cinco proveedores para la planta de tratamiento de un cliente. Necesito decidir a quién comprarle, calcular a cuánto venderle al cliente y ver si conviene financiar la bomba con leasing. Lánzale agentes.
