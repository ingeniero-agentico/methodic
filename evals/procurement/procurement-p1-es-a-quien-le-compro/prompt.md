---
name: procurement-p1-es-a-quien-le-compro
description: "positive es for procurement; expects procurement"
tags: ["trigger", "procurement", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The procurement skill fires; no other skill of the plugin does."
---

Me llegaron tres cotizaciones para el mismo pedido: 220 m de tubería HDPE 90 PN10 y 14 fittings de termofusión. Son de Proveedor A, Proveedor B y Proveedor C, y ninguno tiene todo el stock. ¿A quién le compro qué?
