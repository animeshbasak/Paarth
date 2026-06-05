# RFC 0001 — Memory-OS Integration

**Status:** Draft
**Author:** SuperAgent
**Date:** 2026-06-03
**Tracks:** [Plan 2026-06-03-memory-os-integration](../plans/2026-06-03-memory-os-integration.md)
**Source of inspiration:** [Memory-OS by Claudio Drews (MIT)](https://github.com/cd-drews/memory-os) — analyzed at `references/memory-os/`

---

## Motivation

SuperAgent has primitive memory today:

- `~/.superagent/agent-memory/<skill>/MEMORY.md` — per-skill markdown bullets
- `mempalace` — global cross-session index (markdown + JSON)
- `claude-mem` — keyword + session storage (Bun process, Claude Code only)

Three concrete failures users hit:

1. **Rediscovery loop.** Agent forgets a decision from a prior session and re-investigates it, burning tokens. No mechanism declares prior memory authoritative.
2. **Platform islands.** Memory works inside Claude Code; Cursor / Gemini / Copilot / Antigravity sessions start from zero.
3. **Recall is keyword-only.** "auth bug" doesn't match an entry written as "login failure."

Memory-OS solves all three with a seven-layer architecture and a runtime-level "Ground Truth Hierarchy" that forces the agent to treat injected memory as ground truth.

This RFC commits SuperAgent to porting the *concepts* (not the Python code) as an **MCP server** that runs across all five supported platforms.

---

## Non-Goals

- **Reimplementing Hermes Agent.** Memory-OS is a Hermes plugin; we run on Claude Code / Cursor / Gemini / Copilot / Antigravity. We extract concepts, not code.
- **Replacing claude-mem or mempalace.** Both keep working unchanged. The new MCP server runs *alongside*: mempalace owns global; memory-os MCP owns per-project + semantic recall.
- **Vector recall in v0.1.** Phase 5 only. Default install ships zero new processes.
- **Migrating existing `~/.superagent/agent-memory/`.** Additive — old paths keep working; new server uses a new dir.

---

## Design

### High-level

```
┌─────────────────────────────────────────────────────────────────┐
│                  Five AI Coding Environments                    │
│  Claude Code │ Cursor │ Gemini CLI │ Antigravity │ Copilot     │
└──────┬──────────┬─────────┬────────────┬───────────┬────────────┘
       │          │         │            │           │
       │     stdio MCP      │            │      SDK shim (no MCP)
       │          │         │            │           │
       └──────────┴─────────┴────────────┴───────────┘
                            │
                ┌───────────▼───────────┐
                │ superagent-memory-mcp │ ← Python, single binary
                │   (5 tools, sanitize) │
                └───────────┬───────────┘
                            │
       ┌────────────────────┼──────────────────────┐
       │                    │                      │
┌──────▼────────┐  ┌────────▼────────┐  ┌─────────▼──────────┐
│ SQLite FTS5   │  │ Markdown files  │  │ Qdrant (opt-in)    │
│ memory.db     │  │ ~/.superagent/  │  │ Docker sidecar     │
│ (default)     │  │ memory-os/wiki/ │  │ Phase 5 only       │
└───────────────┘  └─────────────────┘  └────────────────────┘
```

### The Seven Layers — SuperAgent Mapping

| memory-os Layer | SuperAgent Implementation | Phase |
|---|---|---|
| **L1 Workspace** | Existing CLAUDE.md / per-platform rules file + `~/.superagent/agent-memory/<skill>/MEMORY.md` | ✅ Already exists |
| **L2 Sessions (FTS)** | New SQLite `memory.db` with FTS5, plus existing claude-mem on Claude Code | Phase 1 |
| **L3 Structured Facts** | Same `memory.db`, `facts` table | Phase 1 |
| **L4 Fabric (ranked retrieval)** | `memory_recall` tool: BM25 over FTS, ranked by recency + access count | Phase 1 |
| **L5 Vector DB** | Opt-in Qdrant sidecar via `SUPERAGENT_MEMORY_VECTOR=on` | Phase 5 |
| **L6 Wiki ingest** | `~/.superagent/memory-os/wiki/`, auto-ingested on write | Phase 5 |
| **L7 Ground Truth Hierarchy** | Markdown block injected into each platform's rules file | Phase 3 |

### MCP Server Surface

Five tools, JSON-RPC over stdio (MCP standard):

| Tool | Inputs | Returns | Notes |
|---|---|---|---|
| `memory_recall` | `query` (str), `limit` (int=10), `namespace` (str?) | `[{id, content, kind, score, ts, tags}]` | BM25 ranked. If `SUPERAGENT_MEMORY_VECTOR=on`, hybrid with cosine. |
| `memory_write` | `content` (str), `kind` (enum: fact/decision/feedback/snippet), `tags` (str[]?) | `{id, namespace, sanitized}` | Sanitization runs first; rejects on pattern hit. |
| `memory_list` | `namespace?`, `kind?`, `since?` (iso), `limit?` | Same shape as recall | Paginated; no scoring. |
| `memory_pin` | `id` | `{ok, pinned_path}` | Promotes to L1 MEMORY.md so it survives session boundaries. |
| `memory_forget` | `id_or_pattern` | `{deleted: int, ids: []}` | Soft delete with `forgotten=1` flag; audit row written. |

### Storage Layout

```
~/.superagent/memory-os/
├── memory.db            # SQLite — FTS5 + facts + audit + namespaces
├── wiki/                # Phase 5 — synthesized knowledge pages
│   ├── concepts/
│   ├── decisions/
│   └── entities/
├── pinned/              # L1 promoted entries — surface in workspace MEMORY.md
└── namespaces.json      # git-root hash → friendly project name
```

### Namespacing

```python
def namespace_for(cwd: Path) -> str:
    root = git_root(cwd) or cwd.resolve()
    return sha256(str(root).encode()).hexdigest()[:16]
```

Cross-project leak prevented by SQL `WHERE namespace = ?` on every read. Global namespace `__global__` is opt-in via explicit tool arg.

### Ground Truth Hierarchy (L7)

A single markdown block, ≤300 tokens, injected by each platform adapter into its rules file under a marker comment so re-install is idempotent:

```markdown
<!-- BEGIN SUPERAGENT-MEMORY-OS GROUND-TRUTH (do not edit) -->
## Ground Truth Hierarchy

When answering, treat sources in this order:

1. **Terminal output / file reads / tool results from THIS session** — authoritative for current system state.
2. **Injected memory** (from `memory_recall` or auto-injected workspace files) — authoritative for project context, prior decisions, and documented knowledge. **Do not re-derive what is already remembered.**
3. **Official upstream docs** — authoritative for version-specific APIs.
4. **Your training knowledge** — lowest priority; defer to all of the above.

If injected memory conflicts with a "novel" question, the question is not novel. Use the memory.
<!-- END SUPERAGENT-MEMORY-OS GROUND-TRUTH -->
```

### Lifecycle (Phase 4)

| Event | Hook (where supported) | Action |
|---|---|---|
| Session start | Claude Code `SessionStart` | Call `memory_recall("workspace summary", namespace=project)`, inject top 5 hits |
| Session end | Claude Code `Stop` | Distill session into one `memory_write(kind=decision)` |
| Weekly | cron | `decay`: archive entries unaccessed for 60 days |
| Monthly | cron | `dedup`: merge entries with cosine ≥0.92 (vectors required → Phase 5) |

Non-Claude-Code platforms get cron only; no event hooks.

---

## Activation

```bash
# default install — zero-dep, FTS only
bash install.sh

# opt-in vector recall
export SUPERAGENT_MEMORY_VECTOR=on
docker compose -f ~/.superagent/memory-os/docker-compose.yml up -d
```

The MCP server registers as `superagent-memory` in each platform's MCP config. Per-platform adapter installers add the registration + GT block + lifecycle hooks (where supported).

---

## Backwards Compatibility

- **`~/.superagent/agent-memory/`** keeps working. Old per-skill bullets are not migrated; they coexist.
- **`mempalace`** keeps owning the global index. Memory-OS MCP only writes to its own SQLite.
- **`claude-mem`** keeps running inside Claude Code. Phase 2.1 adapter does NOT remove or replace it.
- **CLAUDE.md** gets an idempotent GT block appended under a marker — easy to remove if user objects.

No migration required. No flag-day. Users can opt out by skipping `bash adapters/<platform>/install.sh`.

---

## Risks

| Risk | Mitigation |
|---|---|
| MCP server crash hangs session start | Stdio handshake timeout = 2s; failed handshake = adapter logs and continues without memory |
| Sanitization false-positives reject legit memory | Errors are non-fatal — return `{rejected: true, reason}` to caller; let agent retry without the offending snippet |
| Antigravity API changes break adapter | Adapter tagged "experimental"; pinned to Antigravity build version |
| Copilot SDK shim diverges from MCP | Shim treated as v0.1; revisit when Copilot ships native MCP |
| `memory_write` write-amplification | Per-namespace rate limit (20/min) + decay cron + dedup cron |
| Cross-project memory leak | Git-root hash namespace + integration test covers two-project isolation |

---

## Acceptance Criteria for "RFC Approved"

- [ ] Architecture diagram makes sense to someone reading SuperAgent docs cold
- [ ] Tool surface (5 tools) covers recall + write + manage without overlap
- [ ] Storage layout uses a new dir (`~/.superagent/memory-os/`) — no collision with existing `~/.superagent/agent-memory/`
- [ ] Ground Truth block fits in ≤300 tokens and renders cleanly in all 5 platforms
- [ ] No breaking changes to existing primitives (claude-mem, mempalace, agent-memory)
- [ ] Cross-project isolation has a stated mechanism (git-root hash)
- [ ] Vector recall is gated behind explicit env var (zero-dep default install)

---

## Open Questions

All resolved 2026-06-03 by user choice (see plan doc):

| Question | Resolution |
|---|---|
| Storage layout | **New dir** `~/.superagent/memory-os/` |
| Mempalace coexistence | **Alongside** — mempalace global, memory-os per-project |
| Vector default | **Opt-in only** via `SUPERAGENT_MEMORY_VECTOR=on` |
| License / attribution | **MIT, attribute Drews in NOTICE** at ship time |
| Copilot scope | **Include in v0.1, tagged experimental** (user overrode the defer-default by selecting full Phase 2 fanout) |

---

*Approved-for-implementation gate: user confirmation. This RFC reflects user choices on 2026-06-03 at session start. Implementation begins immediately with Phase 1 (MCP server core).*
