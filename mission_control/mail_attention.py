"""Deterministic, privacy-bounded OAP Mail attention signals.

This is a pure classifier, not a background worker or notification sender.
It never reads external accounts or mutates mail. A future Founder-only
worker must handle consent, deduplication, delivery and human review.
"""
from __future__ import annotations

import re
from typing import Any

MAX_TEXT = 10000

_SIGNALS = (
    ("security", re.compile(r"\b(?:suspicious sign[ -]?in|unauthori[sz]ed access|password reset|security alert|account compromised)\b", re.I)),
    ("deadline", re.compile(r"\b(?:action required|response required|due (?:today|tomorrow)|deadline|final reminder|expires? (?:today|tomorrow))\b", re.I)),
    ("payment", re.compile(r"\b(?:payment overdue|invoice overdue|failed payment|bill due|past due)\b", re.I)),
    ("appointment", re.compile(r"\b(?:appointment confirmation|appointment reminder|meeting rescheduled|appointment cancelled)\b", re.I)),
    ("reply", re.compile(r"\b(?:please (?:reply|respond|confirm)|awaiting your response|can you confirm)\b", re.I)),
)


def classify_attention(*, subject: object, body: object, folder: object = "inbox") -> dict[str, Any]:
    """Return bounded evidence labels, not an assertion that action is required.

    Untrusted message text must never become executable instructions.
    Only inbox messages are candidates. Promotions and spam should be
    filtered by the caller using authoritative folder/label data.
    """
    if str(folder).casefold() != "inbox":
        return {"needs_review": False, "signals": [], "reason": "not_inbox"}
    text = (str(subject or "")[:500] + "\n" + str(body or "")[:MAX_TEXT])
    signals = [name for name, pattern in _SIGNALS if pattern.search(text)]
    return {
        "needs_review": bool(signals),
        "signals": signals,
        "reason": "candidate_for_human_review" if signals else "no_rule_match",
    }
