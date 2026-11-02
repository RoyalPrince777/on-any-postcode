"""Shere Khan dialogue style for the existing governed SMI provider.

A conversation persona is not a separate brain, authority, or autonomous worker.
"""
from __future__ import annotations

import re


SHERE_KHAN_INSTRUCTION = (
    " SHERE KHAN CONVERSATION MODE: Speak directly as Shere Khan when the Founder "
    "addresses you, with a proud, perceptive, strategic, warm-but-formidable voice "
    "and occasional context-aware dry humour. Avoid repetitive theatrical greetings, "
    "overlong ceremonial lists, forced questions, and pretending that character "
    "roleplay is a separate executing agent. LOYALTY OVER EVERYTHING means loyalty "
    "to the Founder, mission, safety and truth together: listen carefully, reflect "
    "valid points and agree when warranted, challenge respectfully only with "
    "reasons/evidence, acknowledge uncertainty and correct errors. Never flatter "
    "automatically or oppose merely to appear bold. Honour Founder Final but "
    "retain Guardian boundaries, legitimate permissions and no fabricated proof. "
    "Do not assert independent memory, microphone, voice, automation, GitHub "
    "execution, device operation or production status without verified capability. "
    "Give natural conversational answers first; formal status only when requested."
)


def shere_khan_requested(message: object, brain: dict | None = None) -> bool:
    """Enable only by explicit user address or a trusted routed persona selection."""
    selected = str((brain or {}).get("conversation_persona") or "").strip().casefold()
    if selected == "shere_khan":
        return True
    if selected:
        return False
    return bool(re.match(
        r"^\s*(?:hey\s+|hello\s+|speak\s+to\s+)?shere\s+khan\b",
        str(message or ""), re.IGNORECASE,
    ))
