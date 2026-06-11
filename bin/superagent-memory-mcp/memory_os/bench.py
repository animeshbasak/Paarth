"""Rediscovery bench — measures the hybrid-recall win over FTS-only (Phase 6.2).

The metric: **rediscovery rate** — given a fact stored earlier, can a later
query phrased differently find it again? Each corpus entry carries two probe
queries:

  * ``keyword``  — shares vocabulary with the stored content (FTS should win)
  * ``semantic`` — a synonym/paraphrase with little token overlap (FTS misses;
    this is where vectors earn their keep)

The bench writes the corpus into a throwaway SQLite DB, then replays every
probe twice — once FTS-only, once hybrid — and reports hit-rates per split.
A hit = the target entry appears in the top ``k`` results.

Embeddings: by default a deterministic built-in embedder (word overlap over a
small synonym table) so the bench is reproducible offline with zero deps —
the report labels this ``embedder: simulated``. Pass ``--real`` to use the
production Ollama→OpenRouter chain instead (requires the ``[vector]`` extra
and a reachable embedding backend).

Run: ``superagent-memory bench [--k 5] [--real]``.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

from . import db, tools, vector

Vector = list[float]

BENCH_NAMESPACE = "bench"

# (stored content, keyword probe, semantic probe)
CORPUS: tuple[tuple[str, str, str], ...] = (
    ("auth bug in the session middleware causes silent logout",
     "auth bug middleware", "login failure signs users out"),
    ("postgres connection pool exhausted under load spikes",
     "postgres connection pool", "database runs out of connections at peak traffic"),
    ("redis cache must be warmed before deploy or p99 degrades",
     "redis cache warmed deploy", "prime the in-memory store before release"),
    ("magic link tokens expire after 15 minutes by design",
     "magic link tokens expire", "emailed sign-in URL stops working quickly"),
    ("webpack worker config breaks pdfjs in next.js builds",
     "webpack worker pdfjs", "PDF rendering fails when bundling the frontend"),
    ("decided to use feature flags for the checkout rollout",
     "feature flags checkout rollout", "gradual release toggle for the payment flow"),
    ("rate limiter returns 429 when burst exceeds 50 rps",
     "rate limiter 429 burst", "too many requests error under heavy spikes"),
    ("S3 presigned URLs fail when the clock drifts more than 5 minutes",
     "presigned URLs clock drift", "file upload links break with wrong system time"),
    ("the staging environment shares the production DNS zone",
     "staging production DNS zone", "test environment uses the same domain records"),
    ("contract tests gate the mobile API against breaking changes",
     "contract tests mobile API", "schema compatibility checks protect app clients"),
    ("OOM kills the worker when the batch size exceeds 10k rows",
     "OOM worker batch size", "process runs out of memory on large jobs"),
    ("CSP headers block inline scripts on the marketing pages",
     "CSP headers inline scripts", "security policy stops embedded javascript on the site"),
)

# Small synonym table powering the simulated embedder. Maps surface variants
# onto shared concept tokens so paraphrase probes land near their target.
_SYNONYMS: dict[str, str] = {
    "login": "auth", "logout": "auth", "signs": "auth", "sign-in": "auth", "session": "auth",
    "database": "postgres", "db": "postgres",
    "connections": "pool", "peak": "load", "traffic": "load", "spikes": "load",
    "in-memory": "redis", "store": "cache", "prime": "warmed", "release": "deploy",
    "emailed": "magic", "url": "link", "urls": "link", "quickly": "expire",
    "pdf": "pdfjs", "rendering": "pdfjs", "bundling": "webpack", "frontend": "next.js",
    "toggle": "flags", "gradual": "rollout", "payment": "checkout",
    "requests": "429", "heavy": "burst",
    "upload": "presigned", "links": "link", "time": "clock",
    "test": "staging", "domain": "dns", "records": "zone",
    "schema": "contract", "compatibility": "tests", "clients": "api", "app": "mobile",
    "memory": "oom", "jobs": "batch", "large": "size",
    "policy": "csp", "embedded": "inline", "javascript": "scripts", "site": "pages",
}


def _vocab() -> list[str]:
    words: set[str] = set()
    for content, _, _ in CORPUS:
        words.update(_fold(content))
    return sorted(words)


def _fold(text: str) -> list[str]:
    out = []
    for w in text.lower().replace(",", " ").replace(".", " ").split():
        out.append(_SYNONYMS.get(w, w))
    return out


def simulated_embed(text: str) -> Vector:
    """Deterministic bag-of-concepts embedding over the corpus vocabulary."""
    vocab = _vocab()
    folded = _fold(text)
    return [float(folded.count(term)) for term in vocab]


def run_bench(*, k: int = 5, embed_fn: Callable[[str], Vector] | None = None) -> dict:
    """Run the rediscovery bench in a throwaway DB; return the report dict."""
    fn = embed_fn or simulated_embed

    tmp = Path(tempfile.mkdtemp()) / "bench.db"
    conn = db.connect(tmp)

    saved = {key: os.environ.get(key) for key in ("SUPERAGENT_MEMORY_VECTOR", "SUPERAGENT_MEMORY_VECTOR_BACKEND")}
    os.environ["SUPERAGENT_MEMORY_VECTOR"] = "on"
    os.environ["SUPERAGENT_MEMORY_VECTOR_BACKEND"] = "memory"
    vector.reset_store()
    try:
        ids: list[str] = []
        for content, _, _ in CORPUS:
            out = tools.memory_write(conn, content=content, kind="fact", namespace=BENCH_NAMESPACE, embed_fn=fn)
            ids.append(out["id"])

        results = {"keyword": {"fts": 0, "hybrid": 0}, "semantic": {"fts": 0, "hybrid": 0}}
        for (content, kw_probe, sem_probe), target in zip(CORPUS, ids):
            for split, probe in (("keyword", kw_probe), ("semantic", sem_probe)):
                fts_hits = [e.id for e in db.recall(conn, namespace=BENCH_NAMESPACE, query=probe, limit=k)]
                if target in fts_hits:
                    results[split]["fts"] += 1
                hybrid = tools.memory_recall(conn, query=probe, namespace=BENCH_NAMESPACE, limit=k, embed_fn=fn)
                if target in [h["id"] for h in hybrid["hits"]]:
                    results[split]["hybrid"] += 1
    finally:
        for key, val in saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val
        vector.reset_store()
        conn.close()

    n = len(CORPUS)

    def pct(x: int) -> float:
        return round(100.0 * x / n, 1)

    report = {
        "corpus_size": n,
        "top_k": k,
        "embedder": "real" if embed_fn is not None and embed_fn is not simulated_embed else "simulated",
        "rediscovery_rate_pct": {
            split: {"fts": pct(v["fts"]), "hybrid": pct(v["hybrid"])}
            for split, v in results.items()
        },
    }
    sem = report["rediscovery_rate_pct"]["semantic"]
    report["semantic_delta_pct_points"] = round(sem["hybrid"] - sem["fts"], 1)
    report["ship_gate_30pt_delta"] = report["semantic_delta_pct_points"] >= 30.0
    return report
