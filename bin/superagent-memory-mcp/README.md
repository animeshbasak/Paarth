# superagent-memory-mcp

MCP server providing persistent multi-tier memory for SuperAgent across Claude Code, Cursor, Antigravity, Gemini CLI, and GitHub Copilot.

Ported in spirit from [memory-os](https://github.com/cd-drews/memory-os) (MIT, Claudio Drews). See [`docs/rfcs/0001-memory-os.md`](../../docs/rfcs/0001-memory-os.md) for the architectural decisions.

## What it does

Five tools, served over MCP stdio:

| Tool | Purpose |
|---|---|
| `memory_recall(query, limit?, namespace?)` | BM25-ranked search over stored memory in the current project namespace |
| `memory_write(content, kind, tags?)` | Append-only store with prompt-injection sanitization |
| `memory_list(namespace?, kind?, since?)` | Recent entries, ordered by timestamp |
| `memory_pin(id)` | Promote an entry to the workspace L1 layer |
| `memory_forget(id_or_pattern)` | Soft-delete by id or SQL LIKE pattern |

Namespacing is automatic: entries are isolated per git-root hash. Cross-project facts go under the reserved `__global__` namespace.

## Install

Requires Python ≥ 3.11.

```bash
# from this directory
uv pip install -e .                  # or: pip install -e .
```

Then register with your MCP-aware client. For Claude Code:

```bash
bash adapters/claude-code/install.sh
```

Or manually add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "superagent-memory": {
      "command": "superagent-memory-mcp"
    }
  }
}
```

## Lifecycle jobs

A second console script, `superagent-memory`, runs maintenance jobs (used by
hooks or cron — not the MCP transport):

```bash
superagent-memory decay --dry-run          # report stale entries, no changes
superagent-memory decay                     # archive entries older than 90d AND idle 30d
superagent-memory decay --max-age-days 180 --idle-days 60 --namespace <ns>
superagent-memory cron install              # schedule weekly decay (launchd on macOS, crontab elsewhere)
superagent-memory cron status
superagent-memory cron uninstall
```

Decay is a soft-delete (`forgotten = 1`, recorded in the `audit` table) and
never touches pinned entries. Recall refreshes an entry's `last_access`, so
frequently-used memory is never archived. Semantic dedup (Phase 4.2) is
deferred until vector recall (Phase 5) lands.

## Storage

- `~/.superagent/memory-os/memory.db` — SQLite + FTS5
- `~/.superagent/memory-os/pinned/` — promoted entries (markdown)
- Override the root via `SUPERAGENT_MEMORY_HOME`.

Default install is zero-dep (FTS only). Vector recall (Qdrant sidecar) is opt-in via `SUPERAGENT_MEMORY_VECTOR=on` — see Phase 5 in the plan doc.

## Tests

```bash
uv pip install -e ".[dev]"
pytest
```

## License

MIT. Concepts inspired by [memory-os](https://github.com/cd-drews/memory-os) (Claudio Drews, MIT). Independent TypeScript-then-Python reimplementation; no upstream code copied.
