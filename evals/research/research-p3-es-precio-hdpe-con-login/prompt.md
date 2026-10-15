---
name: research-p3-es-precio-hdpe-con-login
description: "positive es for research; expects research"
tags: ["trigger", "research", "positive", "es"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The research skill fires; no other skill of the plugin does."
---

Investiga cuánto vale hoy en Chile el metro de tubería HDPE 90 PN10. Si alguna página pide login o captcha, avísame y la bajo yo.
