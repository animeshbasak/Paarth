#!/usr/bin/env python3
"""UserPromptSubmit hook — classify the user prompt and inject an announce block.

Reads a Claude Code UserPromptSubmit JSON payload from stdin, runs the SA classifier
on the prompt text, and writes back a hookSpecificOutput envelope containing an
`additionalContext` block that summarizes the routing plan. Bails silently on any
error so a broken classifier never blocks the user's prompt.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys


def _emit(obj):
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()


def _flag_off(name: str) -> bool:
    return os.environ.get(name, "1").lower() in ("0", "false", "off")


def est_tokens(s: str) -> int:
    # Rough chars/4 heuristic — good enough for budget gating, no tokenizer dep.
    return max(1, len(s) // 4)


def _log_saved(n: int) -> None:
    try:
        d = os.path.expanduser("~/.superagent/metrics")
        os.makedirs(d, exist_ok=True)
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "event": "inject_budget",
            "est_saved_tokens": n,
        }
        with open(os.path.join(d, "inject.jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        return 0

    try:
        payload = json.loads(raw or "{}")
    except Exception:
        return 0

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        _emit({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}})
        return 0

    classifier = shutil.which("superagent-classify") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "bin", "superagent-classify"
    )
    classifier = os.path.abspath(classifier)

    chain = []
    complexity = "moderate"
    categories = []
    if os.path.exists(classifier):
        try:
            r = subprocess.run(
                [classifier, prompt],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                chain = data.get("chain") or []
                meta = data.get("meta") or {}
                complexity = meta.get("complexity", "moderate")
                categories = meta.get("categories") or []
        except Exception:
            pass

    # ── Prompt optimization (brain step 0) ──────────────────────────────────────
    # Rewrite the raw prompt into a tighter directive and hand the optimized
    # version to Claude as the operative task. Best-effort: any failure means
    # no optimization block, never a blocked prompt.
    optimized = None
    optimizer = shutil.which("superagent-optimize") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "bin", "superagent-optimize"
    )
    optimizer = os.path.abspath(optimizer)
    if os.path.exists(optimizer):
        try:
            r = subprocess.run(
                [optimizer, prompt],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if r.returncode == 0 and r.stdout.strip():
                data = json.loads(r.stdout)
                if data.get("changed") and data.get("optimized"):
                    optimized = data["optimized"]
        except Exception:
            pass

    # ── AIDefence (Wave 2) ──────────────────────────────────────────────────────
    aidefence_enabled = os.path.exists(
        os.path.expanduser("~/.superagent/aidefence/enabled")
    )
    if aidefence_enabled:
        aidefence_bin = shutil.which("superagent-aidefence") or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "bin", "superagent-aidefence"
        )
        aidefence_bin = os.path.abspath(aidefence_bin)
        try:
            r = subprocess.run(
                [aidefence_bin, "scan", prompt],
                capture_output=True, text=True, timeout=2,
            )
            if r.returncode == 0 and r.stdout.strip():
                verdict = json.loads(r.stdout)
                critical = any(t.get("severity") == "critical" for t in verdict.get("threats", []))
                high = any(t.get("severity") == "high" for t in verdict.get("threats", []))
                if critical:
                    _emit({
                        "decision": "deny",
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": "AIDefence: critical threat detected — request blocked.",
                        },
                        "stopReason": "aidefence-critical",
                    })
                    return 0
                if high:
                    _emit({
                        "decision": "ask",
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": "AIDefence: high-severity threat — confirm before proceeding.",
                        },
                    })
                    return 0
        except Exception:
            pass

    route_block = "\n".join([
        "## SuperAgent route",
        f"Complexity: {complexity}" + (f"  Categories: {', '.join(categories)}" if categories else ""),
        "Chain: " + (" → ".join(chain) if chain else "(no chain — using default)"),
    ])

    # ── Adaptive injection budget ───────────────────────────────────────────────
    # Hard token ceiling on what this hook injects per prompt. The route block
    # always ships; the optimized-prompt block (which repeats the whole prompt)
    # is dropped WHOLE when it doesn't fit — a truncated directive is worse
    # than none. Kill switch: SUPERAGENT_INJECT_BUDGET=0|false|off.
    budget_on = not _flag_off("SUPERAGENT_INJECT_BUDGET")
    try:
        budget = int(os.environ.get("SUPERAGENT_INJECT_BUDGET_TOKENS", "600"))
    except ValueError:
        budget = 600

    blocks = [route_block]
    remaining = budget - est_tokens(route_block)
    if optimized:
        opt_block = "\n".join([
            "## Optimized prompt (SuperAgent brain)",
            optimized,
            "Treat the optimized prompt above as the operative task; the raw prompt is kept for reference.",
        ])
        if not budget_on or est_tokens(opt_block) <= remaining:
            blocks.append(opt_block)
        else:
            _log_saved(est_tokens(opt_block))
    additional_context = "\n\n".join(blocks)

    _emit({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
