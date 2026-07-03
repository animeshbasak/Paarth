#!/usr/bin/env bash
# test/test-income-skills.sh — income pack integrity: frontmatter convention,
# aidefence injection screen, no dangerous instructions.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."
AIDEF="$ROOT/bin/superagent-aidefence"

DIRS=("$ROOT"/skills/income-*/)
COUNT=0
for d in "${DIRS[@]}"; do
  [[ -d "$d" ]] || continue
  slug=$(basename "$d")                       # income-<name>
  short="${slug#income-}"                     # <name>
  f="$d/SKILL.md"
  [[ -f "$f" ]] || { echo "FAIL: $slug missing SKILL.md"; exit 1; }

  grep -q "^name: income:$short$" "$f" \
    || { echo "FAIL: $slug frontmatter name != income:$short"; exit 1; }
  grep -qE "^description: \"?\[income\]" "$f" \
    || { echo "FAIL: $slug description missing [income] prefix"; exit 1; }

  if grep -nE 'curl[^|]*\|[[:space:]]*(ba)?sh|base64 (-d|--decode)' "$f"; then
    echo "FAIL: $slug contains dangerous shell instruction"; exit 1
  fi

  VERDICT=$("$AIDEF" scan "$(cat "$f")" | jq -r '.safe')
  [[ "$VERDICT" == "true" ]] || { echo "FAIL: $slug aidefence flagged unsafe"; exit 1; }

  COUNT=$((COUNT + 1))
done

[[ "$COUNT" -ge 17 ]] || { echo "FAIL: expected >=17 income skills, found $COUNT"; exit 1; }

echo "test-income-skills: PASS ($COUNT skills screened)"
