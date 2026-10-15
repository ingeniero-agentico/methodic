---
name: orchestrate-p3-es-encargo-nuevo-no-se-por-donde
description: "positive es for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

Llegó un encargo nuevo de un cliente agrícola y no sé por dónde partir: hay planos, un listado de materiales y tres cotizaciones. Ayúdame a armar el plan.
