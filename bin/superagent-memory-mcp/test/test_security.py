"""Security regression tests — pin path traversal (F1) and mass-forget (F2).

These lock in the fixes from the 2026-06 memory-os security review. See the
"Security model" section of the package README for the documented residual
risks (cloud embed fallback, remote Qdrant URL).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from memory_os import db, tools


@pytest.fixture
def conn():
    tmp = Path(tempfile.mkdtemp()) / "memory.db"
    c = db.connect(tmp)
    yield c
    c.close()


# --- F1: namespace validation / pin path traversal ---------------------------

@pytest.mark.parametrize(
    "bad",
    [
        "../../../tmp/evil",
        "a/b",
        "a\\b",
        "..",
        "ns/../..",
        "",
        "x" * 65,
        "ns\x00",
        "ns name",  # whitespace
    ],
)
def test_write_rejects_unsafe_namespace(conn, bad):
    with pytest.raises(ValueError):
        db.write_entry(conn, namespace=bad, kind="fact", content="x")


@pytest.mark.parametrize("good", ["__global__", "a1b2c3d4e5f60718", "my-project.v2", "NS_1"])
def test_write_accepts_safe_namespace(conn, good):
    entry = db.write_entry(conn, namespace=good, kind="fact", content="x")
    assert entry.namespace == good


def test_pin_refuses_path_escape(conn, tmp_path):
    """Even a hostile row that predates validation must not escape pin_dir."""
    entry = db.write_entry(conn, namespace="safe-ns", kind="fact", content="x")
    # Simulate a legacy/hostile row written before validation existed.
    conn.execute("UPDATE entries SET namespace = ? WHERE id = ?", ("../evil", entry.id))
    with pytest.raises(ValueError, match="escapes pin dir"):
        db.pin_entry(conn, entry.id, tmp_path / "pins")
    # Nothing was written outside the pin dir.
    assert not (tmp_path / f"evil__{entry.id}.md").exists()


def test_pin_normal_case_still_works(conn, tmp_path):
    entry = db.write_entry(conn, namespace="safe-ns", kind="fact", content="pin me")
    path = db.pin_entry(conn, entry.id, tmp_path / "pins")
    assert path.exists()
    assert path.parent == (tmp_path / "pins")


# --- F2: mass-forget guard ----------------------------------------------------

@pytest.mark.parametrize("pattern", ["%", "_", "%%", "_%_", " % ", "ab%"])
def test_forget_refuses_low_literal_patterns(conn, pattern):
    db.write_entry(conn, namespace="ns", kind="fact", content="keep me around")
    result = tools.memory_forget(conn, id_or_pattern=pattern, namespace="ns")
    assert result["deleted"] == 0
    assert len(db.list_entries(conn, namespace="ns")) == 1


def test_forget_with_meaningful_pattern_still_works(conn):
    db.write_entry(conn, namespace="ns", kind="fact", content="obsolete postgres tip")
    db.write_entry(conn, namespace="ns", kind="fact", content="keep this redis note")
    result = tools.memory_forget(conn, id_or_pattern="%postgres%", namespace="ns")
    assert result["deleted"] == 1
    remaining = db.list_entries(conn, namespace="ns")
    assert len(remaining) == 1 and "redis" in remaining[0].content


def test_forget_by_exact_id_unaffected(conn):
    entry = db.write_entry(conn, namespace="ns", kind="fact", content="bye")
    result = tools.memory_forget(conn, id_or_pattern=entry.id, namespace="ns")
    assert result["deleted"] == 1
