#!/usr/bin/env bash
# Claude Code adapter for SuperAgent memory-os.
# Registers the MCP server, installs SessionStart/Stop hooks, and injects the
# Ground Truth Hierarchy into ~/.claude/CLAUDE.md.
#
# Usage: bash adapters/claude-code/install-memory-os.sh [--uninstall]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/../_shared/memory-os-lib.sh"

UNINSTALL=0
[[ "${1:-}" == "--uninstall" ]] && UNINSTALL=1

CLAUDE_JSON="${HOME}/.claude.json"
CLAUDE_MD="${HOME}/.claude/CLAUDE.md"
HOOKS_DIR="${HOME}/.claude/hooks/memory-os"

echo ""
echo -e "${CYAN}SuperAgent memory-os → Claude Code${NC}"
echo ""

if [[ $UNINSTALL -eq 1 ]]; then
  mo_remove_gt "$CLAUDE_MD"
  rm -rf "$HOOKS_DIR"
  mo_ok "Removed hooks dir $HOOKS_DIR (MCP entry in ~/.claude.json left intact — remove manually if desired)"
  exit 0
fi

# 1. Ensure MCP server is installed
MCP_BIN="$(mo_ensure_mcp_installed | tail -1)"

# 2. Register in ~/.claude.json
mo_register_mcp_in_json "$CLAUDE_JSON" "superagent-memory" "$MCP_BIN"

# 3. Install lifecycle hook scripts
mkdir -p "$HOOKS_DIR"

cat > "$HOOKS_DIR/session-start.sh" <<'HOOK'
#!/usr/bin/env bash
# memory-os SessionStart hook — recalls workspace memory.
# Output is appended as additional context to the session.
set -e
MCP_BIN="${SUPERAGENT_MEMORY_BIN:-superagent-memory-mcp}"
NS="$(git rev-parse --show-toplevel 2>/dev/null | shasum -a 256 | cut -c1-16 || echo __global__)"
# Emit a brief recall summary so the agent sees workspace state on start.
echo "## SuperAgent Memory-OS wake-up"
echo "Namespace: ${NS}"
echo "Tools available via MCP server 'superagent-memory': memory_recall, memory_write, memory_list, memory_pin, memory_forget"
HOOK
chmod +x "$HOOKS_DIR/session-start.sh"

cat > "$HOOKS_DIR/stop.sh" <<'HOOK'
#!/usr/bin/env bash
# memory-os Stop hook — placeholder for session-end distillation.
# Currently a no-op; agent is encouraged to call memory_write before stopping.
exit 0
HOOK
chmod +x "$HOOKS_DIR/stop.sh"

mo_ok "Installed lifecycle hooks under $HOOKS_DIR"
mo_warn "To wire the SessionStart hook, add this to ~/.claude/settings.json under hooks:"
cat <<EOF
  {
    "hooks": {
      "SessionStart": [
        { "type": "command", "command": "$HOOKS_DIR/session-start.sh" }
      ],
      "Stop": [
        { "type": "command", "command": "$HOOKS_DIR/stop.sh" }
      ]
    }
  }
EOF

# 4. Inject Ground Truth block
mo_inject_gt "$CLAUDE_MD"

echo ""
mo_ok "Claude Code memory-os adapter installed."
mo_info "Restart Claude Code to load the new MCP server."
echo ""
