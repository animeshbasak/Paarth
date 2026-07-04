#!/usr/bin/env bash
# GitHub Copilot adapter for PAARTH memory-os (EXPERIMENTAL).
#
# Copilot does not natively support MCP servers (as of 2026-06). This adapter:
#   1. Installs the MCP server binary (so Copilot SDK extensions or other
#      tools can subprocess it).
#   2. Generates a Copilot SDK shim TypeScript stub under adapters/copilot/sdk-shim/
#      that bridges Copilot's tool API to the MCP stdio server.
#   3. Injects the Ground Truth Hierarchy into the project's copilot-instructions.md.
#   4. Writes a placeholder .github/hooks/session-start.json that invokes the shim.
#
# The SDK shim is a stub — wire it into your Copilot extension to enable the
# memory tools. Revisit when Copilot ships native MCP support.
#
# Usage: bash adapters/copilot/install-memory-os.sh [--project <path>] [--uninstall]
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

COPILOT_INSTRUCTIONS="$TARGET/.github/copilot-instructions.md"
HOOKS_DIR="$TARGET/.github/hooks"
SHIM_DIR="$SCRIPT_DIR/sdk-shim"

echo ""
echo -e "${CYAN}PAARTH memory-os → GitHub Copilot${NC} ${YELLOW}(experimental)${NC}"
echo "Project: $TARGET"
echo ""

if [[ $UNINSTALL -eq 1 ]]; then
  mo_remove_gt "$COPILOT_INSTRUCTIONS"
  [[ -f "$HOOKS_DIR/session-start-memory-os.json" ]] && rm "$HOOKS_DIR/session-start-memory-os.json"
  mo_ok "Uninstalled. SDK shim under $SHIM_DIR left intact (shared repo asset)."
  exit 0
fi

# 1. Ensure MCP server is installed
MCP_BIN="$(mo_ensure_mcp_installed | tail -1)"

# 2. Inject Ground Truth into copilot-instructions.md
mo_inject_gt "$COPILOT_INSTRUCTIONS"

# 3. Emit SDK shim stub (TypeScript)
mkdir -p "$SHIM_DIR"
if [[ ! -f "$SHIM_DIR/index.ts" ]]; then
  cat > "$SHIM_DIR/index.ts" <<'TS'
/**
 * PAARTH memory-os → Copilot SDK shim (stub).
 *
 * Copilot does not natively support MCP servers. This shim wraps the
 * Python MCP server in stdio and exposes its 5 tools as Copilot SDK tools.
 *
 * Wire into your Copilot extension's tool registry:
 *
 *   import { memoryOsTools } from "./adapters/copilot/sdk-shim";
 *   copilot.registerTools(memoryOsTools);
 *
 * Revisit when Copilot ships native MCP support.
 */
import { spawn } from "node:child_process";

const MCP_BIN = process.env.PAARTH_MEMORY_BIN || "paarth-memory-mcp";

interface McpResponse {
  result?: unknown;
  error?: { code: number; message: string };
}

async function callMcp(method: string, params: Record<string, unknown>): Promise<McpResponse> {
  return new Promise((resolve, reject) => {
    const proc = spawn(MCP_BIN, [], { stdio: ["pipe", "pipe", "inherit"] });
    let out = "";
    proc.stdout.on("data", (d) => (out += d.toString()));
    proc.on("close", () => {
      try {
        const lines = out.trim().split("\n").filter(Boolean);
        const last = JSON.parse(lines[lines.length - 1]);
        resolve(last);
      } catch (e) {
        reject(e);
      }
    });
    proc.stdin.write(JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "tools/call",
      params: { name: method, arguments: params },
    }) + "\n");
    proc.stdin.end();
  });
}

export const memoryOsTools = [
  {
    name: "memory_recall",
    description: "Search persistent memory for entries matching a query.",
    parameters: { query: "string", limit: "number?" },
    handler: (args: Record<string, unknown>) => callMcp("memory_recall", args),
  },
  {
    name: "memory_write",
    description: "Store content in persistent memory.",
    parameters: { content: "string", kind: "string", tags: "string[]?" },
    handler: (args: Record<string, unknown>) => callMcp("memory_write", args),
  },
  {
    name: "memory_list",
    description: "List recent memory entries.",
    parameters: { kind: "string?", since: "number?", limit: "number?" },
    handler: (args: Record<string, unknown>) => callMcp("memory_list", args),
  },
  {
    name: "memory_pin",
    description: "Promote a memory entry to the workspace.",
    parameters: { entry_id: "string" },
    handler: (args: Record<string, unknown>) => callMcp("memory_pin", args),
  },
  {
    name: "memory_forget",
    description: "Soft-delete memory by id or content pattern.",
    parameters: { id_or_pattern: "string" },
    handler: (args: Record<string, unknown>) => callMcp("memory_forget", args),
  },
];
TS
  mo_ok "Wrote SDK shim stub: $SHIM_DIR/index.ts"
else
  mo_ok "SDK shim already present: $SHIM_DIR/index.ts (kept as-is)"
fi

# 4. Emit hook placeholder
mkdir -p "$HOOKS_DIR"
cat > "$HOOKS_DIR/session-start-memory-os.json" <<EOF
{
  "event": "sessionStart",
  "type": "command",
  "command": "$MCP_BIN",
  "args": ["--probe"],
  "description": "PAARTH memory-os health check on session start (experimental)."
}
EOF
mo_ok "Wrote hook placeholder: $HOOKS_DIR/session-start-memory-os.json"

echo ""
mo_warn "EXPERIMENTAL: Copilot lacks native MCP support. The SDK shim is a stub —"
mo_warn "wire it into your Copilot extension to enable the memory tools."
mo_ok "Copilot memory-os adapter installed."
echo ""
