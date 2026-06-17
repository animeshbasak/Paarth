"""Wave 3 — persistent knowledge graph tests.

Covers: schema, GraphStore CRUD, ingest job, MCP tool wrappers.
Uses a temp-file SQLite DB (FTS5 requires a real file).
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from memory_os import db, tools
from memory_os.graph import GraphStore, _normalize_label
from memory_os.jobs import graph_ingest as ingest_job


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def conn():
    tmp = Path(tempfile.mkdtemp()) / "memory.db"
    c = db.connect(tmp)
    yield c
    c.close()


@pytest.fixture
def store(conn):
    return GraphStore(conn, "test_ns")


@pytest.fixture
def graph_json(tmp_path):
    """Write a small synthetic graphify node-link JSON to a temp file."""
    data = {
        "nodes": [
            {"id": "n1", "label": "AuthModule", "file_type": "code", "source_file": "auth.py", "community": 0},
            {"id": "n2", "label": "UserModel", "file_type": "code", "source_file": "models.py", "community": 0},
            {"id": "n3", "label": "LoginView", "file_type": "code", "source_file": "views.py", "community": 1},
            {"id": "n4", "label": "README", "file_type": "doc"},
        ],
        "links": [
            {"source": "n1", "target": "n2", "relation": "imports", "confidence": "EXTRACTED"},
            {"source": "n3", "target": "n1", "relation": "calls", "confidence": "INFERRED"},
            {"source": "n4", "target": "n3", "relation": "references", "confidence": "AMBIGUOUS", "confidence_score": 0.15},
        ],
    }
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture
def graph_json_edges_alias(tmp_path):
    """Same graph but using 'edges' instead of 'links'."""
    data = {
        "nodes": [
            {"id": "a", "label": "Alpha"},
            {"id": "b", "label": "Beta"},
        ],
        "edges": [
            {"source": "a", "target": "b", "relation": "connects"},
        ],
    }
    p = tmp_path / "graph_edges.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Schema: entities + triples tables exist
# ---------------------------------------------------------------------------

def test_entities_table_exists(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'").fetchall()
    assert rows, "entities table not created"


def test_triples_table_exists(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='triples'").fetchall()
    assert rows, "triples table not created"


# ---------------------------------------------------------------------------
# upsert_entity
# ---------------------------------------------------------------------------

def test_upsert_entity_creates(store):
    eid = store.upsert_entity("e1", "Foo", kind="module", source_file="foo.py", community=0)
    assert eid == "e1"
    row = store.get_entity("e1")
    assert row is not None
    assert row["label"] == "Foo"
    assert row["kind"] == "module"
    assert row["community"] == 0


def test_upsert_entity_idempotent(store):
    now = int(time.time())
    store.upsert_entity("e1", "Foo", now=now)
    later = now + 100
    store.upsert_entity("e1", "Foo Updated", now=later)
    rows = store.conn.execute(
        "SELECT COUNT(*) AS n FROM entities WHERE namespace='test_ns' AND id='e1'"
    ).fetchone()
    assert rows["n"] == 1


def test_upsert_entity_refreshes_last_seen(store):
    t0 = int(time.time()) - 200
    store.upsert_entity("e1", "Foo", now=t0)
    t1 = t0 + 200
    store.upsert_entity("e1", "Foo", now=t1)
    row = store.get_entity("e1")
    assert row["last_seen"] == t1
    assert row["first_seen"] == t0


# ---------------------------------------------------------------------------
# add_triple / idempotency
# ---------------------------------------------------------------------------

def test_add_triple_creates(store):
    store.upsert_entity("a", "A")
    store.upsert_entity("b", "B")
    store.add_triple("a", "calls", "b")
    rows = store.conn.execute(
        "SELECT COUNT(*) AS n FROM triples WHERE namespace='test_ns' AND subj_id='a' AND obj_id='b'"
    ).fetchone()
    assert rows["n"] == 1


def test_add_triple_idempotent(store):
    store.upsert_entity("a", "A")
    store.upsert_entity("b", "B")
    store.add_triple("a", "calls", "b")
    store.add_triple("a", "calls", "b")  # second call — no-op
    rows = store.conn.execute(
        "SELECT COUNT(*) AS n FROM triples WHERE namespace='test_ns' AND subj_id='a' AND obj_id='b'"
    ).fetchone()
    assert rows["n"] == 1


# ---------------------------------------------------------------------------
# supersede_triple + neighbors(valid_only)
# ---------------------------------------------------------------------------

def test_supersede_excludes_from_valid_neighbors(store):
    store.upsert_entity("a", "A")
    store.upsert_entity("b", "B")
    store.add_triple("a", "calls", "b")
    store.supersede_triple("a", "calls", "b")

    valid = store.neighbors("a", depth=1, valid_only=True)
    assert valid == [], "superseded triple should not appear in valid neighbors"

    all_nbrs = store.neighbors("a", depth=1, valid_only=False)
    assert len(all_nbrs) == 1, "superseded triple should appear when valid_only=False"
    assert all_nbrs[0]["valid_to"] is not None


# ---------------------------------------------------------------------------
# Ingest job — basic counts
# ---------------------------------------------------------------------------

def test_ingest_creates_correct_counts(conn, graph_json):
    result = ingest_job.ingest(conn, "test_ns", graph_json)
    assert result["entities"] == 4
    assert result["triples"] == 3
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# Ingest — edges alias
# ---------------------------------------------------------------------------

def test_ingest_edges_alias(conn, graph_json_edges_alias):
    result = ingest_job.ingest(conn, "test_ns", graph_json_edges_alias)
    assert result["entities"] == 2
    assert result["triples"] == 1
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# Ingest — malformed nodes/edges skipped + counted
# ---------------------------------------------------------------------------

def test_ingest_skips_malformed(conn, tmp_path):
    data = {
        "nodes": [
            {"id": "ok1", "label": "Good"},
            {"label": "no-id-field"},  # malformed: missing 'id'
        ],
        "links": [
            {"source": "ok1", "target": "missing_target"},  # target entity missing but triple still valid
            {"source": "ok1"},  # malformed: missing 'target'
        ],
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    result = ingest_job.ingest(conn, "test_ns", p)
    # 1 good node, 1 bad node → skipped=1
    assert result["entities"] == 1
    assert result["skipped"] >= 1


# ---------------------------------------------------------------------------
# Ingest — confidence type → score mapping
# ---------------------------------------------------------------------------

def test_ingest_confidence_mapping(conn, graph_json):
    ingest_job.ingest(conn, "test_ns", graph_json)
    store = GraphStore(conn, "test_ns")
    # n1→n2: EXTRACTED → default 1.0
    row = store.conn.execute(
        "SELECT confidence_type, confidence_score FROM triples WHERE namespace='test_ns' AND subj_id='n1' AND obj_id='n2'"
    ).fetchone()
    assert row["confidence_type"] == "EXTRACTED"
    assert row["confidence_score"] == 1.0
    # n3→n1: INFERRED → default 0.75
    row = store.conn.execute(
        "SELECT confidence_type, confidence_score FROM triples WHERE namespace='test_ns' AND subj_id='n3' AND obj_id='n1'"
    ).fetchone()
    assert row["confidence_type"] == "INFERRED"
    assert row["confidence_score"] == 0.75
    # n4→n3: AMBIGUOUS, explicit confidence_score=0.15
    row = store.conn.execute(
        "SELECT confidence_type, confidence_score FROM triples WHERE namespace='test_ns' AND subj_id='n4' AND obj_id='n3'"
    ).fetchone()
    assert row["confidence_type"] == "AMBIGUOUS"
    assert abs(row["confidence_score"] - 0.15) < 1e-6


# ---------------------------------------------------------------------------
# Ingest — idempotent re-ingest
# ---------------------------------------------------------------------------

def test_ingest_idempotent(conn, graph_json):
    r1 = ingest_job.ingest(conn, "test_ns", graph_json)
    r2 = ingest_job.ingest(conn, "test_ns", graph_json)
    # Triple count in DB should not grow on second ingest
    triple_count = conn.execute(
        "SELECT COUNT(*) AS n FROM triples WHERE namespace='test_ns'"
    ).fetchone()["n"]
    assert triple_count == r1["triples"]
    # Second ingest returns same entity/triple counts (entities upserted, triples skipped)
    assert r2["entities"] == r1["entities"]
    assert r2["triples"] == r1["triples"]


# ---------------------------------------------------------------------------
# dedup_entities
# ---------------------------------------------------------------------------

def test_dedup_merges_same_label(store):
    t0 = int(time.time()) - 100
    store.upsert_entity("dup1", "AuthModule", now=t0)
    store.upsert_entity("dup2", "AuthModule", now=t0 + 50)  # duplicate label
    # Add a triple referencing dup2
    store.add_triple("dup2", "calls", "dup1", now=t0 + 60)

    merged = store.dedup_entities()
    assert merged >= 1

    # canonical = oldest → dup1; dup2 should be gone
    dup2_entity = store.get_entity("dup2")
    assert dup2_entity is None, "duplicate entity should be deleted"

    # triple's subj_id should be rewritten to canonical
    row = store.conn.execute(
        "SELECT subj_id FROM triples WHERE namespace='test_ns'"
    ).fetchone()
    assert row["subj_id"] == "dup1"


# ---------------------------------------------------------------------------
# shortest_path
# ---------------------------------------------------------------------------

def test_shortest_path_finds_path(store):
    store.upsert_entity("x", "X")
    store.upsert_entity("y", "Y")
    store.upsert_entity("z", "Z")
    store.add_triple("x", "links", "y")
    store.add_triple("y", "links", "z")
    path = store.shortest_path("x", "z")
    assert path is not None
    assert path[0] == "x"
    assert path[-1] == "z"
    assert "y" in path


def test_shortest_path_returns_none_when_disconnected(store):
    store.upsert_entity("x", "X")
    store.upsert_entity("z", "Z")
    path = store.shortest_path("x", "z")
    assert path is None


def test_shortest_path_same_node(store):
    store.upsert_entity("x", "X")
    assert store.shortest_path("x", "x") == ["x"]


# ---------------------------------------------------------------------------
# graph_query tool
# ---------------------------------------------------------------------------

def test_graph_query_returns_entities_and_neighbors(conn, graph_json):
    ingest_job.ingest(conn, "test_ns", graph_json)
    result = tools.graph_query(conn, text="Auth", limit=10, namespace="test_ns")
    assert result["count"] >= 1
    assert any(e["label"] == "AuthModule" for e in result["entities"])
    # Each entity should have neighbors key
    for entity in result["entities"]:
        assert "neighbors" in entity


# ---------------------------------------------------------------------------
# graph_ingest tool
# ---------------------------------------------------------------------------

def test_graph_ingest_tool_returns_counts(conn, graph_json):
    result = tools.graph_ingest(conn, path=str(graph_json), namespace="test_ns")
    assert result["ok"] is True
    assert result["entities"] == 4
    assert result["triples"] == 3


def test_graph_ingest_tool_bad_path(conn):
    result = tools.graph_ingest(conn, path="/nonexistent/path/graph.json", namespace="test_ns")
    assert result["ok"] is False
    assert "reason" in result
