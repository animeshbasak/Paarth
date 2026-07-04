#!/usr/bin/env bash
# test/test-testgen-status.sh — status reports coverage vs threshold
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/../bin/paarth-testgen"
FIXTURES="$SCRIPT_DIR/fixtures/testgen"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT

# No report yet → hasReport:false JSON
OUT=$(HOME="$TMPHOME" "$BIN" status --json)
echo "$OUT" | jq -e '.hasReport == false' >/dev/null \
  || { echo "FAIL: status before scan should hasReport:false"; exit 1; }

HOME="$TMPHOME" "$BIN" scan --fixture "$FIXTURES/jest-coverage-summary.json" >/dev/null

# Default threshold 70, jest fixture is 75% → OK verdict
OUT=$(HOME="$TMPHOME" "$BIN" status)
echo "$OUT" | grep -q "coverage: 75" || { echo "FAIL: coverage line missing"; exit 1; }
echo "$OUT" | grep -q "verdict: OK" || { echo "FAIL: OK verdict missing"; exit 1; }

# Raise threshold to 80 → verdict flips to BELOW THRESHOLD
echo 80 > "$TMPHOME/.paarth/testgen/min-coverage.txt"
OUT_BAD=$(HOME="$TMPHOME" "$BIN" status)
echo "$OUT_BAD" | grep -q "verdict: BELOW THRESHOLD" \
  || { echo "FAIL: threshold-not-met verdict missing: $OUT_BAD"; exit 1; }

# JSON mode carries the threshold
OUT_JSON=$(HOME="$TMPHOME" "$BIN" status --json)
echo "$OUT_JSON" | jq -e '.threshold == 80 and .hasReport == true' >/dev/null \
  || { echo "FAIL: JSON threshold: $OUT_JSON"; exit 1; }

echo "test-testgen-status: PASS"
