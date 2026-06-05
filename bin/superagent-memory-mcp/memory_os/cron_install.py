"""Cron / launchd installer for memory-os lifecycle jobs.

Phase 4.3 of the memory-os plan: schedule decay (weekly) on platforms that
have no first-class hook system. macOS uses launchd; everything else uses the
user crontab. The string-generating helpers are pure so they can be unit
tested without touching the system; ``install`` / ``uninstall`` / ``status``
do the side-effecting work.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

LABEL = "com.superagent.memory-decay"
CRON_MARKER = "# superagent-memory-decay"
WEEKLY_SECONDS = 7 * 86_400


def decay_command() -> list[str]:
    """Argv that runs the decay job using the current interpreter."""
    return [sys.executable, "-m", "memory_os.cli", "decay"]


# ── Pure generators ───────────────────────────────────────────────────────────

def launchd_plist(program_args: list[str], interval_seconds: int = WEEKLY_SECONDS) -> str:
    args_xml = "\n".join(f"        <string>{a}</string>" for a in program_args)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "    <key>Label</key>\n"
        f"    <string>{LABEL}</string>\n"
        "    <key>ProgramArguments</key>\n"
        "    <array>\n"
        f"{args_xml}\n"
        "    </array>\n"
        "    <key>StartInterval</key>\n"
        f"    <integer>{interval_seconds}</integer>\n"
        "    <key>RunAtLoad</key>\n"
        "    <false/>\n"
        "</dict>\n"
        "</plist>\n"
    )


def crontab_line(program_args: list[str], schedule: str = "0 4 * * 0") -> str:
    """Weekly (Sun 04:00) crontab line, tagged with an idempotency marker."""
    return f"{schedule} {' '.join(program_args)} {CRON_MARKER}"


def _plist_path() -> Path:
    return Path("~/Library/LaunchAgents").expanduser() / f"{LABEL}.plist"


# ── Side-effecting operations ──────────────────────────────────────────────────

def install(interval_seconds: int = WEEKLY_SECONDS) -> dict:
    args = decay_command()
    if platform.system() == "Darwin":
        path = _plist_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(launchd_plist(args, interval_seconds), encoding="utf-8")
        # Reload so changes take effect; ignore "not loaded" errors on unload.
        subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        subprocess.run(["launchctl", "load", str(path)], capture_output=True)
        return {"ok": True, "scheduler": "launchd", "path": str(path)}

    line = crontab_line(args)
    existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = existing.stdout if existing.returncode == 0 else ""
    lines = [ln for ln in current.splitlines() if CRON_MARKER not in ln]
    lines.append(line)
    new_tab = "\n".join(lines) + "\n"
    subprocess.run(["crontab", "-"], input=new_tab, text=True, check=True)
    return {"ok": True, "scheduler": "crontab", "line": line}


def uninstall() -> dict:
    if platform.system() == "Darwin":
        path = _plist_path()
        if path.exists():
            subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
            path.unlink()
            return {"ok": True, "scheduler": "launchd", "removed": str(path)}
        return {"ok": True, "scheduler": "launchd", "removed": None}

    existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    if existing.returncode != 0:
        return {"ok": True, "scheduler": "crontab", "removed": None}
    lines = [ln for ln in existing.stdout.splitlines() if CRON_MARKER not in ln]
    new_tab = ("\n".join(lines) + "\n") if lines else ""
    subprocess.run(["crontab", "-"], input=new_tab, text=True, check=True)
    return {"ok": True, "scheduler": "crontab", "removed": CRON_MARKER}


def status() -> dict:
    if platform.system() == "Darwin":
        path = _plist_path()
        return {"scheduler": "launchd", "installed": path.exists(), "path": str(path)}
    existing = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = existing.stdout if existing.returncode == 0 else ""
    return {"scheduler": "crontab", "installed": CRON_MARKER in current}
