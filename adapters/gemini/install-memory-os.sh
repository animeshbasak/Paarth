#!/usr/bin/env bash
# Gemini CLI adapter for PAARTH memory-os.
# Registers the MCP server via gemini-cli's standard MCP config and seeds a
# GEMINI.md preamble with the Ground Truth Hierarchy.
#
# Usage: bash adapters/gemini/install-memory-os.sh [--project <path>] [--uninstall]
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

GEMINI_USER_CONFIG="${HOME}/.gemini/settings.json"
GEMINI_MD="$TARGET/GEMINI.md"

echo ""
echo -e "${CYAN}PAARTH memory-os → Gemini CLI${NC}"
echo "Project: $TARGET"
echo ""

if [[ $UNINSTALL -eq 1 ]]; then
  mo_remove_gt "$GEMINI_MD"
  mo_warn "MCP entry in $GEMINI_USER_CONFIG left intact — remove manually if desired."
  exit 0
fi

if ! command -v gemini >/dev/null 2>&1; then
  mo_warn "gemini CLI not found on PATH. Install it first: https://github.com/google/gemini-cli"
  mo_info "Continuing with file-only install (MCP registration skipped)."
fi

# 1. Ensure MCP server is installed
MCP_BIN="$(mo_ensure_mcp_installed | tail -1)"

# 2. Register in user-level Gemini config
mo_register_mcp_in_json "$GEMINI_USER_CONFIG" "paarth-memory" "$MCP_BIN"

# 3. Inject Ground Truth block into project GEMINI.md
mo_inject_gt "$GEMINI_MD"

echo ""
mo_ok "Gemini CLI memory-os adapter installed."
mo_info "Verify with: gemini /mcp list"
mo_info "Restart any active gemini session to pick up the new MCP server."
echo ""
