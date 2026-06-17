"""MCP stdio server exposing the 5 memory tools.

Uses the FastMCP high-level API from the official `mcp` Python SDK.
Run via ``superagent-memory-mcp`` (entry-point) or
``python -m memory_os.server``.

Environment variables:
    SUPERAGENT_MEMORY_HOME       Storage dir (default ~/.superagent/memory-os)
    SUPERAGENT_MEMORY_NAMESPACE  Override the auto-detected git-root namespace
"""

from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import db, namespace, tools

mcp = FastMCP("superagent-memory")

# Single shared connection — SQLite WAL mode handles multi-reader/single-writer
# concurrency, and an MCP server is single-process by design.
_conn = db.connect()


def _resolve_namespace(explicit: str | None) -> str:
    return explicit or namespace.namespace_for()


@mcp.tool()
def memory_recall(query: str, limit: int = 10, namespace: str | None = None) -> dict:
    """Search memory for entries matching ``query``.

    Returns BM25-ranked hits within the current project namespace (auto-
    detected from git root) unless ``namespace`` is explicitly provided.
    Pass ``namespace='__global__'`` for cross-project facts.
    """
    return tools.memory_recall(_conn, query=query, limit=limit, namespace=_resolve_namespace(namespace))


@mcp.tool()
def memory_write(
    content: str,
    kind: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> dict:
    """Store ``content`` in memory under ``kind`` (fact/decision/feedback/snippet/session).

    Content is sanitized first. High-density prompt-injection payloads are
    rejected (returns ``{ok: false, rejected: true}``).
    """
    return tools.memory_write(
        _conn,
        content=content,
        kind=kind,
        namespace=_resolve_namespace(namespace),
        tags=tags or (),
    )


@mcp.tool()
def memory_list(
    namespace: str | None = None,
    kind: str | None = None,
    since: float | None = None,
    limit: int = 50,
) -> dict:
    """List recent entries (no scoring, ordered by ts DESC)."""
    return tools.memory_list(
        _conn,
        namespace=_resolve_namespace(namespace),
        kind=kind,
        since=since,
        limit=limit,
    )


@mcp.tool()
def memory_pin(entry_id: str) -> dict:
    """Promote an entry to the L1 workspace (writes a markdown pin file).

    Pinned entries surface in the workspace memory and persist across sessions.
    """
    return tools.memory_pin(_conn, entry_id=entry_id)


@mcp.tool()
def memory_forget(id_or_pattern: str, namespace: str | None = None) -> dict:
    """Soft-delete by id or by SQL LIKE pattern over content.

    Forgotten rows are kept in the DB (with ``forgotten=1``) for audit; they
    will not be returned by recall or list. Use a SQL LIKE wildcard (% or _)
    in ``id_or_pattern`` to forget by content fragment.
    """
    return tools.memory_forget(
        _conn,
        id_or_pattern=id_or_pattern,
        namespace=_resolve_namespace(namespace),
    )


@mcp.tool()
def memory_retrieve(token: str, query: str | None = None) -> dict:
    """Retrieve the original content for a CCR sentinel token or bare hash.

    ``token`` is either a full sentinel (``ccr:<hash>:<n>``) emitted by
    compress-cache-retrieve, or a bare 12-char hex hash.  ``query`` is an
    optional whitespace-separated list of terms; when provided only lines
    containing ALL terms (case-insensitive) are returned.

    Returns ``{ok: true, hash, kind, content, truncated_by_query}`` on success
    or ``{ok: false, reason: "not-found-or-expired", token}`` otherwise.
    """
    return tools.memory_retrieve(_conn, token=token, query=query)


@mcp.tool()
def graph_ingest(path: str, namespace: str | None = None) -> dict:
    """Ingest a graphify node-link JSON into the persistent knowledge graph.

    ``path`` is the filesystem path to a ``graph.json`` produced by graphify
    (NetworkX node-link format).  Nodes become entities; edges become triples.
    Ingestion is idempotent — re-ingesting the same file is safe.

    Returns ``{ok, entities, triples, skipped}``.
    """
    return tools.graph_ingest(_conn, path=path, namespace=_resolve_namespace(namespace))


@mcp.tool()
def graph_query(text: str, limit: int = 10, namespace: str | None = None) -> dict:
    """Search the knowledge graph by entity label and return matches + neighbors.

    Returns entities whose labels match ``text`` (case-insensitive substring)
    plus their immediate incident triples.  When the text-memory backend is
    available, results are fused with ``memory_recall`` hits via RRF so the
    caller gets a single unified ranked view of both tiers.

    Returns ``{entities, text_hits, fusion, count}``.
    """
    return tools.graph_query(_conn, text=text, limit=limit, namespace=_resolve_namespace(namespace))


@mcp.tool()
def graph_neighbors(entity_id: str, depth: int = 1, namespace: str | None = None) -> dict:
    """Return the incident triples for an entity up to ``depth`` hops.

    Traverses the currently-valid (non-superseded) edges in both directions.
    Returns ``{entity_id, depth, count, neighbors}``.
    """
    return tools.graph_neighbors(_conn, entity_id=entity_id, depth=depth, namespace=_resolve_namespace(namespace))


def main() -> None:
    """Console-script entry point."""
    try:
        mcp.run()
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(0)


if __name__ == "__main__":
    main()
