---
name: testgen
description: Slash dispatcher for testgen. Forwards args to bin/superagent-testgen.
---

# /testgen

Routes the user's subcommand to `bin/superagent-testgen`. See [testgen](../skills/testgen/SKILL.md) for the full procedure.

## Usage

```
/testgen scan [--fixture <path>]       # parse coverage output
/testgen gap [--top N]                 # ranked table of files below threshold
/testgen suggest <file>                # markdown skeleton (uncovered ranges + symbols)
/testgen status [--json]               # current coverage vs threshold
```

## Procedure

- `scan` — print the format/total/file-count summary verbatim.
- `gap` — print the markdown table verbatim.
- `suggest <file>` — print the skeleton verbatim. Then offer to dispatch the `tester` agent to implement the listed tests.
- `status` — human-readable by default; `--json` for downstream tools.

Do not have testgen write test bodies. That's the `tester` agent's job.
