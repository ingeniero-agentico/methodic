---
name: procurement-p2-es-tiras-de-6-metros
description: "positive es for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

El proveedor A me cotizó la tubería a $4.200 el metro pero vende en tiras de 6 m, y el B a $4.500 el metro suelto. Además el A me cotizó solo 120 de los 200 metros que necesito. ¿Con quién me quedo y cuánto le pido a cada uno?
