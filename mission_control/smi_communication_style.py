"""Bounded communication-style adaptation for governed SMI chat.

This module observes presentation preferences in approved, user-authored text.
It does not infer identity or protected traits, process microphone audio, or try
to impersonate the Human Authority.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

_WORD = re.compile(r"[A-Za-z0-9']+")
_EMOJI = re.compile(
    "[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\u2600-\u27BF]"
)
_LIST_LINE = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+")
_SOUTH_LONDON_TERMS = (
    "allow it",
    "bare",
    "blud",
    "bruv",
    "calm",
    "ends",
    "fam",
    "innit",
    "long",
    "mandem",
    "peak",
    "peng",
    "safe",
    "vex",
    "wagwan",
)


def _approved_user_text(history: Iterable[Mapping[str, object]]) -> list[str]:
    texts: list[str] = []
    for item in list(history)[-21:]:
        if str(item.get("role") or "") != "user":
            continue
        outcome = str(item.get("guardian_outcome") or "PASSED")
        if outcome != "PASSED":
            continue
        source = str(item.get("source") or "typed")
        if source != "typed":
            continue
        text = str(item.get("content") or "").strip()[:2000]
        if text:
            texts.append(text)
    return texts


def communication_style_guidance(
    history: Iterable[Mapping[str, object]] | None,
) -> str | None:
    """Return compact provider guidance from a meaningful approved sample."""

    texts = _approved_user_text(history or ())
    words = [word for text in texts for word in _WORD.findall(text)]
    if len(texts) < 3 or len(words) < 12:
        return None

    average_words = len(words) / len(texts)
    pace = "concise and direct" if average_words <= 10 else (
        "balanced in length" if average_words <= 24 else "detailed"
    )
    emoji_messages = sum(bool(_EMOJI.search(text)) for text in texts)
    list_messages = sum(bool(_LIST_LINE.search(text)) for text in texts)
    joined = " ".join(texts).casefold()
    observed_terms = [
        term
        for term in _SOUTH_LONDON_TERMS
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", joined)
    ][:5]

    preferences = [pace]
    if emoji_messages / len(texts) >= 0.25:
        preferences.append("comfortable with purposeful emoji signals")
    if list_messages / len(texts) >= 0.25:
        preferences.append("often uses scannable lists")
    if observed_terms:
        preferences.append(
            "observed vocabulary: " + ", ".join(observed_terms)
        )

    return (
        "Communication preference derived only from prior approved, user-authored "
        "typed chat: "
        + "; ".join(preferences)
        + ". Match clarity and cadence gently. Use observed vocabulary sparingly "
        "and only where natural. Never claim to be the user, infer identity or "
        "protected traits, invent dialect, or weaken Human Authority."
    )
