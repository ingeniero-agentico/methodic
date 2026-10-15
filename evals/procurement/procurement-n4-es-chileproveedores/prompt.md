---
name: procurement-n4-es-chileproveedores
description: "negative es for procurement; expects no skill"
tags: ["trigger", "procurement", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "procurement stays silent; no skill of this plugin fires."
---

¿Qué es ChileProveedores y qué papeles necesito para inscribir mi empresa y poder venderle al Estado por Mercado Público?
