#!/usr/bin/env bash
# test/test-rebrand.sh — v4.0 PAARTH rename is complete and consistent.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

# no old-name binaries, hooks, or skills remain
ls "$ROOT/bin" | grep -q "^superagent" && { echo "FAIL: superagent-* bin remains"; exit 1; }
ls "$ROOT/hooks" | grep -q "superagent" && { echo "FAIL: superagent hook remains"; exit 1; }
ls "$ROOT/skills" | grep -q "^superagent" && { echo "FAIL: superagent skill dir remains"; exit 1; }

# runtime surfaces carry no old identifiers
grep -rq "SUPERAGENT_" "$ROOT/bin" "$ROOT/hooks" --include="*" 2>/dev/null \
  && { echo "FAIL: SUPERAGENT_ env var in runtime code"; exit 1; }
grep -q "superagent" "$ROOT/hooks/hooks.json" && { echo "FAIL: hooks.json references old name"; exit 1; }

# brand assets
[[ -f "$ROOT/docs/media/hero-paarth.svg" ]] || { echo "FAIL: hero-paarth.svg missing"; exit 1; }
grep -q "hero-paarth.svg" "$ROOT/README.md" || { echo "FAIL: README does not reference new hero"; exit 1; }
grep -q "Proactive Agentic AI for Routing, Telemetry & Heuristics" "$ROOT/README.md" \
  || { echo "FAIL: acronym missing from README"; exit 1; }

# memory MCP identity
grep -q 'FastMCP("paarth-memory")' "$ROOT/bin/paarth-memory-mcp/memory_os/server.py" \
  || { echo "FAIL: MCP server name not renamed"; exit 1; }

# state migration present
grep -q 'HOME}/.superagent' "$ROOT/hooks/paarth-state-init.sh" \
  || { echo "FAIL: legacy state migration missing from state-init"; exit 1; }

echo "test-rebrand: PASS"
