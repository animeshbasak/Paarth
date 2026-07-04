#!/usr/bin/env bash
# Antigravity adapter for PAARTH memory-os (EXPERIMENTAL).
#
# Antigravity's extensibility surface is still in flux as of 2026-06. This
# adapter installs the MCP server and emits a Skill manifest in the format
# Antigravity loads from ~/.gemini/antigravity/skills/. Verify against the
# Antigravity docs for your installed version before relying on it.
#
# Usage: bash adapters/antigravity/install-memory-os.sh [--uninstall]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$SCRIPT_DIR/../_shared/memory-os-lib.sh"

UNINSTALL=0
[[ "${1:-}" == "--uninstall" ]] && UNINSTALL=1

ANTIGRAVITY_SKILLS_DIR="${HOME}/.gemini/antigravity/skills/paarth-memory"
ANTIGRAVITY_MCP_CONFIG="${HOME}/.gemini/antigravity/settings.json"

echo ""
echo -e "${CYAN}PAARTH memory-os → Antigravity${NC} ${YELLOW}(experimental)${NC}"
echo ""

if [[ $UNINSTALL -eq 1 ]]; then
  rm -rf "$ANTIGRAVITY_SKILLS_DIR"
  mo_ok "Removed skill dir $ANTIGRAVITY_SKILLS_DIR"
  exit 0
fi

# 1. Ensure MCP server is installed
MCP_BIN="$(mo_ensure_mcp_installed | tail -1)"

# 2. Register MCP server (best-effort — config path may vary by Antigravity version)
if [[ -d "$(dirname "$ANTIGRAVITY_MCP_CONFIG")" ]]; then
  mo_register_mcp_in_json "$ANTIGRAVITY_MCP_CONFIG" "paarth-memory" "$MCP_BIN"
else
  mo_warn "Antigravity config dir not found at $(dirname "$ANTIGRAVITY_MCP_CONFIG"); skipping MCP registration."
  mo_info "Manually register the MCP server with command: $MCP_BIN"
fi

# 3. Emit Skill manifest with Ground Truth block
mkdir -p "$ANTIGRAVITY_SKILLS_DIR"
GT_BLOCK="$(mo_gt_block)"

cat > "$ANTIGRAVITY_SKILLS_DIR/SKILL.md" <<EOF
---
name: paarth-memory
description: Persistent multi-tier memory for Antigravity sessions via the PAARTH memory-os MCP server. Activate whenever a task references prior decisions, recorded preferences, project context, or anything previously discussed.
version: 0.1.0
experimental: true
triggers:
  - "recall what we decided about X"
  - "remember when we"
  - "previous discussion about"
  - "the user mentioned"
---

# PAARTH Memory-OS

This skill exposes the memory-os MCP server. The five tools — \`memory_recall\`, \`memory_write\`, \`memory_list\`, \`memory_pin\`, \`memory_forget\` — are namespaced by git root.

$(cat "$GT_BLOCK")
EOF

mo_ok "Wrote Antigravity skill: $ANTIGRAVITY_SKILLS_DIR/SKILL.md"

echo ""
mo_warn "EXPERIMENTAL: Antigravity API surface is unstable. Verify after each Antigravity update."
mo_ok "Antigravity memory-os adapter installed."
echo ""
