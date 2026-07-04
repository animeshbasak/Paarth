#!/usr/bin/env bash
# test/test-hook-prompt-submit.sh — UserPromptSubmit hook returns valid Claude Code output
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$SCRIPT_DIR/../hooks/paarth-prompt-submit.py"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
mkdir -p "$TMPHOME/.paarth/brain"
: > "$TMPHOME/.paarth/brain/routes.jsonl"
: > "$TMPHOME/.paarth/brain/patterns.jsonl"

PAYLOAD='{"session_id":"s-1","transcript_path":"/tmp/x","cwd":"/tmp","permission_mode":"default","hook_event_name":"UserPromptSubmit","prompt":"fix dark mode toggle bug"}'

OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" python3 "$HOOK" <<<"$PAYLOAD")

echo "$OUT" | jq -e '.hookSpecificOutput.hookEventName == "UserPromptSubmit"' >/dev/null \
  || { echo "FAIL: invalid hook output: $OUT"; exit 1; }

echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | type == "string"' >/dev/null \
  || { echo "FAIL: additionalContext missing or not a string"; exit 1; }

echo '{"session_id":"s","prompt":""}' | HOME="$TMPHOME" python3 "$HOOK" >/dev/null

# filler-heavy prompt → hook injects an optimized-prompt block
PAYLOAD='{"session_id":"s-2","hook_event_name":"UserPromptSubmit","prompt":"could you please fix the dark mode toggle bug?"}'
OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" python3 "$HOOK" <<<"$PAYLOAD")

echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## Optimized prompt")' >/dev/null \
  || { echo "FAIL: optimized prompt block missing: $OUT"; exit 1; }

echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("Fix the dark mode toggle bug.")' >/dev/null \
  || { echo "FAIL: optimized text missing: $OUT"; exit 1; }

# already-clean prompt → no optimization block
PAYLOAD='{"session_id":"s-3","hook_event_name":"UserPromptSubmit","prompt":"Fix the dark mode toggle bug."}'
OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" python3 "$HOOK" <<<"$PAYLOAD")

echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## Optimized prompt") | not' >/dev/null \
  || { echo "FAIL: unexpected optimization block on clean prompt: $OUT"; exit 1; }

# ── adaptive injection budget ────────────────────────────────────────────────
# Filler-heavy LONG prompt: optimizer fires, but the optimized block (~>750
# est. tokens) blows the 600-token default budget → dropped whole; route block stays.
LONG="could you please fix the dark mode toggle bug? $(printf 'detail %.0s' {1..500})"
PAYLOAD=$(jq -cn --arg p "$LONG" '{"session_id":"s-4","hook_event_name":"UserPromptSubmit","prompt":$p}')
OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" python3 "$HOOK" <<<"$PAYLOAD")

echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## Optimized prompt") | not' >/dev/null \
  || { echo "FAIL: over-budget optimized block not dropped"; exit 1; }
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## PAARTH route")' >/dev/null \
  || { echo "FAIL: route block missing when optimized block dropped: $OUT"; exit 1; }
jq -e '.event == "inject_budget" and .est_saved_tokens > 600' "$TMPHOME/.paarth/metrics/inject.jsonl" >/dev/null \
  || { echo "FAIL: inject_budget savings not recorded"; exit 1; }

# Kill switch → uncapped, block present again
OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" PAARTH_INJECT_BUDGET=0 python3 "$HOOK" <<<"$PAYLOAD")
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## Optimized prompt")' >/dev/null \
  || { echo "FAIL: kill switch did not disable budget"; exit 1; }

# Generous budget → block present
OUT=$(HOME="$TMPHOME" PATH="$SCRIPT_DIR/../bin:$PATH" PAARTH_INJECT_BUDGET_TOKENS=5000 python3 "$HOOK" <<<"$PAYLOAD")
echo "$OUT" | jq -e '.hookSpecificOutput.additionalContext | contains("## Optimized prompt")' >/dev/null \
  || { echo "FAIL: block dropped despite generous budget"; exit 1; }

echo "test-hook-prompt-submit: PASS"
