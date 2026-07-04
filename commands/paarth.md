---
description: Route a task through PAARTH's classifier, skill chain, memory, and verification workflow.
argument-hint: "<task description>"
allowed-tools: ["Bash", "Read", "Write", "Edit", "Grep", "Glob"]
---

You were invoked via `/paarth $ARGUMENTS`.

Invoke the **`paarth` skill** with the argument string `$ARGUMENTS`
exactly as typed. The skill knows how to:

- Wake local memory with `mempalace wake-up`.
- Classify the task with `paarth-classify "$ARGUMENTS"`.
- Announce the selected skill chain and rationale.
- Execute the chain in order, respecting each skill's verification rules.
- Log the outcome to `~/.paarth/brain/routes.jsonl`.

If `$ARGUMENTS` is empty, ask the user for the task to route. Otherwise,
follow the `paarth` skill procedure and stop when the routed workflow is
complete or explicitly paused for user input.
