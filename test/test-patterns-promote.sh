#!/usr/bin/env bash
# test/test-patterns-promote.sh — promote groups by chain (not task wording),
# learns from halt/fail outcomes, and stays idempotent.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATBIN="$SCRIPT_DIR/../bin/superagent-patterns"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
mkdir -p "$TMPHOME/.superagent/brain"
: > "$TMPHOME/.superagent/brain/patterns.jsonl"

TS=$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)
# Three DIFFERENTLY-worded tasks sharing one chain — the real-world shape that
# the old wording-fingerprint grouping could never promote.
cat > "$TMPHOME/.superagent/brain/routes.jsonl" <<JSONL
{"ts":"$TS","task_hash":"abc","task":"fix bug in dark mode toggle","chain":["systematic-debugging","tdd"],"outcome":"done","backend":"anthropic"}
{"ts":"$TS","task_hash":"ghi","task":"login crash on submit needs root cause","chain":["systematic-debugging","tdd"],"outcome":"done","backend":"anthropic"}
{"ts":"$TS","task_hash":"jkl","task":"resolve flaky checkout error","chain":["systematic-debugging","tdd"],"outcome":"done","backend":"anthropic"}
{"ts":"$TS","task_hash":"def","task":"this one should be ignored — only 1 occurrence","chain":["random"],"outcome":"done","backend":"anthropic"}
JSONL

HOME="$TMPHOME" "$PATBIN" promote >/dev/null

LINES=$(wc -l < "$TMPHOME/.superagent/brain/patterns.jsonl" | tr -d ' ')
[[ "$LINES" == "1" ]] || { echo "FAIL: expected 1 pattern, got $LINES"; cat "$TMPHOME/.superagent/brain/patterns.jsonl"; exit 1; }

REC=$(cat "$TMPHOME/.superagent/brain/patterns.jsonl")
# 3 done, 0 fail: sr = (3 + 0.6*2) / (3 + 2) = 0.84
echo "$REC" | jq -e '.useCount == 3 and .successRate == 0.84 and (.chain == ["systematic-debugging","tdd"])' >/dev/null \
  || { echo "FAIL: pattern record shape wrong: $REC"; exit 1; }

HOME="$TMPHOME" "$PATBIN" promote >/dev/null
LINES2=$(wc -l < "$TMPHOME/.superagent/brain/patterns.jsonl" | tr -d ' ')
[[ "$LINES2" == "1" ]] || { echo "FAIL: dedup broken on second run, got $LINES2 lines"; exit 1; }

# A halt in the same chain plus a 4th done: sr = (4 + 1.2) / (5 + 2) ≈ 0.7429
cat >> "$TMPHOME/.superagent/brain/routes.jsonl" <<JSONL
{"ts":"$TS","task_hash":"mno","task":"debug broken pagination","chain":["systematic-debugging","tdd"],"outcome":"halt","backend":"anthropic"}
{"ts":"$TS","task_hash":"pqr","task":"traceback in export job","chain":["systematic-debugging","tdd"],"outcome":"done","backend":"anthropic"}
JSONL
HOME="$TMPHOME" "$PATBIN" promote >/dev/null
REC2=$(grep '"systematic-debugging"' "$TMPHOME/.superagent/brain/patterns.jsonl")
echo "$REC2" | jq -e '.useCount == 4 and (.successRate > 0.74 and .successRate < 0.75)' >/dev/null \
  || { echo "FAIL: halt outcome not blended into successRate: $REC2"; exit 1; }

echo "test-patterns-promote: PASS"
