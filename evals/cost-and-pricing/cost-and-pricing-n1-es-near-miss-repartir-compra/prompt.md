---
name: cost-and-pricing-n1-es-near-miss-repartir-compra
description: "negative es for cost-and-pricing; expects procurement"
tags: ["trigger", "cost-and-pricing", "negative", "es", "near-miss"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "cost-and-pricing stays silent; the neighbour procurement fires instead."
---

Tengo dos cotizaciones para los mismos 40 sacos de cemento y ninguno de los dos proveedores los tiene todos. ¿Cómo reparto la compra entre ellos?
