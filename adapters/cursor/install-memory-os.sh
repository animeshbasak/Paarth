#!/usr/bin/env bash
# Cursor adapter for PAARTH memory-os.
# Registers the MCP server in cursor_settings.json and emits a project rule
# (.cursor/rules/memory-os.mdc) carrying the Ground Truth Hierarchy.
#
# Usage: bash adapters/cursor/install-memory-os.sh [--project <path>] [--uninstall]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/../_shared/memory-os-lib.sh"

UNINSTALL=0
TARGET="${PROJECT_DIR:-.}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --uninstall) UNINSTALL=1; shift ;;
    --project)   shift; TARGET="${1:-.}"; shift ;;
    *)           shift ;;
  esac
done
TARGET="$(cd "$TARGET" && pwd)"

CURSOR_CONFIG_USER="${HOME}/Library/Application Support/Cursor/User/cursor_settings.json"
CURSOR_RULES_DIR="$TARGET/.cursor/rules"
RULE_FILE="$CURSOR_RULES_DIR/memory-os.mdc"

echo ""
echo -e "${CYAN}PAARTH memory-os → Cursor${NC}"
echo "Project: $TARGET"
echo ""

if [[ $UNINSTALL -eq 1 ]]; then
  [[ -f "$RULE_FILE" ]] && rm "$RULE_FILE" && mo_ok "Removed $RULE_FILE"
  mo_warn "MCP entry in $CURSOR_CONFIG_USER left intact — remove manually if desired."
  exit 0
fi

# 1. Ensure MCP server is installed
MCP_BIN="$(mo_ensure_mcp_installed | tail -1)"

# 2. Register in user-level Cursor config (project-level cursor_settings.json
#    is not standard; user config covers all projects).
if [[ -d "$(dirname "$CURSOR_CONFIG_USER")" ]]; then
  mo_register_mcp_in_json "$CURSOR_CONFIG_USER" "paarth-memory" "$MCP_BIN"
else
  mo_warn "Cursor config dir not found at $(dirname "$CURSOR_CONFIG_USER"); skipping MCP registration."
  mo_info "When Cursor is installed, re-run this script."
fi

# 3. Emit the .mdc rule with the Ground Truth block + memory-tool reminders
mkdir -p "$CURSOR_RULES_DIR"
GT_BLOCK="$(mo_gt_block)"

cat > "$RULE_FILE" <<EOF
---
description: PAARTH memory-os — Ground Truth Hierarchy and memory tool usage policy.
globs: ["**/*"]
alwaysApply: true
---

# PAARTH Memory-OS

This project is wired into the PAARTH memory-os MCP server.

Tools available: \`memory_recall\`, \`memory_write\`, \`memory_list\`, \`memory_pin\`, \`memory_forget\`.

$(cat "$GT_BLOCK")
EOF

mo_ok "Wrote Cursor rule: $RULE_FILE"

echo ""
mo_ok "Cursor memory-os adapter installed."
mo_info "Restart Cursor to load the new MCP server."
mo_warn "Cursor MCP cap is ~40 tools — verify you're not over the limit."
echo ""
