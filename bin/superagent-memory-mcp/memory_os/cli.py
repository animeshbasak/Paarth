"""Command-line entry point for memory-os lifecycle jobs.

    superagent-memory decay [--dry-run] [--max-age-days N] [--idle-days N] [--namespace NS]
    superagent-memory cron  {install|uninstall|status}

The MCP server itself is a separate console script (``superagent-memory-mcp``);
this CLI is for maintenance jobs run by hooks or cron.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import cron_install, db
from .jobs import decay as decay_job


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


def _cmd_cron(args: argparse.Namespace) -> dict:
    if args.action == "install":
        return cron_install.install()
    if args.action == "uninstall":
        return cron_install.uninstall()
    return cron_install.status()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="superagent-memory", description="memory-os maintenance jobs")
    sub = parser.add_subparsers(dest="command", required=True)

    d = sub.add_parser("decay", help="archive stale entries")
    d.add_argument("--dry-run", action="store_true", help="report without mutating")
    d.add_argument("--max-age-days", type=int, default=decay_job.DEFAULT_MAX_AGE_DAYS)
    d.add_argument("--idle-days", type=int, default=decay_job.DEFAULT_IDLE_DAYS)
    d.add_argument("--namespace", default=None, help="limit to one namespace (default: all)")
    d.set_defaults(func=_cmd_decay)

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
