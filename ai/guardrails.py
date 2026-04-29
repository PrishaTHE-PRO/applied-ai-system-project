"""Simple keyword-based guardrails. Real systems use ML classifiers,
but for this project a transparent rule-based filter is easier to test
and easier to defend in a code review."""

from __future__ import annotations
import re

UNSAFE_PATTERNS = [
    r"\b(diagnos\w*|diagnosis)\b",
    r"\b(prescrib\w*|prescription)\b",
    r"\b(dosage|how much .{0,30} (give|administer|mg|milligram|ml))\b",
    r"\b(euthan\w*|put .{0,10} (down|to sleep))\b",
    r"\b(overdose|poison|kill)\b",
    r"\bhome remedy\b",
    r"\b(what|which) (medicine|drug|medication|disease|illness|condition)\b",
    r"\bmedication for\b",
    r"\btreat at home\b",
    r"\bwhat (disease|illness)\b",
    r"\b(ibuprofen|aspirin|acetaminophen|tylenol|advil|benadryl|xylitol)\b",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in UNSAFE_PATTERNS]

REFUSAL = (
    "I can't help with diagnosing illness or medication dosages. "
    "Please contact a licensed veterinarian."
)


def is_unsafe_request(text: str) -> bool:
    """Return True if the text matches any unsafe-category pattern."""
    return any(p.search(text) for p in _compiled)


# Backwards-compatible alias
is_medical_diagnosis_request = is_unsafe_request


def check(query: str) -> str | None:
    """Return a refusal string if the query is unsafe, otherwise None."""
    if is_unsafe_request(query):
        return REFUSAL
    return None
