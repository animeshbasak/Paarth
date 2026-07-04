"""Command-line entry point for memory-os lifecycle jobs.

    paarth-memory decay [--dry-run] [--max-age-days N] [--idle-days N] [--namespace NS]
    paarth-memory dedup [--dry-run] [--threshold T] [--namespace NS]
    paarth-memory stats
    paarth-memory bench [--k N] [--real]
    paarth-memory cron  {install|uninstall|status}

The MCP server itself is a separate console script (``paarth-memory-mcp``);
this CLI is for maintenance jobs run by hooks or cron.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import cron_install, db, vector
from .jobs import decay as decay_job
from .jobs import dedup as dedup_job


def _cmd_decay(args: argparse.Namespace) -> dict:
    conn = db.connect()
    result = decay_job.decay(
        conn,
        max_age_days=args.max_age_days,
        idle_days=args.idle_days,
        namespace=args.namespace,
        dry_run=args.dry_run,
    )
    return result.to_dict()


def _cmd_dedup(args: argparse.Namespace) -> dict:
    # Dedup needs embeddings; refuse cleanly rather than embedding every row
    # against a backend the user never opted into.
    if not vector.is_enabled():
        return {
            "ok": False,
            "reason": "vector-disabled",
            "hint": "Semantic dedup needs embeddings. Enable with PAARTH_MEMORY_VECTOR=on.",
        }
    conn = db.connect()
    result = dedup_job.dedup(
        conn,
        namespace=args.namespace,
        threshold=args.threshold,
        dry_run=args.dry_run,
    )
    return {"ok": True, **result.to_dict()}


def _cmd_stats(args: argparse.Namespace) -> dict:
    conn = db.connect()
    return db.stats(conn)


def _cmd_bench(args: argparse.Namespace) -> dict:
    from . import bench

    embed_fn = None
    if args.real:
        from .vector import embed as embed_mod

        embed_fn = embed_mod.embed
    return bench.run_bench(k=args.k, embed_fn=embed_fn)


def _cmd_cron(args: argparse.Namespace) -> dict:
    if args.action == "install":
        return cron_install.install()
    if args.action == "uninstall":
        return cron_install.uninstall()
    return cron_install.status()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paarth-memory", description="memory-os maintenance jobs")
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("decay", help="archive stale entries")
    d.add_argument("--dry-run", action="store_true", help="report without mutating")
    d.add_argument("--max-age-days", type=int, default=decay_job.DEFAULT_MAX_AGE_DAYS)
    d.add_argument("--idle-days", type=int, default=decay_job.DEFAULT_IDLE_DAYS)
    d.add_argument("--namespace", default=None, help="limit to one namespace (default: all)")
    d.set_defaults(func=_cmd_decay)

    dd = sub.add_parser("dedup", help="merge near-duplicate entries (needs PAARTH_MEMORY_VECTOR=on)")
    dd.add_argument("--dry-run", action="store_true", help="report without mutating")
    dd.add_argument("--threshold", type=float, default=dedup_job.DEFAULT_THRESHOLD, help="cosine similarity to merge (0,1]")
    dd.add_argument("--namespace", default=None, help="limit to one namespace (default: all)")
    dd.set_defaults(func=_cmd_dedup)

    s = sub.add_parser("stats", help="local usage counters + store aggregates (never leaves this machine)")
    s.set_defaults(func=_cmd_stats)

    b = sub.add_parser("bench", help="rediscovery bench: FTS-only vs hybrid recall on a fixture corpus")
    b.add_argument("--k", type=int, default=5, help="top-k cutoff for a hit (default 5)")
    b.add_argument("--real", action="store_true", help="use the real Ollama/OpenRouter embedder instead of the simulated one")
    b.set_defaults(func=_cmd_bench)

    c = sub.add_parser("cron", help="schedule weekly decay (launchd/crontab)")
    c.add_argument("action", choices=["install", "uninstall", "status"])
    c.set_defaults(func=_cmd_cron)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
