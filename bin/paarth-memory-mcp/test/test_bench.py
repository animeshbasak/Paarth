"""Phase 6.2 bench-harness tests.

The bench itself is deterministic (simulated embedder, fixed corpus), so we
can assert the actual shape of the win, not just that it runs.
"""

from __future__ import annotations

import os

from memory_os import bench


def test_bench_runs_and_reports():
    report = bench.run_bench(k=5)
    assert report["corpus_size"] == len(bench.CORPUS)
    assert report["embedder"] == "simulated"
    rates = report["rediscovery_rate_pct"]
    assert set(rates) == {"keyword", "semantic"}
    for split in rates.values():
        assert 0.0 <= split["fts"] <= 100.0
        assert 0.0 <= split["hybrid"] <= 100.0


def test_hybrid_beats_fts_on_semantic_split():
    report = bench.run_bench(k=5)
    sem = report["rediscovery_rate_pct"]["semantic"]
    assert sem["hybrid"] > sem["fts"], report
    # The ship-gate: ≥30-point rediscovery delta on paraphrase probes.
    assert report["ship_gate_30pt_delta"] is True, report


def test_hybrid_does_not_regress_keyword_split():
    report = bench.run_bench(k=5)
    kw = report["rediscovery_rate_pct"]["keyword"]
    assert kw["hybrid"] >= kw["fts"], report


def test_bench_is_deterministic():
    assert bench.run_bench(k=5) == bench.run_bench(k=5)


def test_bench_restores_environment():
    before_flag = os.environ.get("PAARTH_MEMORY_VECTOR")
    before_backend = os.environ.get("PAARTH_MEMORY_VECTOR_BACKEND")
    bench.run_bench(k=3)
    assert os.environ.get("PAARTH_MEMORY_VECTOR") == before_flag
    assert os.environ.get("PAARTH_MEMORY_VECTOR_BACKEND") == before_backend
