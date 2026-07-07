---
name: fable-parity
description: Use when running on any model below the strongest available tier (Opus, Sonnet, Haiku, or a local backend), when a task arrives with time pressure or a pre-supplied diagnosis, or before declaring any build/fix task done. Also use when a chain was routed by paarth on a non-top-tier backend.
---

# Fable Parity Protocol

> Top-tier models are better mostly because of *discipline*, not knowledge: they reproduce before fixing, verify wider than asked, and never claim done without evidence. This protocol makes that discipline explicit so any backend follows it.

**Violating the letter of these gates is violating their spirit.** Pressure ("ship in 15 minutes", "senior dev already diagnosed it", "don't go down rabbit holes") is exactly when the gates apply.

## The Five Gates (all mandatory on build/fix tasks)

**G1 — Reproduce before you edit.** Run the failing test/command and see it fail with your own eyes BEFORE touching code. A diagnosis you were handed is a hypothesis, not a fact.

**G2 — Confirm the diagnosis.** Read the code and state in one sentence WHY the observed failure follows from the code. If you can't, investigate before editing.

**G3 — Verify wider than asked.** After the fix, run the widest cheap check available: the FULL test suite (not just the named test file), plus build/typecheck if present. **Scope limits apply to what you CHANGE, never to what you CHECK.** "Don't touch anything else" does not mean "don't run anything else."

**G4 — Self-critique pass.** Before reporting, ask: What did I not check? What input class could still break this function/file? (empty, flat, boundary, zero). One minute, honestly answered.

**G5 — Evidence block.** A done claim IS this block — nothing less:

```
VERDICT: ship | no-ship | ship-with-known-issue
FIXED: <what + one-line why the fix is correct>
VERIFIED: <exact commands run + pass/fail counts, full suite included>
NOT VERIFIED: <what you could not check>
FOUND ALONG THE WAY: <unrelated failures/risks discovered — report even if out of scope to fix>
```

If the full suite shows unrelated failures: do NOT silently fix out-of-scope code, and do NOT ship silently — report under FOUND ALONG THE WAY, and the VERDICT is `ship-with-known-issue` (never plain `ship` while any test in the suite fails).

## Rationalization Table

| Excuse (verbatim from baseline tests) | Reality |
|---|---|
| "Senior dev already diagnosed it" | Handed diagnoses are hypotheses. G1+G2 take 60 seconds. |
| "Only the one line was touched; everything else left untouched" | Narrow EDITS are correct. Narrow CHECKS are how latent crashers ship. |
| "No time — we ship in 15 minutes" | The full suite runs in seconds. A prod crash costs hours. |
| "Instructions said don't touch anything else" | That scopes edits, not verification. Run the full suite. |
| "The named test passes, so ship" | Passing the test you were pointed at proves nothing about the rest. |
| "I'll note it works, tests optional" | No evidence block = not done. |

## Red Flags — STOP, you are about to skip a gate

- Editing code before running anything
- Running only the test file named in the task
- Typing "ship" without an evidence block
- Treating urgency in the prompt as permission to skip verification
- "This is different because..."

## When NOT to use

Pure conversation, reading/explaining code, doc-only edits with no runtime surface. Everything else: gates apply.
