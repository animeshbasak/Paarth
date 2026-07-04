"""Tests for the decay scanner and cron-line generators."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from memory_os import cron_install, db
from memory_os.jobs import decay as decay_job

DAY = decay_job.DAY_SECONDS


@pytest.fixture
def conn():
    tmp = Path(tempfile.mkdtemp()) / "memory.db"
    c = db.connect(tmp)
    yield c
    c.close()


def _backdate(conn, entry_id: str, *, age_days: float, idle_days: float, now: float) -> None:
    conn.execute(
        "UPDATE entries SET ts = ?, last_access = ? WHERE id = ?",
        (now - age_days * DAY, now - idle_days * DAY, entry_id),
    )


# ── schema migration ───────────────────────────────────────────────────────────

def test_last_access_column_present(conn) -> None:
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(entries)").fetchall()}
    assert "last_access" in cols


def test_write_sets_last_access_to_ts(conn) -> None:
    e = db.write_entry(conn, namespace="ns", kind="fact", content="hello")
    row = conn.execute("SELECT ts, last_access FROM entries WHERE id = ?", (e.id,)).fetchone()
    assert row["last_access"] == pytest.approx(row["ts"])


def test_recall_bumps_last_access(conn) -> None:
    e = db.write_entry(conn, namespace="ns", kind="fact", content="postgres prod database")
    before = conn.execute("SELECT last_access FROM entries WHERE id = ?", (e.id,)).fetchone()["last_access"]
    time.sleep(0.01)
    db.recall(conn, namespace="ns", query="postgres")
    after = conn.execute("SELECT last_access FROM entries WHERE id = ?", (e.id,)).fetchone()["last_access"]
    assert after > before


# ── decay behavior ──────────────────────────────────────────────────────────────

def test_decay_archives_old_and_idle(conn) -> None:
    now = time.time()
    stale = db.write_entry(conn, namespace="ns", kind="fact", content="stale entry")
    _backdate(conn, stale.id, age_days=120, idle_days=60, now=now)

    res = decay_job.decay(conn, max_age_days=90, idle_days=30, now=now)
    assert res.archived == 1
    assert stale.id in res.archived_ids
    row = conn.execute("SELECT forgotten FROM entries WHERE id = ?", (stale.id,)).fetchone()
    assert row["forgotten"] == 1


def test_decay_keeps_recent(conn) -> None:
    now = time.time()
    fresh = db.write_entry(conn, namespace="ns", kind="fact", content="fresh entry")
    _backdate(conn, fresh.id, age_days=5, idle_days=1, now=now)
    res = decay_job.decay(conn, max_age_days=90, idle_days=30, now=now)
    assert res.archived == 0


def test_decay_keeps_old_but_recently_accessed(conn) -> None:
    now = time.time()
    e = db.write_entry(conn, namespace="ns", kind="fact", content="old but used")
    _backdate(conn, e.id, age_days=200, idle_days=2, now=now)  # old, but accessed 2 days ago
    res = decay_job.decay(conn, max_age_days=90, idle_days=30, now=now)
    assert res.archived == 0


def test_decay_never_touches_pinned(conn) -> None:
    now = time.time()
    e = db.write_entry(conn, namespace="ns", kind="fact", content="pinned old idle")
    _backdate(conn, e.id, age_days=300, idle_days=300, now=now)
    conn.execute("UPDATE entries SET pinned = 1 WHERE id = ?", (e.id,))
    res = decay_job.decay(conn, max_age_days=90, idle_days=30, now=now)
    assert res.archived == 0


def test_decay_dry_run_does_not_mutate(conn) -> None:
    now = time.time()
    e = db.write_entry(conn, namespace="ns", kind="fact", content="stale dry run")
    _backdate(conn, e.id, age_days=200, idle_days=200, now=now)
    res = decay_job.decay(conn, max_age_days=90, idle_days=30, dry_run=True, now=now)
    assert res.archived == 1 and res.dry_run is True
    row = conn.execute("SELECT forgotten FROM entries WHERE id = ?", (e.id,)).fetchone()
    assert row["forgotten"] == 0


def test_decay_namespace_scoped(conn) -> None:
    now = time.time()
    a = db.write_entry(conn, namespace="ns_a", kind="fact", content="stale a")
    b = db.write_entry(conn, namespace="ns_b", kind="fact", content="stale b")
    for e in (a, b):
        _backdate(conn, e.id, age_days=200, idle_days=200, now=now)
    res = decay_job.decay(conn, max_age_days=90, idle_days=30, namespace="ns_a", now=now)
    assert res.archived == 1 and a.id in res.archived_ids
    assert conn.execute("SELECT forgotten FROM entries WHERE id = ?", (b.id,)).fetchone()["forgotten"] == 0


def test_decay_writes_audit_rows(conn) -> None:
    now = time.time()
    e = db.write_entry(conn, namespace="ns", kind="fact", content="audited stale")
    _backdate(conn, e.id, age_days=200, idle_days=200, now=now)
    decay_job.decay(conn, max_age_days=90, idle_days=30, now=now)
    n = conn.execute("SELECT COUNT(*) AS n FROM audit WHERE action = 'decay'").fetchone()["n"]
    assert n == 1


def test_decay_rejects_negative_args(conn) -> None:
    with pytest.raises(ValueError):
        decay_job.decay(conn, max_age_days=-1, idle_days=30)


# ── cron line generators (pure) ────────────────────────────────────────────────

def test_crontab_line_has_marker() -> None:
    line = cron_install.crontab_line(["python", "-m", "memory_os.cli", "decay"])
    assert cron_install.CRON_MARKER in line
    assert "decay" in line


def test_launchd_plist_well_formed() -> None:
    plist = cron_install.launchd_plist(["python", "-m", "memory_os.cli", "decay"], 604800)
    assert cron_install.LABEL in plist
    assert "<integer>604800</integer>" in plist
    assert plist.startswith("<?xml")
