#!/usr/bin/env bash
# test/test-state-init.sh — verify state-init creates all Wave 1 paths
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INIT_SCRIPT="$SCRIPT_DIR/../hooks/paarth-state-init.sh"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
HOME="$TMPHOME" bash "$INIT_SCRIPT" > /dev/null

EXPECTED=(
  "$TMPHOME/.paarth/brain/patterns.jsonl"
  "$TMPHOME/.paarth/brain/protected-patterns.jsonl"
  "$TMPHOME/.paarth/cost/budget.json"
  "$TMPHOME/.paarth/cost/alerts.jsonl"
  "$TMPHOME/.paarth/defaults.toml"
)

fail=0
for path in "${EXPECTED[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "FAIL: missing $path"
    fail=1
  fi
done

# budget.json must be valid JSON with daily_usd
if ! jq -e '.daily_usd > 0' "$TMPHOME/.paarth/cost/budget.json" >/dev/null 2>&1; then
  echo "FAIL: budget.json missing daily_usd"
  fail=1
fi

# defaults.toml must contain [learning] section
if ! grep -q '^\[learning\]' "$TMPHOME/.paarth/defaults.toml"; then
  echo "FAIL: defaults.toml missing [learning] section"
  fail=1
fi

[[ $fail -eq 0 ]] && echo "test-state-init: PASS" || { echo "test-state-init: FAIL"; exit 1; }
