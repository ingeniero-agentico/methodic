---
name: economic-evaluation-p5-en-pure-cash-flow-cnc
description: "positive en for economic-evaluation; expects economic-evaluation"
tags: ["trigger", "economic-evaluation", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The economic-evaluation skill fires; no other skill of the plugin does."
---

Build me the pure project cash flow, with tax, depreciation and salvage value, for buying a CNC machine, and tell me whether it pays off.
