---
name: paarth-learn-loop
description: PAARTH learning loop. Promotes recurring done-routes into pattern records, decays stale ones, and feeds them back to the classifier. Use whenever the user wants to teach PAARTH which chains worked, prune old patterns, or inspect/protect specific routes. Triggers on "promote pattern", "learn this routing", "decay patterns", "list patterns", "protect pattern".
---

# paarth-learn-loop

The PAARTH classifier becomes self-improving in v2.4. Every Stop hook runs `paarth-patterns promote` (extracts repeated done-routes into pattern records) and `paarth-patterns decay` (exponentially decays inactive ones). The classifier reads `~/.paarth/brain/patterns.jsonl` and prepends matched chains when `successRate ≥ 0.6` and `useCount ≥ 5`.

## When to use

- User says "remember this pattern" / "promote this route" / "learn this".
- User wants to inspect, protect, or prune the pattern store.
- After a session where you discovered a chain that should survive into future sessions.

## Procedure

1. **List current patterns** to ground the user:
   ```bash
   paarth-patterns list
   ```
2. **Manual promote** if the user wants the latest routes folded in immediately (Stop hook already does this on session end):
   ```bash
   paarth-patterns promote
   ```
3. **Protect a high-value pattern** so decay won't drop it below 0.3:
   ```bash
   paarth-patterns protect p-<id>
   ```
4. **Manual prune** to clean noise below a custom threshold:
   ```bash
   paarth-patterns prune --below 0.3
   ```

## Files

- Store: `~/.paarth/brain/patterns.jsonl` (append-only JSONL).
- Source: `~/.paarth/brain/routes.jsonl` (read by `promote`).
- Defaults: `~/.paarth/defaults.toml` `[learning]` section.

## Ethos

Memory is compounding interest. Each successful chain that survives the gate becomes a faster route next session. Don't bypass the gate — `successRate ≥ 0.6 + useCount ≥ 5` is what keeps one-off coincidences out of the classifier.
