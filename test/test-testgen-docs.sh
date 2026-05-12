#!/usr/bin/env bash
# test/test-testgen-docs.sh — testgen skill + slash + classifier rule
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -f "$ROOT/skills/testgen/SKILL.md" ]] || { echo "FAIL: SKILL.md missing"; exit 1; }
[[ -f "$ROOT/commands/testgen.md" ]] || { echo "FAIL: /testgen slash missing"; exit 1; }
grep -qE "never writes test bodies|skeleton names" "$ROOT/skills/testgen/SKILL.md" \
  || { echo "FAIL: no-test-bodies discipline not documented"; exit 1; }

OUT=$("$ROOT/bin/superagent-classify" "scan coverage and tell me where the gaps are")
echo "$OUT" | jq -e '.chain | index("testgen") != null' >/dev/null \
  || { echo "FAIL: classifier doesn't route to testgen: $OUT"; exit 1; }

echo "test-testgen-docs: PASS"
