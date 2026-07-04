"""Opt-in vector recall (Phase 5).

Gated behind ``PAARTH_MEMORY_VECTOR=on``. The default install never imports
qdrant-client or makes a network call; this package only activates when the
flag is set. ``InMemoryStore`` provides a zero-dependency fallback (and the
test backend) so hybrid recall works without a running Qdrant.

Public API (all no-ops unless the flag is on):
  is_enabled()    — gate check
  index_entry()   — embed + upsert on write (best-effort)
  vector_search() — embed query + cosine search
  delete_entry()  — drop from the index on forget
  reciprocal_rank_fusion() — blend FTS + vector rankings
"""

from .recall import RRF_K, reciprocal_rank_fusion
from .service import (
    delete_entry,
    get_store,
    index_entry,
    is_enabled,
    reset_store,
    vector_search,
)
from .store import Hit

__all__ = [
    "is_enabled",
    "index_entry",
    "vector_search",
    "delete_entry",
    "get_store",
    "reset_store",
    "reciprocal_rank_fusion",
    "RRF_K",
    "Hit",
]
