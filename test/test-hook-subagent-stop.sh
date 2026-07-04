#!/usr/bin/env bash
# test/test-hook-subagent-stop.sh — appends a subagent-flagged route record
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$SCRIPT_DIR/../hooks/paarth-subagent-stop.py"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
mkdir -p "$TMPHOME/.paarth/brain"
: > "$TMPHOME/.paarth/brain/routes.jsonl"

PAYLOAD='{"hook_event_name":"SubagentStop","session_id":"s","stop_hook_active":false,"transcript_path":"/tmp/x","tool_input":{"description":"refactor auth module"},"tool_output":{"success":true}}'
HOME="$TMPHOME" python3 "$HOOK" <<<"$PAYLOAD" >/dev/null

LAST=$(tail -n1 "$TMPHOME/.paarth/brain/routes.jsonl")
echo "$LAST" | jq -e '.subagent == true and .outcome == "done"' >/dev/null \
  || { echo "FAIL: subagent-stop record shape: $LAST"; exit 1; }

# A stop with no description must NOT be logged — it is pure noise.
COUNT_BEFORE=$(wc -l < "$TMPHOME/.paarth/brain/routes.jsonl")
NODESC='{"hook_event_name":"SubagentStop","session_id":"s","tool_input":{},"tool_output":{"success":true}}'
HOME="$TMPHOME" python3 "$HOOK" <<<"$NODESC" >/dev/null
EMPTYDESC='{"hook_event_name":"SubagentStop","session_id":"s","tool_input":{"description":"   "},"tool_output":{"success":true}}'
HOME="$TMPHOME" python3 "$HOOK" <<<"$EMPTYDESC" >/dev/null
COUNT_AFTER=$(wc -l < "$TMPHOME/.paarth/brain/routes.jsonl")
[ "$COUNT_BEFORE" -eq "$COUNT_AFTER" ] \
  || { echo "FAIL: empty-description stop was logged ($COUNT_BEFORE -> $COUNT_AFTER)"; exit 1; }

echo "test-hook-subagent-stop: PASS"
