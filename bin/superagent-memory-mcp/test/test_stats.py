"""Phase 6.1 telemetry tests — local-only counters + stats aggregates."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from memory_os import db, tools
from memory_os.jobs import dedup as dedup_job


@pytest.fixture
def conn():
    tmp = Path(tempfile.mkdtemp()) / "memory.db"
    c = db.connect(tmp)
    yield c
    c.close()


def test_write_and_recall_bump_counters(conn):
    tools.memory_write(conn, content="postgres prod database", kind="fact", namespace="ns")
    tools.memory_write(conn, content="redis cache layer", kind="fact", namespace="ns")
    tools.memory_recall(conn, query="postgres", namespace="ns")
    s = db.stats(conn)
    assert s["counters"]["write"] == 2
    assert s["counters"]["recall"] == 1


def test_stats_entry_aggregates(conn):
    tools.memory_write(conn, content="a fact", kind="fact", namespace="ns1")
    tools.memory_write(conn, content="a decision", kind="decision", namespace="ns2")
    e = db.write_entry(conn, namespace="ns1", kind="fact", content="bye")
    db.forget_entries(conn, namespace="ns1", id_or_pattern=e.id)
    s = db.stats(conn)
    assert s["entries"]["total"] == 3
    assert s["entries"]["live"] == 2
    assert s["entries"]["archived"] == 1
    assert s["entries"]["namespaces"] == 2
    assert s["entries"]["by_kind"] == {"fact": 1, "decision": 1}


def test_telemetry_off_switch(conn, monkeypatch):
    monkeypatch.setenv("SUPERAGENT_MEMORY_TELEMETRY", "off")
    tools.memory_write(conn, content="quiet write", kind="fact", namespace="ns")
    s = db.stats(conn)
    assert s["counters"] == {}
    assert s["telemetry"] == "off"
    # The write itself still happened — only counting is disabled.
    assert s["entries"]["live"] == 1


def test_dedup_bumps_merge_counter(conn):
    vocab = ["postgres", "redis"]

    def fake_embed(text: str) -> list[float]:
        return [float(text.count(t)) for t in vocab]

    db.write_entry(conn, namespace="ns", kind="fact", content="postgres postgres")
    db.write_entry(conn, namespace="ns", kind="fact", content="postgres postgres")
    dedup_job.dedup(conn, namespace="ns", embed_fn=fake_embed)
    assert db.stats(conn)["counters"]["dedup_merge"] == 1


def test_decay_bumps_archive_counter(conn):
    from memory_os.jobs import decay as decay_job

    db.write_entry(conn, namespace="ns", kind="fact", content="ancient note")
    # Make it stale: created and last accessed 200 days ago.
    conn.execute("UPDATE entries SET ts = ts - 200*86400, last_access = last_access - 200*86400")
    decay_job.decay(conn)
    assert db.stats(conn)["counters"]["decay_archive"] == 1


def test_counter_namespaced_rollup(conn):
    tools.memory_write(conn, content="one", kind="fact", namespace="ns1")
    tools.memory_write(conn, content="two", kind="fact", namespace="ns2")
    # stats rolls counters up across namespaces
    assert db.stats(conn)["counters"]["write"] == 2
