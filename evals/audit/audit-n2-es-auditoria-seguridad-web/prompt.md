---
name: audit-n2-es-auditoria-seguridad-web
description: "negative es for audit; expects no skill"
tags: ["trigger", "audit", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "audit stays silent; no skill of this plugin fires."
---

Haz una auditoría de seguridad del formulario de contacto de mi sitio web: quiero saber si es vulnerable a spam o inyección.
