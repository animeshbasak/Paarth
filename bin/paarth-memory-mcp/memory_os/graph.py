"""Persistent knowledge graph — entities + triples stored in SQLite.

Provides :class:`GraphStore` which wraps the ``entities`` and ``triples``
tables added in the Wave 3 schema migration.  All operations are
namespace-scoped so project isolation is preserved.
"""

from __future__ import annotations

import re
import sqlite3
import time
from collections import deque
from typing import Any


class GraphStore:
    """CRUD + traversal interface for the knowledge-graph tables."""

    def __init__(self, conn: sqlite3.Connection, namespace: str) -> None:
        self.conn = conn
        self.namespace = namespace

    # ------------------------------------------------------------------
    # Entity helpers
    # ------------------------------------------------------------------

    def upsert_entity(
        self,
        id: str,
        label: str,
        kind: str | None = None,
        source_file: str | None = None,
        community: int | None = None,
        now: int | None = None,
    ) -> str:
        """Insert entity or refresh ``last_seen``. Returns the canonical id."""
        ts = now if now is not None else int(time.time())
        existing = self.conn.execute(
            "SELECT id FROM entities WHERE namespace = ? AND id = ?",
            (self.namespace, id),
        ).fetchone()
        if existing:
            self.conn.execute(
                "UPDATE entities SET last_seen = ?, label = ?, kind = COALESCE(?, kind), "
                "source_file = COALESCE(?, source_file), community = COALESCE(?, community) "
                "WHERE namespace = ? AND id = ?",
                (ts, label, kind, source_file, community, self.namespace, id),
            )
        else:
            self.conn.execute(
                "INSERT INTO entities (id, namespace, label, kind, source_file, community, first_seen, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (id, self.namespace, label, kind, source_file, community, ts, ts),
            )
        return id

    def get_entity(self, id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT id, namespace, label, kind, source_file, community, first_seen, last_seen "
            "FROM entities WHERE namespace = ? AND id = ?",
            (self.namespace, id),
        ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Triple helpers
    # ------------------------------------------------------------------

    def add_triple(
        self,
        subj_id: str,
        predicate: str,
        obj_id: str,
        confidence_type: str = "EXTRACTED",
        confidence_score: float = 1.0,
        source_file: str | None = None,
        now: int | None = None,
    ) -> None:
        """Insert triple; idempotent — no-op if an identical currently-valid triple exists."""
        ts = now if now is not None else int(time.time())
        exists = self.conn.execute(
            "SELECT rowid FROM triples WHERE namespace=? AND subj_id=? AND predicate=? AND obj_id=? AND valid_to IS NULL",
            (self.namespace, subj_id, predicate, obj_id),
        ).fetchone()
        if exists:
            return
        self.conn.execute(
            "INSERT INTO triples (namespace, subj_id, predicate, obj_id, confidence_type, confidence_score, source_file, ts, valid_from, valid_to) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
            (self.namespace, subj_id, predicate, obj_id, confidence_type, confidence_score, source_file, ts, ts),
        )

    def supersede_triple(
        self,
        subj_id: str,
        predicate: str,
        obj_id: str,
        now: int | None = None,
    ) -> int:
        """Set valid_to=now on matching currently-valid triples. Returns rows affected."""
        ts = now if now is not None else int(time.time())
        cur = self.conn.execute(
            "UPDATE triples SET valid_to = ? "
            "WHERE namespace=? AND subj_id=? AND predicate=? AND obj_id=? AND valid_to IS NULL",
            (ts, self.namespace, subj_id, predicate, obj_id),
        )
        return cur.rowcount

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    def neighbors(self, entity_id: str, depth: int = 1, valid_only: bool = True) -> list[dict]:
        """Return all incident triples (both directions) up to ``depth`` hops."""
        visited_edges: list[dict] = []
        frontier = {entity_id}
        seen_nodes = {entity_id}

        validity_clause = "AND t.valid_to IS NULL" if valid_only else ""

        for _ in range(depth):
            if not frontier:
                break
            placeholders = ",".join("?" * len(frontier))
            rows = self.conn.execute(
                f"""
                SELECT t.subj_id, t.predicate, t.obj_id, t.confidence_type,
                       t.confidence_score, t.source_file, t.valid_from, t.valid_to
                FROM triples t
                WHERE t.namespace = ?
                  AND (t.subj_id IN ({placeholders}) OR t.obj_id IN ({placeholders}))
                  {validity_clause}
                """,
                [self.namespace, *frontier, *frontier],
            ).fetchall()
            next_frontier: set[str] = set()
            for row in rows:
                triple = dict(row)
                if triple not in visited_edges:
                    visited_edges.append(triple)
                for node in (row["subj_id"], row["obj_id"]):
                    if node not in seen_nodes:
                        next_frontier.add(node)
                        seen_nodes.add(node)
            frontier = next_frontier

        return visited_edges

    def shortest_path(self, a_id: str, b_id: str) -> list[str] | None:
        """BFS over currently-valid triples. Returns node id list or None."""
        if a_id == b_id:
            return [a_id]

        visited = {a_id}
        queue: deque[list[str]] = deque([[a_id]])

        while queue:
            path = queue.popleft()
            current = path[-1]
            rows = self.conn.execute(
                "SELECT subj_id, obj_id FROM triples "
                "WHERE namespace=? AND (subj_id=? OR obj_id=?) AND valid_to IS NULL",
                (self.namespace, current, current),
            ).fetchall()
            for row in rows:
                neighbour = row["obj_id"] if row["subj_id"] == current else row["subj_id"]
                if neighbour == b_id:
                    return path + [neighbour]
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(path + [neighbour])

        return None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, text: str, limit: int = 10) -> list[dict]:
        """Match entities by case-insensitive substring over label."""
        pattern = f"%{text}%"
        rows = self.conn.execute(
            "SELECT id, namespace, label, kind, source_file, community, first_seen, last_seen "
            "FROM entities WHERE namespace=? AND label LIKE ? COLLATE NOCASE "
            "ORDER BY last_seen DESC LIMIT ?",
            (self.namespace, pattern, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Dedup
    # ------------------------------------------------------------------

    def dedup_entities(self, threshold: float = 0.92) -> int:
        """Merge entities whose normalized labels are identical.

        Canonical = oldest (lowest first_seen). Rewrites triples' subj_id/obj_id
        from duplicate to canonical, then deletes the duplicate entity.

        If the vector embedder is available, also merges entities whose label
        embeddings have cosine >= threshold (mirroring jobs/dedup.py logic).
        Returns merge count.
        """
        rows = self.conn.execute(
            "SELECT id, label, first_seen FROM entities WHERE namespace=? ORDER BY first_seen ASC",
            (self.namespace,),
        ).fetchall()

        # Group by normalized label
        label_to_canonical: dict[str, str] = {}
        merged = 0

        for row in rows:
            norm = _normalize_label(row["label"])
            if norm in label_to_canonical:
                canonical_id = label_to_canonical[norm]
                self._merge_entity(duplicate_id=row["id"], canonical_id=canonical_id)
                merged += 1
            else:
                label_to_canonical[norm] = row["id"]

        # Optional: cosine dedup over remaining entities if vector available
        try:
            from .vector.store import cosine as cosine_fn
            from .vector import embed as embed_mod

            remaining = self.conn.execute(
                "SELECT id, label FROM entities WHERE namespace=?",
                (self.namespace,),
            ).fetchall()
            embedded: list[tuple[str, list[float]]] = []
            for r in remaining:
                try:
                    vec = embed_mod.embed(r["label"])
                    embedded.append((r["id"], vec))
                except Exception:
                    pass

            reps: list[tuple[str, list[float]]] = []
            for eid, vec in embedded:
                best_id = None
                best_sim = -1.0
                for rep_id, rep_vec in reps:
                    sim = cosine_fn(vec, rep_vec)
                    if sim > best_sim:
                        best_sim, best_id = sim, rep_id
                if best_id is not None and best_sim >= threshold:
                    # canonical is the already-established rep
                    exists = self.conn.execute(
                        "SELECT id FROM entities WHERE namespace=? AND id=?",
                        (self.namespace, eid),
                    ).fetchone()
                    rep_exists = self.conn.execute(
                        "SELECT id FROM entities WHERE namespace=? AND id=?",
                        (self.namespace, best_id),
                    ).fetchone()
                    if exists and rep_exists:
                        self._merge_entity(duplicate_id=eid, canonical_id=best_id)
                        merged += 1
                else:
                    reps.append((eid, vec))
        except Exception:
            pass  # vector backend not available — text dedup only

        return merged

    def _merge_entity(self, duplicate_id: str, canonical_id: str) -> None:
        """Rewrite triples from duplicate → canonical, delete duplicate entity."""
        self.conn.execute(
            "UPDATE triples SET subj_id=? WHERE namespace=? AND subj_id=?",
            (canonical_id, self.namespace, duplicate_id),
        )
        self.conn.execute(
            "UPDATE triples SET obj_id=? WHERE namespace=? AND obj_id=?",
            (canonical_id, self.namespace, duplicate_id),
        )
        self.conn.execute(
            "DELETE FROM entities WHERE namespace=? AND id=?",
            (self.namespace, duplicate_id),
        )


def _normalize_label(label: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for comparison."""
    label = label.lower().strip()
    label = re.sub(r"[^\w\s]", "", label)
    label = re.sub(r"\s+", " ", label)
    return label
