# Memory-OS Quickstart — per platform

One memory, every tool. The same SQLite store (`~/.paarth/memory-os/memory.db`)
serves Claude Code, Cursor, and Gemini CLI; what you teach one tool, the others know.

## 0. Install the server (once)

```bash
cd bin/paarth-memory-mcp
uv pip install -e .            # zero-dep default (FTS recall only)
# optional semantic recall:
uv pip install -e ".[vector]"
```

Verify: `paarth-memory stats` prints a JSON report.

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
docker compose -f bin/paarth-memory-mcp/docker/docker-compose.yml up -d  # Qdrant sidecar
ollama pull nomic-embed-text                                                 # local embedder
export PAARTH_MEMORY_VECTOR=on
```

No Docker? It degrades to an in-process store. No Ollama? Writes still
succeed (FTS-only until embeddings return). Measure the difference any time:

```bash
paarth-memory bench          # deterministic, offline
paarth-memory bench --real   # against your live Ollama
```

## Maintenance (set and forget)

```bash
paarth-memory cron install   # weekly decay via launchd/crontab
paarth-memory dedup --dry-run
paarth-memory stats          # local-only usage counters
```

## Env reference

| Var | Default | Purpose |
|---|---|---|
| `PAARTH_MEMORY_HOME` | `~/.paarth/memory-os` | storage root |
| `PAARTH_MEMORY_NAMESPACE` | git-root hash | namespace override |
| `PAARTH_MEMORY_VECTOR` | off | hybrid semantic recall |
| `PAARTH_MEMORY_VECTOR_BACKEND` | `auto` | `qdrant` / `memory` / `auto` |
| `PAARTH_MEMORY_QDRANT_URL` | `http://127.0.0.1:6333` | Qdrant endpoint |
| `PAARTH_MEMORY_OLLAMA_URL` | `http://127.0.0.1:11434` | local embedder |
| `OPENROUTER_API_KEY` | unset | cloud embed fallback (explicit opt-in) |
| `PAARTH_MEMORY_TELEMETRY` | on (local-only) | `off` disables counters |
