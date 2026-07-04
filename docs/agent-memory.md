# PAARTH — Per-Skill Agent Memory

Convention for per-skill persistent memory. Lets each skill accumulate its own
domain learnings without polluting the global `mempalace` index.

## Layout

```
~/.paarth/agent-memory/
├── <skill-name>/
│   ├── MEMORY.md         ← human-readable index (one bullet per fact)
│   ├── learnings.jsonl   ← append-only structured log
│   └── refs/             ← optional: pinned snippets, command outputs
```

## Lifecycle

1. **Read on demand.** When a skill activates, the brain may load
   `~/.paarth/agent-memory/<skill>/MEMORY.md` (≤4 KB) into context as a
   system reminder. No automatic preload to keep token cost low.

2. **Write on success.** When a skill completes a non-trivial task, it appends
   one structured line to `learnings.jsonl`:

   ```json
   {"ts": "2026-05-04T12:00Z", "task_hash": "abc123", "kind": "feedback|fact|pattern", "content": "..."}
   ```

3. **Distill periodically.** A weekly job (or `Stop` hook on milestone) reduces
   the JSONL into `MEMORY.md` bullets. Keep it short — if you can't fit the
   skill's hard-won knowledge into 50 bullets, you're hoarding.

## What belongs here vs. mempalace

| Memory type | Per-skill (`agent-memory/`) | Global (`mempalace`) |
|---|---|---|
| Project facts (deadlines, who-does-what) | ❌ | ✅ |
| User preferences | ❌ | ✅ |
| Skill-specific gotchas (e.g. framer-motion + RSC pitfalls) | ✅ | ❌ |
| Tool versions tested with | ✅ | ❌ |
| Cross-session decisions | ❌ | ✅ |

If a fact would help any future skill in any project, it belongs in
`mempalace`. If it only helps one skill, it belongs here.

## Reading from a skill

```python
import json, os
from pathlib import Path

mem_dir = Path.home() / ".paarth" / "agent-memory" / "<skill-name>"
memory = (mem_dir / "MEMORY.md").read_text() if (mem_dir / "MEMORY.md").exists() else ""
```

## Writing from a skill

```bash
mkdir -p ~/.paarth/agent-memory/<skill-name>
printf '%s\n' "{\"ts\":\"$(date -u +%FT%TZ)\",\"kind\":\"pattern\",\"content\":\"...\"}" \
  >> ~/.paarth/agent-memory/<skill-name>/learnings.jsonl
```

## Initialization

`hooks/paarth-state-init.sh` creates the root directory. Skills that opt in
ship a `MEMORY.md.template` alongside `SKILL.md`; the installer copies it to
`~/.paarth/agent-memory/<skill>/MEMORY.md` if missing.

---

## Memory-OS — the cross-platform memory MCP (v3.1)

Per-skill memory (above) and `mempalace` cover *skill gotchas* and the *global
index*. **Memory-OS** is the third tier: per-project persistent memory served
over MCP, shared by every tool you code in (Claude Code, Cursor, Gemini CLI;
Copilot + Antigravity experimental).

- **Server:** `bin/paarth-memory-mcp` — Python, SQLite + FTS5, 5 tools
  (`memory_recall` / `write` / `list` / `pin` / `forget`).
- **Isolation:** namespace = git-root hash. Recall, decay, and dedup never
  cross projects.
- **Lifecycle:** weekly decay (90d old + 30d idle, pinned exempt), semantic
  dedup (cosine ≥0.92), local-only `stats` counters.
- **Hybrid recall (opt-in):** `PAARTH_MEMORY_VECTOR=on` blends FTS/BM25
  with embedding cosine via reciprocal rank fusion. Local-first embeddings
  (Ollama `nomic-embed-text`; OpenRouter only as an explicit fallback).
- **Hardened:** write sanitization (12 injection-pattern classes), namespace
  lockdown (no path traversal), mass-forget guard, soft-deletes + audit trail.

### The measured win

`paarth-memory bench` replays a fixture corpus where every fact gets a
keyword probe and a paraphrase probe (top-5 cutoff, deterministic embedder):

| Split | FTS-only | Hybrid | Delta |
|---|---|---|---|
| keyword | 100% | 100% | 0 (no regression) |
| **semantic (paraphrase)** | **0%** | **100%** | **+100 pts** |

Paraphrased queries — "login failure signs users out" looking for a stored
"auth bug in the session middleware" — are exactly how you ask about your own
past work three weeks later. FTS alone returns nothing; hybrid finds it.
(Ship gate was ≥30 points. Run `paarth-memory bench --real` to measure
with live Ollama embeddings instead of the simulated embedder.)

### Which tier do I want?

| Question you're asking | Tier |
|---|---|
| "What did *this project* decide three weeks ago?" | **Memory-OS** |
| "What gotchas does the framer-motion skill know?" | per-skill `agent-memory/` |
| "Who am I, what are my global preferences?" | `mempalace` |

See `docs/memory-os-quickstart.md` for per-platform setup.
