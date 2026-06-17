"""Ingest a graphify node-link JSON into the persistent knowledge graph.

Accepts the NetworkX node-link JSON produced by the ``graphify`` tool:
  {"nodes": [...], "links": [...]}   (also accepts "edges" in place of "links")

Each node becomes an entity; each link becomes a triple.  Missing optional
fields are tolerated.  Malformed nodes/edges are skipped and counted.
Re-ingesting the same file is idempotent (existing valid triples are no-ops).
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

from ..graph import GraphStore

# Default confidence score by type when confidence_score field is absent
_CONF_SCORE_DEFAULTS: dict[str, float] = {
    "EXTRACTED": 1.0,
    "INFERRED": 0.75,
    "AMBIGUOUS": 0.2,
}

# Recognise common aliases for the confidence string field
_CONF_TYPE_ALIASES: dict[str, str] = {
    "extracted": "EXTRACTED",
    "inferred": "INFERRED",
    "ambiguous": "AMBIGUOUS",
}


def ingest(
    conn: sqlite3.Connection,
    namespace: str,
    graph_json_path: str | Path,
) -> dict[str, Any]:
    """Parse graphify JSON and load entities + triples.

    Returns ``{"entities": int, "triples": int, "skipped": int}``.
    """
    path = Path(graph_json_path)
    raw = json.loads(path.read_text(encoding="utf-8"))

    nodes = raw.get("nodes") or []
    links = raw.get("links") or raw.get("edges") or []

    store = GraphStore(conn, namespace)
    now = int(time.time())

    entity_count = 0
    triple_count = 0
    skipped = 0

    for node in nodes:
        try:
            node_id = str(node["id"])
            label = str(node.get("label") or node_id)
            kind = node.get("file_type") or node.get("kind") or None
            source_file = node.get("source_file") or None
            community_raw = node.get("community")
            community = int(community_raw) if community_raw is not None else None
            store.upsert_entity(
                id=node_id,
                label=label,
                kind=kind,
                source_file=source_file,
                community=community,
                now=now,
            )
            entity_count += 1
        except Exception:
            skipped += 1
            continue

    for link in links:
        try:
            subj_id = str(link["source"])
            obj_id = str(link["target"])
            predicate = str(link.get("relation") or "related_to")

            conf_str = str(link.get("confidence") or "EXTRACTED").strip().upper()
            confidence_type = _CONF_TYPE_ALIASES.get(conf_str.lower(), conf_str)
            if confidence_type not in _CONF_SCORE_DEFAULTS:
                confidence_type = "EXTRACTED"

            raw_score = link.get("confidence_score")
            if raw_score is not None:
                confidence_score = float(raw_score)
            else:
                confidence_score = _CONF_SCORE_DEFAULTS[confidence_type]

            source_file = link.get("source_file") or None
            store.add_triple(
                subj_id=subj_id,
                predicate=predicate,
                obj_id=obj_id,
                confidence_type=confidence_type,
                confidence_score=confidence_score,
                source_file=source_file,
                now=now,
            )
            triple_count += 1
        except Exception:
            skipped += 1
            continue

    try:
        store.dedup_entities()
    except Exception:
        pass  # dedup failure never aborts ingest

    return {"entities": entity_count, "triples": triple_count, "skipped": skipped}
