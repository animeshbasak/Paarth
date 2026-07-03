#!/usr/bin/env bash
# Smoke test for safety invariant: distill hook MUST NOT touch CLAUDE.md.
# Covers both transcript schemas: simplified {"role","content"} and the real
# Claude Code shape {"message":{"role","content":[blocks]}}.
set -eu

HOOK="./hooks/superagent-distill.sh"
[[ -x "$HOOK" ]] || { echo "FAIL: hook not executable"; exit 1; }

TMPHOME=$(mktemp -d)
TMP_TRANSCRIPT=$(mktemp)
trap 'rm -rf "$TMPHOME" "$TMP_TRANSCRIPT" CLAUDE.md.superagent-proposed' EXIT

cat > "$TMP_TRANSCRIPT" <<'EOF'
{"role":"user","content":"no, don't use mocks in these tests"}
{"role":"assistant","content":"got it"}
EOF

BEFORE_HASH=""
[[ -f CLAUDE.md ]] && BEFORE_HASH=$(shasum -a 256 CLAUDE.md | cut -d' ' -f1)

echo "{\"transcript_path\":\"$TMP_TRANSCRIPT\"}" | HOME="$TMPHOME" bash "$HOOK"

AFTER_HASH=""
[[ -f CLAUDE.md ]] && AFTER_HASH=$(shasum -a 256 CLAUDE.md | cut -d' ' -f1)

if [[ "$BEFORE_HASH" != "$AFTER_HASH" ]]; then
  echo "FAIL: CLAUDE.md mutated"
  exit 1
fi

if [[ ! -f CLAUDE.md.superagent-proposed ]]; then
  echo "FAIL: no proposal file written"
  exit 1
fi

if ! grep -q "don't use mocks" CLAUDE.md.superagent-proposed; then
  echo "FAIL: proposal missing correction"
  exit 1
fi

LEARN_ROOT="$TMPHOME/.superagent/learnings"
PROJECT_HASH=$(printf '%s' "$PWD" | shasum -a 256 | cut -c1-12)
LEARN_FILE="$LEARN_ROOT/$PROJECT_HASH.jsonl"
if [[ ! -f "$LEARN_FILE" ]] || ! grep -q "don't use mocks" "$LEARN_FILE"; then
  echo "FAIL: learnings jsonl missing entry"
  exit 1
fi

# ── real Claude Code schema: nested .message.role / block-array content ──────
cat > "$TMP_TRANSCRIPT" <<'EOF'
{"type":"user","message":{"role":"user","content":"never commit directly to main in this repo"}}
{"type":"user","message":{"role":"user","content":[{"type":"text","text":"actually the flag lives in config.yaml not env"}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"noted"}]}}
EOF

echo "{\"transcript_path\":\"$TMP_TRANSCRIPT\"}" | HOME="$TMPHOME" bash "$HOOK"

if ! grep -q "never commit directly to main" CLAUDE.md.superagent-proposed; then
  echo "FAIL: real-schema string correction not extracted"
  exit 1
fi
if ! grep -q "actually the flag lives in config.yaml" CLAUDE.md.superagent-proposed; then
  echo "FAIL: real-schema block-array correction not extracted"
  exit 1
fi

echo "PASS: 6 invariants held"
