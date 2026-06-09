"""Vector-recall orchestration (Phase 5).

Owns the opt-in gate, the process-wide store singleton, and the two side
effects the rest of the server cares about: ``index_entry`` (write path) and
``vector_search`` (recall path). Everything here is a no-op unless
``SUPERAGENT_MEMORY_VECTOR`` is on, so the default install pays nothing.

Store selection (``SUPERAGENT_MEMORY_VECTOR_BACKEND``):
  * ``auto`` (default) — try Qdrant, fall back to the in-memory store
  * ``qdrant``         — require Qdrant (raise if unavailable)
  * ``memory``         — always use the in-memory store
"""

from __future__ import annotations

import os
from typing import Callable

from . import embed as _embed
from .store import Hit, InMemoryStore, QdrantStore, VectorStore

Vector = list[float]
EmbedFn = Callable[[str], Vector]

_FLAG = "SUPERAGENT_MEMORY_VECTOR"
_TRUTHY = {"1", "on", "true", "yes"}

_store: VectorStore | None = None


def is_enabled() -> bool:
    return os.environ.get(_FLAG, "").strip().lower() in _TRUTHY


def get_store() -> VectorStore:
    """Lazily build and cache the store for this process."""
    global _store
    if _store is None:
        _store = _build_store()
    return _store


def reset_store() -> None:
    """Drop the cached store. Tests use this to swap backends between cases."""
    global _store
    _store = None


def _build_store() -> VectorStore:
    backend = os.environ.get("SUPERAGENT_MEMORY_VECTOR_BACKEND", "auto").strip().lower()
    if backend == "memory":
        return InMemoryStore()
    if backend in ("qdrant", "auto"):
        try:
            url = os.environ.get("SUPERAGENT_MEMORY_QDRANT_URL", "http://127.0.0.1:6333")
            return QdrantStore(url=url)
        except Exception:
            if backend == "qdrant":
                raise
            # auto: Qdrant unreachable / extra not installed → degrade gracefully.
            return InMemoryStore()
    raise ValueError(f"unknown vector backend {backend!r}")


def index_entry(
    *,
    entry_id: str,
    content: str,
    namespace: str,
    embed_fn: EmbedFn | None = None,
) -> bool:
    """Best-effort: embed ``content`` and upsert it. Never raises.

    Returns True on success. A failed embed (Ollama down, no cloud key) must
    not break a memory write, so failures are swallowed and reported via the
    return value for the caller to audit.
    """
    fn = embed_fn or _embed.embed
    try:
        vector = fn(content)
        get_store().upsert(id=entry_id, vector=vector, namespace=namespace)
        return True
    except Exception:
        return False


def vector_search(
    *,
    query: str,
    namespace: str,
    limit: int,
    embed_fn: EmbedFn | None = None,
) -> list[Hit]:
    """Embed the query and return the top ``limit`` cosine hits. Never raises."""
    fn = embed_fn or _embed.embed
    try:
        vector = fn(query)
        return get_store().search(vector=vector, limit=limit, namespace=namespace)
    except Exception:
        return []


def delete_entry(*, entry_id: str) -> None:
    """Best-effort removal from the vector index (called on forget)."""
    try:
        get_store().delete(id=entry_id)
    except Exception:
        pass
