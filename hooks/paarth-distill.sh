#!/usr/bin/env bash
# Stop hook: distills correction signals from transcript into CLAUDE.md.paarth-proposed
#   AND appends to ~/.paarth/learnings/<project-hash>.jsonl.
#
# SAFETY: never mutates CLAUDE.md directly. v2.0 writes proposals only.
# Exit 0 always — never block the session.

set -eu

PAYLOAD=$(cat 2>/dev/null || echo '{}')

# ── Wave 1: pattern store maintenance (runs unconditionally) ──────────────────
# Resolve paarth-patterns: prefer PATH, then script-relative bin/.
PATBIN=""
if command -v paarth-patterns >/dev/null 2>&1; then
  PATBIN="$(command -v paarth-patterns)"
elif [[ -x "$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-patterns" ]]; then
  PATBIN="$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-patterns"
fi

if [[ -n "$PATBIN" ]]; then
  "$PATBIN" promote >/dev/null 2>&1 || true
  "$PATBIN" decay   >/dev/null 2>&1 || true
fi

# ── Wave 2: observability daily rotation (idempotent per-day marker) ──────────
ROTATE_BIN=""
if command -v paarth-obs-rotate >/dev/null 2>&1; then
  ROTATE_BIN="$(command -v paarth-obs-rotate)"
elif [[ -x "$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-obs-rotate" ]]; then
  ROTATE_BIN="$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-obs-rotate"
fi
[[ -n "$ROTATE_BIN" ]] && "$ROTATE_BIN" >/dev/null 2>&1 || true

# ── Wave 3: session auto-capture into memory-os ───────────────────────────────
# Kill switch: PAARTH_AUTO_CAPTURE=0|false|off (checked inside the bin too).
CAPTURE_BIN=""
if command -v paarth-capture >/dev/null 2>&1; then
  CAPTURE_BIN="$(command -v paarth-capture)"
elif [[ -x "$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-capture" ]]; then
  CAPTURE_BIN="$(dirname "${BASH_SOURCE[0]}")/../bin/paarth-capture"
fi
[[ -n "$CAPTURE_BIN" ]] && printf '%s' "$PAYLOAD" | "$CAPTURE_BIN" >/dev/null 2>&1 || true

TRANSCRIPT=$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // empty' 2>/dev/null || echo "")
[[ -n "$TRANSCRIPT" && -f "$TRANSCRIPT" ]] || exit 0

CORRECTIONS=$(tail -n 400 "$TRANSCRIPT" 2>/dev/null \
  | jq -r 'select((.message.role // .role) == "user")
           | (.message.content // .content // empty)
           | if type == "array" then (map(select(.type? == "text") | .text) | join(" ")) else . end' 2>/dev/null \
  | grep -iE "^(no[,. ]|don't|stop|never|actually|wrong|not like that|do not )" \
  | head -5 || true)

[[ -z "$CORRECTIONS" ]] && exit 0

DATE=$(date -I 2>/dev/null || date +%Y-%m-%d)

# Write 1: proposed additions (never mutate CLAUDE.md directly)
PROPOSAL_FILE="$PWD/CLAUDE.md.paarth-proposed"
MARK="<!-- paarth:auto-learnings -->"

if [[ ! -f "$PROPOSAL_FILE" ]]; then
  printf '# Proposed CLAUDE.md additions from PAARTH distill hook\n\n' > "$PROPOSAL_FILE"
  printf '%s\n## Auto-distilled learnings\n\n' "$MARK" >> "$PROPOSAL_FILE"
fi

while IFS= read -r c; do
  [[ -z "$c" ]] && continue
  FIRST40=$(printf '%s' "$c" | head -c 40)
  if ! grep -qF "$FIRST40" "$PROPOSAL_FILE" 2>/dev/null; then
    printf -- '- (%s) %s\n' "$DATE" "$(printf '%s' "$c" | head -c 200)" >> "$PROPOSAL_FILE"
  fi
done <<< "$CORRECTIONS"

# Write 2: structured jsonl to ~/.paarth/learnings/<project-hash>.jsonl
LEARN_ROOT="$HOME/.paarth/learnings"
mkdir -p "$LEARN_ROOT"
PROJECT_HASH=$( (printf '%s' "$PWD" | shasum -a 256 2>/dev/null) || (printf '%s' "$PWD" | sha256sum 2>/dev/null) )
PROJECT_HASH=$(printf '%s' "$PROJECT_HASH" | cut -c1-12)
LEARN_FILE="$LEARN_ROOT/$PROJECT_HASH.jsonl"

while IFS= read -r c; do
  [[ -z "$c" ]] && continue
  TS=$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)
  printf '%s' "$c" | jq -Rs --arg ts "$TS" --arg proj "$PWD" --arg src "auto-distill" \
    '{ts: $ts, project: $proj, source: $src, text: .}' >> "$LEARN_FILE" 2>/dev/null || true
done <<< "$CORRECTIONS"

exit 0
