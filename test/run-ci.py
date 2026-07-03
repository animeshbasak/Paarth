#!/usr/bin/env python3
"""CI shell-test runner: runs every test/test-*.sh with a per-test timeout,
skipping tests that cannot work on a fresh runner (reasons inline).

Usage: python3 test/run-ci.py [--timeout SECONDS]
Exit 0 when every non-skipped test passes.
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys

# name -> reason. Keep reasons honest; every skip is printed in the CI log.
# (test-canary.sh is NOT skipped: it self-hosts a mock on :18082 — it only
# fails on dev machines where the real proxy already holds the port.)
SKIP = {
    "test-agents-install.sh": "install.sh path hangs on `mempalace mine` (network/pipx)",
    "test-install-hooks.sh": "install.sh path hangs on `mempalace mine` (network/pipx)",
    "test-install-migration.sh": "install.sh path hangs on `mempalace mine` (network/pipx)",
    "test-install-wave2.sh": "install.sh path hangs on `mempalace mine` (network/pipx)",
    "test-install-wave3.sh": "install.sh path hangs on `mempalace mine` (network/pipx)",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    tests = sorted(glob.glob("test/test-*.sh"))
    if not tests:
        print("no tests found", file=sys.stderr)
        return 1

    passed, failed, skipped = 0, [], 0
    for t in tests:
        name = os.path.basename(t)
        if name in SKIP:
            print(f"SKIP  {name}  ({SKIP[name]})")
            skipped += 1
            continue
        try:
            r = subprocess.run(["bash", t], capture_output=True, text=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            failed.append((name, f"TIMEOUT after {args.timeout}s"))
            print(f"FAIL  {name}  (timeout)")
            continue
        if r.returncode == 0:
            passed += 1
            print(f"PASS  {name}")
        else:
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-5:])
            failed.append((name, tail))
            print(f"FAIL  {name}")

    print(f"\n{passed} passed, {len(failed)} failed, {skipped} skipped")
    for name, detail in failed:
        print(f"\n--- {name} ---\n{detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
