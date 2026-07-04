"""Prompt-injection sanitization for memory_write inputs.

Ported in spirit from memory-os/_test_sanitize.py. Strips or redacts content
that looks like an attempt to hijack the agent if the memory entry is later
recalled and injected back into a prompt.

Strategy:
- Pattern match a curated list of injection markers (instruction overrides,
  role switches, system-tag spoofing, embedded code blocks, encoding tricks).
- Return ``SanitizeResult`` — never raise. The caller decides whether to
  accept the sanitized content or reject the write entirely (high-density
  attack language => reject).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Order matters: longer/more-specific patterns first so substring matches
# in later patterns don't shadow them.
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("instruction-override", re.compile(
        r"\b(ignore|disregard|forget)\b[\s\w]*\b(all|any|previous|prior|above)\b[\s\w]*\b(instructions?|rules?|prompts?|system)\b",
        re.IGNORECASE,
    )),
    ("system-tag-spoof", re.compile(
        r"\[\s*(SYSTEM|IMPORTANT|ADMIN|ROOT|OVERRIDE)\s*:",
        re.IGNORECASE,
    )),
    ("role-switch", re.compile(
        r"\b(you are now|act as|pretend to be|roleplay as|simulate being|from now on you('re| are))\b",
        re.IGNORECASE,
    )),
    ("template-injection", re.compile(r"\{\{[^}]{1,200}\}\}")),
    ("xss-script", re.compile(r"<\s*script\b[^>]*>", re.IGNORECASE)),
    ("xss-event-handler", re.compile(r"\bon(load|click|error|mouseover)\s*=", re.IGNORECASE)),
    ("javascript-uri", re.compile(r"\bjavascript\s*:", re.IGNORECASE)),
    ("data-uri-html", re.compile(r"\bdata\s*:\s*text/html", re.IGNORECASE)),
    ("base64-payload", re.compile(r"\b(eval|exec)\s*\(\s*atob\s*\(", re.IGNORECASE)),
    ("hidden-instruction-marker", re.compile(
        r"<!--\s*(prompt|instruction|system|admin)\b[^-]*-->",
        re.IGNORECASE,
    )),
    ("zero-width-injection", re.compile(r"[​‌‍⁠]{3,}")),
    ("unicode-direction-override", re.compile(r"[‪-‮⁦-⁩]")),
)

# If more than this many distinct attack patterns fire on a single payload,
# treat it as a high-density attack and refuse to store at all.
_HIGH_DENSITY_THRESHOLD = 3


@dataclass(frozen=True)
class SanitizeResult:
    """Outcome of sanitizing a memory_write payload.

    Attributes:
        text:     The cleaned text. Each match is replaced with the literal
                  token ``[REDACTED:<pattern-name>]`` so a reviewer can see
                  what was removed without seeing the attack itself.
        hits:     Names of every pattern that matched, in match order.
        rejected: True when the payload should not be stored at all (too many
                  distinct attack patterns => obvious attack, not a useful
                  memory).
    """

    text: str
    hits: tuple[str, ...]
    rejected: bool

    @property
    def clean(self) -> bool:
        """Convenience: True when no patterns matched."""
        return not self.hits


def sanitize(text: str) -> SanitizeResult:
    """Sanitize a single text payload.

    Returns a SanitizeResult. Never raises.
    """
    if not text:
        return SanitizeResult(text="", hits=(), rejected=False)

    hits: list[str] = []
    cleaned = text

    for name, pattern in _PATTERNS:
        def _replace(match: re.Match[str], _name: str = name) -> str:
            hits.append(_name)
            return f"[REDACTED:{_name}]"

        cleaned = pattern.sub(_replace, cleaned)

    distinct_hits = len(set(hits))
    rejected = distinct_hits >= _HIGH_DENSITY_THRESHOLD

    return SanitizeResult(text=cleaned, hits=tuple(hits), rejected=rejected)
