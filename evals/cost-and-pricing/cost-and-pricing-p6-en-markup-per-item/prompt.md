---
name: cost-and-pricing-p6-en-markup-per-item
description: "positive en for cost-and-pricing; expects cost-and-pricing"
tags: ["trigger", "cost-and-pricing", "positive", "en"]
plugins: ["../../.."]
runs: 3
max_turns: 8
timeout_seconds: 240
allowed_tools: [Skill, Read, Glob, Grep]
expected_outcome: "The cost-and-pricing skill fires; no other skill of the plugin does."
---

Set sale prices with a markup on cost for these items and show the real margin on sales for each: valve, cost 20,000 CLP, markup 30 %; pipe, cost 4,100 CLP per metre, markup 25 %; elbow, cost 3,700 CLP, markup 40 %; tee, cost 1,250 CLP, markup 60 %; flange, cost 9,800 CLP, markup 35 %.
