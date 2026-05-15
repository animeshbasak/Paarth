---
description: Route a task through SuperAgent's classifier, skill chain, memory, and verification workflow.
argument-hint: "<task description>"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob"]
---

You were invoked via `/superagent $ARGUMENTS`.

Invoke the **`superagent` skill** with the argument string `$ARGUMENTS`
exactly as typed. The skill knows how to:

- Wake local memory with `mempalace wake-up`.
- Classify the task with `superagent-classify "$ARGUMENTS"`.
- Announce the selected skill chain and rationale.
- Execute the chain in order, respecting each skill's verification rules.
- Log the outcome to `~/.superagent/brain/routes.jsonl`.

If `$ARGUMENTS` is empty, ask the user for the task to route. Otherwise,
follow the `superagent` skill procedure and stop when the routed workflow is
complete or explicitly paused for user input.
