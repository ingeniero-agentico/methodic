---
name: procurement-n3-es-correo-pedir-pdf
description: "negative es for procurement; expects no skill"
tags: ["trigger", "procurement", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "procurement stays silent; no skill of this plugin fires."
---

Redáctame un correo amable para pedirle a un proveedor que me reenvíe la cotización en PDF, porque la que mandó viene cortada en la segunda página.
