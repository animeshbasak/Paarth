"""Decay scanner — archives stale memory entries.

Ported in spirit from memory-os ``scripts/decay_scanner.py``. An entry is
considered *stale* and archived (soft-deleted: ``forgotten = 1``) when ALL of:

  - it is not pinned (pinned entries are permanent),
  - it is not already forgotten,
  - it was created more than ``max_age_days`` ago, AND
  - it has not been accessed in the last ``idle_days`` days.

Archiving is reversible at the DB level (the row stays with ``forgotten = 1``)
and every archive is recorded in the ``audit`` table with action ``decay``.

Run via the CLI: ``superagent-memory decay [--dry-run]``.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

from .. import db

DAY_SECONDS = 86_400

DEFAULT_MAX_AGE_DAYS = 90
DEFAULT_IDLE_DAYS = 30


@dataclass(frozen=True)
class DecayResult:
    scanned: int
    archived: int
    archived_ids: tuple[str, ...]
    dry_run: bool
    max_age_days: int
    idle_days: int

    def to_dict(self) -> dict:
        return {
            "scanned": self.scanned,
            "archived": self.archived,
            "archived_ids": list(self.archived_ids),
            "dry_run": self.dry_run,
            "max_age_days": self.max_age_days,
            "idle_days": self.idle_days,
        }


def decay(
    conn: sqlite3.Connection,
    *,
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    idle_days: int = DEFAULT_IDLE_DAYS,
    namespace: str | None = None,
    dry_run: bool = False,
    now: float | None = None,
) -> DecayResult:
    """Archive stale entries. Returns a :class:`DecayResult` summary.

    ``namespace`` limits the scan to one project store; ``None`` scans all.
    ``dry_run`` reports what would be archived without mutating anything.
    ``now`` is injectable for deterministic testing.
    """
    if max_age_days < 0 or idle_days < 0:
        raise ValueError("max_age_days and idle_days must be non-negative")

    now = time.time() if now is None else now
    age_cutoff = now - max_age_days * DAY_SECONDS
    idle_cutoff = now - idle_days * DAY_SECONDS

    clauses = [
        "pinned = 0",
        "forgotten = 0",
        "ts < ?",
        "last_access < ?",
    ]
    params: list = [age_cutoff, idle_cutoff]
    if namespace is not None:
        clauses.append("namespace = ?")
        params.append(namespace)

    where = " AND ".join(clauses)
    scanned = conn.execute(
        "SELECT COUNT(*) AS n FROM entries WHERE forgotten = 0"
        + ("" if namespace is None else " AND namespace = ?"),
        ([] if namespace is None else [namespace]),
    ).fetchone()["n"]

    rows = conn.execute(
        f"SELECT id, namespace FROM entries WHERE {where}",
        params,
    ).fetchall()
    ids = [r["id"] for r in rows]

    if not dry_run and ids:
        conn.execute(
            f"UPDATE entries SET forgotten = 1 WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
        db.bump_counter(conn, "decay_archive", namespace or "", by=len(ids))
        for r in rows:
            db._audit(
                conn,
                "decay",
                r["id"],
                r["namespace"],
                {"max_age_days": max_age_days, "idle_days": idle_days},
            )

    return DecayResult(
        scanned=scanned,
        archived=len(ids),
        archived_ids=tuple(ids),
        dry_run=dry_run,
        max_age_days=max_age_days,
        idle_days=idle_days,
    )
