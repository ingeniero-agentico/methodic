---
name: orchestrate-p2-es-tercera-camioneta-y-financiar
description: "positive es for orchestrate; expects orchestrate"
tags: ["trigger", "orchestrate", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "orchestrate fires (the skills of its chain may follow)."
---

Orquesta esto: quiero saber si me conviene comprar una tercera camioneta para el negocio de arriendo y, si conviene, cómo financiarla. Investiga las tasas que falten.
