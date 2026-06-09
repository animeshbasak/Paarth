"""Hybrid recall fusion (Phase 5, Task 5.3).

Reciprocal Rank Fusion (RRF) blends the FTS5/BM25 ranking with the vector
cosine ranking. RRF needs only the *order* of each list, not comparable
scores, which is exactly right here: BM25 ranks and cosine similarities live
on different scales and can't be added directly.

    score(d) = Σ  1 / (k + rank_i(d))

over each list ``i`` the document appears in. ``k`` (default 60, the value
from the original Cormack et al. RRF paper) damps the influence of top ranks
so a single list can't dominate.
"""

from __future__ import annotations

from typing import Sequence

RRF_K = 60


def reciprocal_rank_fusion(*ranked_lists: Sequence[str], k: int = RRF_K) -> list[str]:
    """Fuse ranked id lists into one, best-first.

    Each input is an ordered sequence of ids (rank 0 = best). Returns the
    union of all ids ordered by descending fused RRF score. Ties break by the
    id's best (lowest) rank across the inputs, then lexically, so the result
    is deterministic.
    """
    fused: dict[str, float] = {}
    best_rank: dict[str, int] = {}
    for ranked in ranked_lists:
        for rank, eid in enumerate(ranked):
            fused[eid] = fused.get(eid, 0.0) + 1.0 / (k + rank + 1)
            if eid not in best_rank or rank < best_rank[eid]:
                best_rank[eid] = rank
    return sorted(fused, key=lambda e: (-fused[e], best_rank[e], e))
