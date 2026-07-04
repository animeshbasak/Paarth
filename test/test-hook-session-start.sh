#!/usr/bin/env bash
# test/test-hook-session-start.sh — SessionStart hook respects the injection budget
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$SCRIPT_DIR/../hooks/paarth-session-start.py"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
mkdir -p "$TMPHOME/.paarth/brain"

TS=$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)
for i in 1 2 3 4 5 6; do
  echo "{\"ts\":\"$TS\",\"task\":\"t$i\",\"chain\":[\"investigate\",\"review\",\"ship\",\"verification-before-completion\"],\"outcome\":\"done\"}" \
    >> "$TMPHOME/.paarth/brain/routes.jsonl"
done

# Default budget (600): header + 5 routes fit comfortably
OUT=$(HOME="$TMPHOME" python3 "$HOOK" </dev/null)
echo "$OUT" | jq -e '.hookSpecificOutput.hookEventName == "SessionStart"' >/dev/null \
  || { echo "FAIL: invalid hook output: $OUT"; exit 1; }
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("Recent routes (last 5)")' >/dev/null \
  || { echo "FAIL: expected 5 routes under default budget: $OUT"; exit 1; }

# Tiny budget → routes list shrinks (or disappears), header always survives
OUT=$(HOME="$TMPHOME" PAARTH_INJECT_BUDGET_TOKENS=40 python3 "$HOOK" </dev/null)
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## PAARTH context")' >/dev/null \
  || { echo "FAIL: header missing under tiny budget: $OUT"; exit 1; }
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("Recent routes (last 5)") | not' >/dev/null \
  || { echo "FAIL: routes not trimmed under tiny budget: $OUT"; exit 1; }

# Budget kill switch → back to full 5
OUT=$(HOME="$TMPHOME" PAARTH_INJECT_BUDGET_TOKENS=40 PAARTH_INJECT_BUDGET=0 python3 "$HOOK" </dev/null)
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("Recent routes (last 5)")' >/dev/null \
  || { echo "FAIL: budget kill switch ignored: $OUT"; exit 1; }

# Dedicated hook kill switch → no output at all
OUT=$(HOME="$TMPHOME" PAARTH_SESSION_CONTEXT=0 python3 "$HOOK" </dev/null || true)
[[ -z "$OUT" ]] || { echo "FAIL: PAARTH_SESSION_CONTEXT=0 still emitted: $OUT"; exit 1; }

echo "test-hook-session-start: PASS"
