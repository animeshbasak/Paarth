#!/usr/bin/env bash
# test/test-testgen-scan.sh — parses jest + pytest fixtures into normalized last-report.json
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/../bin/paarth-testgen"
FIXTURES="$SCRIPT_DIR/fixtures/testgen"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT

HOME="$TMPHOME" "$BIN" scan --fixture "$FIXTURES/jest-coverage-summary.json" >/dev/null
JEST=$(cat "$TMPHOME/.paarth/testgen/last-report.json")
echo "$JEST" | jq -e '.format == "jest" and .total.coverage == 75.0 and (.files["src/auth.ts"].uncovered | length) >= 20' >/dev/null \
  || { echo "FAIL: jest parse: $JEST"; exit 1; }

HOME="$TMPHOME" "$BIN" scan --fixture "$FIXTURES/pytest-cov.json" >/dev/null
PYT=$(cat "$TMPHOME/.paarth/testgen/last-report.json")
echo "$PYT" | jq -e '.format == "pytest" and .total.coverage > 70 and .total.coverage < 71 and (.files | length) == 3' >/dev/null \
  || { echo "FAIL: pytest parse: $PYT"; exit 1; }

echo "test-testgen-scan: PASS"
