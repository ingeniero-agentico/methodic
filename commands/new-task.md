---
description: Receives an engineering or management task, maps the context, proposes the agent plan and runs it with your approval
argument-hint: "<the task in your words> [reread | first-run] [without agents]"
---

Use the `orchestrate` skill with this task:

$ARGUMENTS

If it says "reread" or "first-run" (or the Spanish "relectura" or "primera vez"), that mode
prevails over the one the cartographer suggests. If it says "without agents" ("sin agentes"), run
the stages in sequence in this conversation. If the task comes empty, ask what it is before
starting.
