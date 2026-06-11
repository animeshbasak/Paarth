# Memory-OS Quickstart — per platform

One memory, every tool. The same SQLite store (`~/.superagent/memory-os/memory.db`)
serves Claude Code, Cursor, and Gemini CLI; what you teach one tool, the others know.

## 0. Install the server (once)

```bash
cd bin/superagent-memory-mcp
uv pip install -e .            # zero-dep default (FTS recall only)
# optional semantic recall:
uv pip install -e ".[vector]"
```

Verify: `superagent-memory stats` prints a JSON report.

## 1. Claude Code

```bash
./adapters/claude-code/install-memory-os.sh
```

Registers the MCP server in `~/.claude.json` and injects the Ground Truth
block into `~/.claude/CLAUDE.md`. Restart the session; the 5 `memory_*` tools
appear automatically. Memory is namespaced per git root — no setup per project.

## 2. Cursor

```bash
./adapters/cursor/install-memory-os.sh
```

Adds the server to `~/.cursor/mcp.json` and a `.mdc` rule teaching Cursor when
to recall/write. Reload Cursor to pick up the MCP config.

## 3. Gemini CLI

```bash
./adapters/gemini/install-memory-os.sh
```

Registers in `~/.gemini/settings.json`; Ground Truth lands in `GEMINI.md`.

## 4. Copilot / Antigravity (experimental)

```bash
./adapters/copilot/install-memory-os.sh      # SDK shim — no native MCP yet
./adapters/antigravity/install-memory-os.sh  # pinned to current build; API may churn
```

Treat both as v0.1: functional, but expect breakage as the platforms evolve.

## Optional: semantic recall

```bash
docker compose -f bin/superagent-memory-mcp/docker/docker-compose.yml up -d  # Qdrant sidecar
ollama pull nomic-embed-text                                                 # local embedder
export SUPERAGENT_MEMORY_VECTOR=on
```

No Docker? It degrades to an in-process store. No Ollama? Writes still
succeed (FTS-only until embeddings return). Measure the difference any time:

```bash
superagent-memory bench          # deterministic, offline
superagent-memory bench --real   # against your live Ollama
```

## Maintenance (set and forget)

```bash
superagent-memory cron install   # weekly decay via launchd/crontab
superagent-memory dedup --dry-run
superagent-memory stats          # local-only usage counters
```

## Env reference

| Var | Default | Purpose |
|---|---|---|
| `SUPERAGENT_MEMORY_HOME` | `~/.superagent/memory-os` | storage root |
| `SUPERAGENT_MEMORY_NAMESPACE` | git-root hash | namespace override |
| `SUPERAGENT_MEMORY_VECTOR` | off | hybrid semantic recall |
| `SUPERAGENT_MEMORY_VECTOR_BACKEND` | `auto` | `qdrant` / `memory` / `auto` |
| `SUPERAGENT_MEMORY_QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant endpoint |
| `SUPERAGENT_MEMORY_OLLAMA_URL` | `http://127.0.0.1:11434` | local embedder |
| `OPENROUTER_API_KEY` | unset | cloud embed fallback (explicit opt-in) |
| `SUPERAGENT_MEMORY_TELEMETRY` | on (local-only) | `off` disables counters |
