"""The 5 memory tools exposed via MCP.

Each function returns plain dicts (JSON-serializable) and accepts a single
connection argument so the same code paths can be unit-tested against an
in-memory SQLite DB without spinning up an MCP transport.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Iterable

from . import db
from .sanitize import sanitize

PIN_DIR_DEFAULT = db.DEFAULT_DB_DIR / "pinned"


def memory_recall(
    conn: sqlite3.Connection,
    *,
    query: str,
    limit: int = 10,
    namespace: str,
) -> dict:
    """Return BM25-ranked memory hits in the given namespace.

    The score is the negated FTS5 BM25 rank so callers can sort
    descending if they want.
    """
    entries = db.recall(conn, namespace=namespace, query=query, limit=limit)
    return {
        "namespace": namespace,
        "query": query,
        "count": len(entries),
        "hits": [e.to_dict() for e in entries],
    }


def memory_write(
    conn: sqlite3.Connection,
    *,
    content: str,
    kind: str,
    namespace: str,
    tags: Iterable[str] = (),
) -> dict:
    """Sanitize then store. Refuse storage on high-density attacks."""
    result = sanitize(content)
    if result.rejected:
        return {
            "ok": False,
            "rejected": True,
            "reason": "high-density-attack",
            "hits": list(result.hits),
        }

    entry = db.write_entry(
        conn,
        namespace=namespace,
        kind=kind,
        content=result.text,
        tags=tags,
    )
    return {
        "ok": True,
        "id": entry.id,
        "namespace": entry.namespace,
        "sanitized": not result.clean,
        "sanitize_hits": list(result.hits),
    }


def memory_list(
    conn: sqlite3.Connection,
    *,
    namespace: str,
    kind: str | None = None,
    since: float | None = None,
    limit: int = 50,
) -> dict:
    entries = db.list_entries(conn, namespace=namespace, kind=kind, since=since, limit=limit)
    return {
        "namespace": namespace,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }


def memory_pin(
    conn: sqlite3.Connection,
    *,
    entry_id: str,
    pin_dir: Path = PIN_DIR_DEFAULT,
) -> dict:
    try:
        path = db.pin_entry(conn, entry_id, pin_dir)
    except KeyError:
        return {"ok": False, "reason": "not-found", "id": entry_id}
    return {"ok": True, "id": entry_id, "pinned_path": str(path)}


def memory_forget(
    conn: sqlite3.Connection,
    *,
    id_or_pattern: str,
    namespace: str,
) -> dict:
    deleted = db.forget_entries(conn, namespace=namespace, id_or_pattern=id_or_pattern)
    return {
        "ok": True,
        "deleted": len(deleted),
        "ids": deleted,
        "namespace": namespace,
    }


# Helpers for the MCP server layer ---------------------------------------------


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
