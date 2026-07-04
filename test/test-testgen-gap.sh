#!/usr/bin/env bash
# test/test-testgen-gap.sh — gap × LOC ranking
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/../bin/paarth-testgen"
FIXTURES="$SCRIPT_DIR/fixtures/testgen"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT

HOME="$TMPHOME" "$BIN" scan --fixture "$FIXTURES/jest-coverage-summary.json" >/dev/null

OUT=$(HOME="$TMPHOME" "$BIN" gap --top 5)
echo "$OUT" | grep -q "Coverage gaps" || { echo "FAIL: heading missing"; exit 1; }

# Expected ranking with threshold=70:
#   billing.ts: gap=10, loc=200, impact=2000  (largest)
#   auth.ts:    gap=7.5, loc=80,  impact=600
#   util.ts: 95% > 70%, excluded
# Verify billing.ts appears BEFORE auth.ts in the table
B_LINE=$(echo "$OUT" | grep -n "src/billing.ts" | head -1 | cut -d: -f1)
A_LINE=$(echo "$OUT" | grep -n "src/auth.ts" | head -1 | cut -d: -f1)
[[ -n "$B_LINE" && -n "$A_LINE" && "$B_LINE" -lt "$A_LINE" ]] \
  || { echo "FAIL: billing.ts must precede auth.ts (B=$B_LINE A=$A_LINE)"; echo "$OUT"; exit 1; }

# util.ts (95%) must NOT appear (no gap)
echo "$OUT" | grep -q "src/util.ts" \
  && { echo "FAIL: util.ts above threshold should not appear"; exit 1; } || true

echo "test-testgen-gap: PASS"
