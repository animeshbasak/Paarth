"""Phase 5 vector-recall tests.

All hermetic: the in-memory store + an injected fake ``embed_fn`` mean no
Qdrant, no Ollama, and no network. The cloud/local HTTP legs are exercised
against a monkeypatched fake ``httpx`` so the provider-chain logic is covered
without the optional dependency.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from memory_os import db, tools, vector
from memory_os.vector import embed as embed_mod
from memory_os.vector.recall import reciprocal_rank_fusion
from memory_os.vector.store import InMemoryStore, cosine


@pytest.fixture
def conn():
    tmp = Path(tempfile.mkdtemp()) / "memory.db"
    c = db.connect(tmp)
    yield c
    c.close()


@pytest.fixture(autouse=True)
def fresh_store():
    """Reset the process-wide store before and after each test."""
    vector.reset_store()
    yield
    vector.reset_store()


@pytest.fixture
def vector_on(monkeypatch):
    monkeypatch.setenv("SUPERAGENT_MEMORY_VECTOR", "on")
    monkeypatch.setenv("SUPERAGENT_MEMORY_VECTOR_BACKEND", "memory")
    vector.reset_store()


# --- a deterministic toy embedder: bag-of-words over a tiny vocabulary -------
VOCAB = ["auth", "login", "bug", "fix", "database", "postgres", "cache", "redis"]
SYNONYMS = {"login": "auth", "signin": "auth", "fix": "bug"}


def fake_embed(text: str) -> list[float]:
    """Map text to a vocab-count vector, folding a few synonyms together so
    'login fix' and 'auth bug' land near each other in cosine space."""
    words = [SYNONYMS.get(w, w) for w in text.lower().replace(",", " ").split()]
    return [float(words.count(term)) for term in VOCAB]


# --- store + cosine ----------------------------------------------------------

def test_cosine_identical_is_one():
    assert cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cosine_orthogonal_is_zero():
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_dimension_mismatch_raises():
    with pytest.raises(ValueError):
        cosine([1.0], [1.0, 2.0])


def test_inmemory_store_ranks_by_similarity():
    s = InMemoryStore()
    s.upsert(id="a", vector=[1.0, 0.0], namespace="ns")
    s.upsert(id="b", vector=[0.0, 1.0], namespace="ns")
    hits = s.search(vector=[0.9, 0.1], limit=2, namespace="ns")
    assert [h.id for h in hits] == ["a", "b"]
    assert hits[0].score > hits[1].score


def test_inmemory_store_namespace_filter():
    s = InMemoryStore()
    s.upsert(id="a", vector=[1.0, 0.0], namespace="ns1")
    s.upsert(id="b", vector=[1.0, 0.0], namespace="ns2")
    hits = s.search(vector=[1.0, 0.0], limit=10, namespace="ns1")
    assert [h.id for h in hits] == ["a"]


def test_inmemory_store_delete():
    s = InMemoryStore()
    s.upsert(id="a", vector=[1.0], namespace="ns")
    s.delete(id="a")
    assert len(s) == 0
    s.delete(id="missing")  # idempotent


# --- reciprocal rank fusion --------------------------------------------------

def test_rrf_rewards_agreement():
    # 'x' is top of both lists; should win over items ranked high in only one.
    fused = reciprocal_rank_fusion(["x", "a", "b"], ["x", "c", "d"])
    assert fused[0] == "x"


def test_rrf_union_of_ids():
    fused = reciprocal_rank_fusion(["a", "b"], ["b", "c"])
    assert set(fused) == {"a", "b", "c"}


def test_rrf_deterministic_tiebreak():
    # Same single-list rank → tie on score → break by best rank then id.
    fused = reciprocal_rank_fusion(["b", "a"], [])
    assert fused == ["b", "a"]
    assert reciprocal_rank_fusion([], []) == []


# --- gate --------------------------------------------------------------------

def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SUPERAGENT_MEMORY_VECTOR", raising=False)
    assert vector.is_enabled() is False


@pytest.mark.parametrize("val", ["on", "1", "true", "YES"])
def test_enabled_truthy_values(monkeypatch, val):
    monkeypatch.setenv("SUPERAGENT_MEMORY_VECTOR", val)
    assert vector.is_enabled() is True


def test_recall_fts_mode_when_disabled(conn, monkeypatch):
    monkeypatch.delenv("SUPERAGENT_MEMORY_VECTOR", raising=False)
    tools.memory_write(conn, content="postgres is the prod database", kind="fact", namespace="ns")
    out = tools.memory_recall(conn, query="postgres", namespace="ns")
    assert out["mode"] == "fts"
    assert "indexed" not in tools.memory_write(
        conn, content="another", kind="fact", namespace="ns"
    )


# --- hybrid recall end-to-end ------------------------------------------------

def test_write_indexes_when_enabled(conn, vector_on):
    out = tools.memory_write(
        conn, content="auth bug in middleware", kind="fact", namespace="ns", embed_fn=fake_embed
    )
    assert out["indexed"] is True
    assert len(vector.get_store()) == 1


def test_hybrid_recall_finds_synonym_miss(conn, vector_on):
    """The win condition: a query that FTS cannot match but vectors can.

    Stored doc says 'auth bug'; query is 'login fix'. FTS (keyword) returns
    nothing, but the synonym-folding embedder places them adjacent, so hybrid
    recall still surfaces the entry."""
    tools.memory_write(
        conn, content="auth bug in the middleware", kind="fact", namespace="ns", embed_fn=fake_embed
    )
    tools.memory_write(
        conn, content="redis cache warming notes", kind="fact", namespace="ns", embed_fn=fake_embed
    )

    # FTS alone misses: no shared keyword between 'login fix' and 'auth bug'.
    fts_only = db.recall(conn, namespace="ns", query="login fix", limit=10)
    assert all("auth bug" not in e.content for e in fts_only)

    out = tools.memory_recall(conn, query="login fix", namespace="ns", embed_fn=fake_embed)
    assert out["mode"] == "hybrid"
    assert any("auth bug" in h["content"] for h in out["hits"])


def test_hybrid_recall_respects_namespace(conn, vector_on):
    tools.memory_write(conn, content="auth bug", kind="fact", namespace="ns1", embed_fn=fake_embed)
    tools.memory_write(conn, content="auth bug", kind="fact", namespace="ns2", embed_fn=fake_embed)
    out = tools.memory_recall(conn, query="auth bug", namespace="ns1", embed_fn=fake_embed)
    assert out["count"] == 1
    assert all(h["namespace"] == "ns1" for h in out["hits"])


def test_hybrid_falls_back_to_fts_when_embed_fails(conn, vector_on):
    """If the embedder raises, write still succeeds (indexed=False) and recall
    degrades to FTS rather than erroring."""
    def boom(_text):
        raise RuntimeError("ollama down")

    out = tools.memory_write(
        conn, content="postgres prod database", kind="fact", namespace="ns", embed_fn=boom
    )
    assert out["ok"] is True
    assert out["indexed"] is False

    recall = tools.memory_recall(conn, query="postgres", namespace="ns", embed_fn=boom)
    # Keyword hit still works; vector leg returned nothing.
    assert any("postgres" in h["content"] for h in recall["hits"])


def test_forget_removes_from_index(conn, vector_on):
    w = tools.memory_write(
        conn, content="auth bug here", kind="fact", namespace="ns", embed_fn=fake_embed
    )
    assert len(vector.get_store()) == 1
    tools.memory_forget(conn, id_or_pattern=w["id"], namespace="ns")
    assert len(vector.get_store()) == 0


# --- embedder provider chain (fake httpx) ------------------------------------

class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self._status = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self._status >= 400:
            raise RuntimeError(f"HTTP {self._status}")


class _FakeHttpx:
    """Minimal stand-in for the httpx module used by embed.py."""

    def __init__(self, handler):
        self._handler = handler

    def post(self, url, **kwargs):
        return self._handler(url, kwargs)


def test_embed_uses_ollama_first(monkeypatch):
    def handler(url, kwargs):
        assert "api/embeddings" in url
        return _FakeResponse({"embedding": [0.1, 0.2, 0.3]})

    monkeypatch.setattr(embed_mod, "_import_httpx", lambda: _FakeHttpx(handler))
    assert embed_mod.embed("hello") == [0.1, 0.2, 0.3]


def test_embed_falls_back_to_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

    def handler(url, kwargs):
        if "11434" in url or "api/embeddings" in url:
            raise RuntimeError("connection refused")
        assert "openrouter" in url or "/embeddings" in url
        return _FakeResponse({"data": [{"embedding": [9.0, 8.0]}]})

    monkeypatch.setattr(embed_mod, "_import_httpx", lambda: _FakeHttpx(handler))
    assert embed_mod.embed("hello") == [9.0, 8.0]


def test_embed_raises_when_no_provider(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def handler(url, kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(embed_mod, "_import_httpx", lambda: _FakeHttpx(handler))
    with pytest.raises(embed_mod.EmbeddingError):
        embed_mod.embed("hello")
