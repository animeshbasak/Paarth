#!/usr/bin/env bash
# Shared helpers for memory-os adapter installers.
# Source from each per-platform install-memory-os.sh:
#   . "$(dirname "${BASH_SOURCE[0]}")/../_shared/memory-os-lib.sh"

# ── Color helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
mo_ok()   { echo -e "${GREEN}✓${NC} $*"; }
mo_info() { echo -e "${CYAN}→${NC} $*"; }
mo_warn() { echo -e "${YELLOW}!${NC} $*"; }
mo_err()  { echo -e "${RED}✗${NC} $*" >&2; }

# Resolve repo root from a caller script's $BASH_SOURCE
mo_repo_root() {
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  cd "$script_dir/../.." && pwd
}

# Path to the Ground Truth template (always relative to repo root)
mo_gt_block() {
  local root
  root="$(mo_repo_root)"
  echo "$root/templates/memory-os/ground-truth-hierarchy.md"
}

# ── Idempotent block injection ──────────────────────────────────────────────
# Usage: mo_inject_gt <target-markdown-file>
# Appends the GT block iff the BEGIN marker is not already present.
mo_inject_gt() {
  local target="$1"
  local block
  block="$(mo_gt_block)"

  if [[ ! -f "$block" ]]; then
    mo_err "Ground Truth template not found at $block"
    return 1
  fi

  mkdir -p "$(dirname "$target")"
  touch "$target"

  if grep -q "BEGIN SUPERAGENT-MEMORY-OS GROUND-TRUTH" "$target"; then
    mo_ok "Ground Truth block already present in $target"
    return 0
  fi

  printf "\n" >> "$target"
  cat "$block" >> "$target"
  mo_ok "Injected Ground Truth block into $target"
}

# Usage: mo_remove_gt <target-markdown-file>
# Removes the block (between BEGIN/END markers) if present. Used by uninstall.
mo_remove_gt() {
  local target="$1"
  [[ -f "$target" ]] || return 0
  if ! grep -q "BEGIN SUPERAGENT-MEMORY-OS GROUND-TRUTH" "$target"; then
    return 0
  fi
  local tmp
  tmp="$(mktemp)"
  awk '
    /BEGIN SUPERAGENT-MEMORY-OS GROUND-TRUTH/ { skip=1; next }
    /END SUPERAGENT-MEMORY-OS GROUND-TRUTH/ { skip=0; next }
    !skip { print }
  ' "$target" > "$tmp"
  mv "$tmp" "$target"
  mo_ok "Removed Ground Truth block from $target"
}

# ── MCP server install/check ────────────────────────────────────────────────
# Ensures the superagent-memory-mcp Python entry point is installed and on PATH.
# Returns the absolute path to the binary on success, exits non-zero otherwise.
mo_ensure_mcp_installed() {
  local root
  root="$(mo_repo_root)"
  local mcp_dir="$root/bin/superagent-memory-mcp"

  if [[ ! -d "$mcp_dir" ]]; then
    mo_err "MCP server source not found at $mcp_dir"
    return 1
  fi

  # Prefer venv binary if it exists; install on first run otherwise.
  local bin="$mcp_dir/.venv/bin/superagent-memory-mcp"
  if [[ ! -x "$bin" ]]; then
    mo_info "First run — creating venv and installing MCP server (one-time setup)…"
    if ! command -v uv >/dev/null 2>&1; then
      mo_err "uv is required (https://github.com/astral-sh/uv). Install: brew install uv"
      return 1
    fi
    (
      cd "$mcp_dir"
      uv venv --python 3.12 --quiet
      uv pip install -e . --quiet
    ) || { mo_err "MCP server install failed"; return 1; }
  fi

  if [[ ! -x "$bin" ]]; then
    mo_err "MCP server binary missing after install: $bin"
    return 1
  fi

  mo_ok "MCP server ready: $bin"
  echo "$bin"
}

# ── JSON helpers (require jq) ───────────────────────────────────────────────
mo_require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    mo_err "jq is required for MCP config editing. Install: brew install jq"
    return 1
  fi
}

# Usage: mo_register_mcp_in_json <config-file> <server-name> <command-path>
# Idempotently adds the server to mcpServers in a JSON config file.
mo_register_mcp_in_json() {
  local config="$1" name="$2" cmd="$3"
  mo_require_jq || return 1

  mkdir -p "$(dirname "$config")"
  if [[ ! -f "$config" ]]; then
    echo '{}' > "$config"
  fi

  local tmp
  tmp="$(mktemp)"
  jq --arg name "$name" --arg cmd "$cmd" '
    .mcpServers //= {} |
    .mcpServers[$name] = { command: $cmd }
  ' "$config" > "$tmp" && mv "$tmp" "$config"
  mo_ok "Registered MCP server '$name' in $config"
}
