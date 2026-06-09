"""Project namespacing — isolates memory per git-root.

Strategy: hash the absolute path of the nearest git root above cwd. Falls back
to cwd itself if no git root exists. The hash is truncated to 16 hex chars,
which is collision-safe for any realistic user (~10^19 namespaces before a
50% collision probability).

A reserved namespace `__global__` is available for cross-project facts that
the user explicitly wants shared.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

GLOBAL_NAMESPACE = "__global__"


def git_root(start: Path | None = None) -> Path | None:
    """Return the nearest git-root above ``start`` (or cwd), or None."""
    cwd = (start or Path.cwd()).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).resolve()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Manual walk fallback (no git installed)
    for parent in (cwd, *cwd.parents):
        if (parent / ".git").exists():
            return parent
    return None


def namespace_for(start: Path | None = None) -> str:
    """Return the namespace identifier for the given cwd (or current cwd)."""
    env_override = os.environ.get("SUPERAGENT_MEMORY_NAMESPACE")
    if env_override:
        return env_override

    root = git_root(start) or (start or Path.cwd()).resolve()
    return hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]


def friendly_name(start: Path | None = None) -> str:
    """Human-readable label for the current namespace (e.g. for logs)."""
    root = git_root(start) or (start or Path.cwd()).resolve()
    return root.name
