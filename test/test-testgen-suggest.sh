#!/usr/bin/env bash
# test/test-testgen-suggest.sh — markdown skeleton names tests for uncovered ranges + named symbols
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$SCRIPT_DIR/../bin/paarth-testgen"
FIXTURES="$SCRIPT_DIR/fixtures/testgen"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT

HOME="$TMPHOME" "$BIN" scan --fixture "$FIXTURES/jest-coverage-summary.json" >/dev/null

# Use the sample source so symbol extraction has something to chew on
cp -r "$FIXTURES/sample-src" "$TMPHOME/src"
cd "$TMPHOME"

OUT=$(HOME="$TMPHOME" "$BIN" suggest "src/auth.ts")

# Heading mentions current coverage and target
echo "$OUT" | grep -q "62" || { echo "FAIL: missing current coverage"; exit 1; }
echo "$OUT" | grep -q "target 70" || { echo "FAIL: missing target"; exit 1; }

# Uncovered ranges collapsed into L42-50, L91-103, L124
echo "$OUT" | grep -qE 'L42-50|L42-49' || { echo "FAIL: range L42-50 missing"; exit 1; }
echo "$OUT" | grep -qE 'L91-103|L91-102' || { echo "FAIL: range L91-103 missing"; exit 1; }
echo "$OUT" | grep -q "L124" || { echo "FAIL: line L124 missing"; exit 1; }

# Suggested test names reference at least one exported symbol
echo "$OUT" | grep -qE 'should_(authenticate|verifytoken|refreshsession|autherror|isadmin)' \
  || { echo "FAIL: no symbol-based test name suggestions"; exit 1; }

# Hands off to tester agent
echo "$OUT" | grep -qE 'tester|test-driven-development' \
  || { echo "FAIL: hand-off note missing"; exit 1; }

echo "test-testgen-suggest: PASS"
