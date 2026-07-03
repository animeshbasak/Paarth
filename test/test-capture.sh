#!/usr/bin/env bash
# test/test-capture.sh — session auto-capture writes memory-os entries,
# upserts per session, and honors the kill switch.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CAPBIN="$SCRIPT_DIR/../bin/superagent-capture"
FIXTURE="$SCRIPT_DIR/fixtures/transcript-real.jsonl"

TMPHOME=$(mktemp -d)
trap 'rm -rf "$TMPHOME"' EXIT
DB="$TMPHOME/.superagent/memory-os/memory.db"

PAYLOAD=$(jq -cn --arg t "$FIXTURE" --arg c "$TMPHOME" \
  '{"hook_event_name":"Stop","session_id":"s-cap-1","transcript_path":$t,"cwd":$c}')

# 1) capture writes a session entry + decision + feedback
HOME="$TMPHOME" python3 "$CAPBIN" <<<"$PAYLOAD"
SESSIONS=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='session' AND forgotten=0")
[[ "$SESSIONS" == "1" ]] || { echo "FAIL: expected 1 session entry, got $SESSIONS"; exit 1; }

sqlite3 "$DB" "SELECT content FROM entries WHERE kind='session' AND forgotten=0" | grep -q "retry wrapper" \
  || { echo "FAIL: session summary missing first prompt"; exit 1; }
sqlite3 "$DB" "SELECT content FROM entries WHERE kind='session' AND forgotten=0" | grep -q "sync.py" \
  || { echo "FAIL: session summary missing edited files"; exit 1; }

DECISIONS=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='decision' AND forgotten=0")
[[ "$DECISIONS" == "1" ]] || { echo "FAIL: expected 1 decision, got $DECISIONS"; exit 1; }
sqlite3 "$DB" "SELECT content FROM entries WHERE kind='decision'" | grep -qi "exponential backoff" \
  || { echo "FAIL: decision content wrong"; exit 1; }

FEEDBACK=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='feedback' AND forgotten=0")
[[ "$FEEDBACK" == "1" ]] || { echo "FAIL: expected 1 feedback, got $FEEDBACK"; exit 1; }

sqlite3 "$DB" "SELECT tags_json FROM entries WHERE kind='session' AND forgotten=0" | grep -q 'session:s-cap-1' \
  || { echo "FAIL: session tag missing"; exit 1; }

# 2) upsert: second Stop for the same session leaves exactly 1 live session entry
HOME="$TMPHOME" python3 "$CAPBIN" <<<"$PAYLOAD"
LIVE=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='session' AND forgotten=0")
[[ "$LIVE" == "1" ]] || { echo "FAIL: upsert broken — $LIVE live session entries"; exit 1; }
GONE=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='session' AND forgotten=1")
[[ "$GONE" -ge "1" ]] || { echo "FAIL: prior session entry not forgotten"; exit 1; }

# 3) different session id -> its own live entry
PAYLOAD2=$(jq -cn --arg t "$FIXTURE" --arg c "$TMPHOME" \
  '{"hook_event_name":"Stop","session_id":"s-cap-2","transcript_path":$t,"cwd":$c}')
HOME="$TMPHOME" python3 "$CAPBIN" <<<"$PAYLOAD2"
LIVE=$(sqlite3 "$DB" "SELECT COUNT(*) FROM entries WHERE kind='session' AND forgotten=0")
[[ "$LIVE" == "2" ]] || { echo "FAIL: expected 2 live sessions across ids, got $LIVE"; exit 1; }

# 4) kill switch -> no writes
T2=$(mktemp -d)
HOME="$T2" SUPERAGENT_AUTO_CAPTURE=0 python3 "$CAPBIN" <<<"$PAYLOAD"
[[ ! -f "$T2/.superagent/memory-os/memory.db" ]] || { echo "FAIL: kill switch ignored"; rm -rf "$T2"; exit 1; }
rm -rf "$T2"

# 5) missing transcript -> exit 0, no crash
echo '{"hook_event_name":"Stop","session_id":"x","transcript_path":"/nonexistent"}' \
  | HOME="$TMPHOME" python3 "$CAPBIN" || { echo "FAIL: nonzero exit on missing transcript"; exit 1; }

echo "test-capture: PASS"
