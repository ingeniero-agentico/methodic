---
name: research-n3-es-paper-metodologia
description: "negative es for research; expects no skill"
tags: ["trigger", "research", "negative", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "research stays silent; no skill of this plugin fires."
---

Ayúdame a escribir la sección de metodología de mi paper del seminario de investigación sobre liderazgo en equipos deportivos.
