"""Vector store abstraction with a zero-dep in-memory backend and a Qdrant one.

The ``VectorStore`` protocol is intentionally tiny: ``upsert`` and ``search``.
``InMemoryStore`` implements exact cosine similarity in pure Python (no numpy)
so tests and the no-Docker fallback work everywhere. ``QdrantStore`` lazily
imports ``qdrant-client`` only when instantiated, keeping the default install
dependency-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

Vector = list[float]


@dataclass(frozen=True)
class Hit:
    id: str
    score: float  # cosine similarity in [-1, 1]; higher is better
    namespace: str


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, *, id: str, vector: Vector, namespace: str) -> None: ...

    def search(self, *, vector: Vector, limit: int, namespace: str | None = None) -> list[Hit]: ...

    def delete(self, *, id: str) -> None: ...


def cosine(a: Vector, b: Vector) -> float:
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} != {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


@dataclass
class InMemoryStore:
    """Exact-cosine store. Holds vectors in a dict; fine for thousands of rows."""

    _vecs: dict[str, tuple[Vector, str]] = field(default_factory=dict)

    def upsert(self, *, id: str, vector: Vector, namespace: str) -> None:
        self._vecs[id] = (list(vector), namespace)

    def delete(self, *, id: str) -> None:
        self._vecs.pop(id, None)

    def search(self, *, vector: Vector, limit: int, namespace: str | None = None) -> list[Hit]:
        scored = [
            Hit(id=eid, score=cosine(vector, vec), namespace=ns)
            for eid, (vec, ns) in self._vecs.items()
            if namespace is None or ns == namespace
        ]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:limit]

    def __len__(self) -> int:  # convenience for tests
        return len(self._vecs)


class QdrantStore:
    """Qdrant-backed store. Imports qdrant-client lazily on construction.

    Install the optional dependency group to use it: ``pip install -e '.[vector]'``.
    Vectors are upserted with a ``namespace`` payload so search can filter
    per project. Cosine distance is configured on the collection.
    """

    def __init__(self, *, url: str = "http://127.0.0.1:6333", collection: str = "memory_os", dim: int = 768) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise RuntimeError(
                "qdrant-client not installed. Run: pip install -e '.[vector]'"
            ) from exc

        self._client = QdrantClient(url=url)
        self._collection = collection
        self._dim = dim
        existing = {c.name for c in self._client.get_collections().collections}
        if collection not in existing:
            self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(self, *, id: str, vector: Vector, namespace: str) -> None:  # pragma: no cover - needs live Qdrant
        from qdrant_client.models import PointStruct

        self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=_uuid_point(id), vector=vector, payload={"entry_id": id, "namespace": namespace})],
        )

    def delete(self, *, id: str) -> None:  # pragma: no cover - needs live Qdrant
        from qdrant_client.models import FilterSelector, Filter, FieldCondition, MatchValue

        self._client.delete(
            collection_name=self._collection,
            points_selector=FilterSelector(
                filter=Filter(must=[FieldCondition(key="entry_id", match=MatchValue(value=id))])
            ),
        )

    def search(self, *, vector: Vector, limit: int, namespace: str | None = None) -> list[Hit]:  # pragma: no cover - needs live Qdrant
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        flt = None
        if namespace is not None:
            flt = Filter(must=[FieldCondition(key="namespace", match=MatchValue(value=namespace))])
        res = self._client.search(
            collection_name=self._collection, query_vector=vector, limit=limit, query_filter=flt
        )
        return [
            Hit(id=p.payload["entry_id"], score=float(p.score), namespace=p.payload.get("namespace", ""))
            for p in res
        ]


def _uuid_point(entry_id: str) -> str:  # pragma: no cover - trivial
    """Qdrant point ids must be int or UUID; derive a stable UUID from entry_id."""
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_URL, entry_id))
