"""Bounded symbol and Unicode intelligence for the single SMI brain.

This module decodes caller-supplied Unicode scalars and separates technical
facts from claims that require external evidence.  It deliberately performs
no OCR, network lookup, supernatural judgement, autonomous publication or
Registry write.  The returned receipt is a deterministic, non-persisted
evidence envelope for a later authenticated Registry adapter.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable, Iterable
from hashlib import sha256
from typing import Any

MAX_SYMBOLS = 256
MAX_CLAIMS = 64
MAX_CLAIM_LENGTH = 2_000

_HEX_TOKEN = re.compile(r"^(?:U\+|0X)([0-9A-F]{1,6})$", re.IGNORECASE)
_DECIMAL_TOKEN = re.compile(r"^[0-9]{1,7}$")
_SUPERNATURAL_TERMS = (
    "demon",
    "demonic",
    "magic",
    "magical",
    "occult",
    "ritual",
    "sigil",
    "spell",
    "spirit",
    "summon",
    "summoning",
)
_CONTROL_TERMS = (
    "brainwash",
    "control you",
    "controls you",
    "hijack your attention",
    "mind control",
    "manipulate you",
)


class SymbolIntelligenceBlocked(ValueError):
    """Raised when the bounded scanner must fail closed."""


def _check_stop(stop_check: Callable[[], bool] | None) -> None:
    if stop_check is None or not callable(stop_check):
        raise SymbolIntelligenceBlocked("stop_check_required")
    try:
        stopped = stop_check()
    except Exception as exc:  # pragma: no cover - precise exception is untrusted
        raise SymbolIntelligenceBlocked("stop_check_unavailable") from exc
    if stopped is not False:
        raise SymbolIntelligenceBlocked("stopped")


def _as_codepoint(token: object) -> int:
    if isinstance(token, bool):
        raise SymbolIntelligenceBlocked("invalid_codepoint")
    if isinstance(token, int):
        value = token
    else:
        text = str(token).strip()
        match = _HEX_TOKEN.fullmatch(text)
        if match:
            value = int(match.group(1), 16)
        elif _DECIMAL_TOKEN.fullmatch(text):
            value = int(text, 10)
        elif len(text) == 1:
            value = ord(text)
        else:
            raise SymbolIntelligenceBlocked("invalid_codepoint")
    if value < 0 or value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
        raise SymbolIntelligenceBlocked("invalid_unicode_scalar")
    return value


def decode_symbol(token: object) -> dict[str, Any]:
    """Decode one Unicode scalar without assigning spiritual meaning."""

    value = _as_codepoint(token)
    character = chr(value)
    return {
        "input": str(token),
        "decimal": value,
        "codepoint": f"U+{value:04X}",
        "character": character,
        "unicode_name": unicodedata.name(character, "UNASSIGNED"),
        "unicode_category": unicodedata.category(character),
        "technical_fact": True,
        "spiritual_meaning_inferred": False,
    }


def classify_claim(claim: object) -> dict[str, Any]:
    """Classify evidential posture; never decide a belief or claim is fact."""

    text = str(claim).strip()
    if not text:
        raise SymbolIntelligenceBlocked("empty_claim")
    if len(text) > MAX_CLAIM_LENGTH:
        raise SymbolIntelligenceBlocked("claim_too_long")
    lowered = text.casefold()
    supernatural = tuple(term for term in _SUPERNATURAL_TERMS if term in lowered)
    control = tuple(term for term in _CONTROL_TERMS if term in lowered)
    evidence_required = bool(supernatural or control)
    return {
        "claim": text,
        "claim_sha256": sha256(text.encode("utf-8")).hexdigest(),
        "classification": (
            "EXTERNAL_EVIDENCE_REQUIRED" if evidence_required else "UNASSESSED"
        ),
        "supernatural_terms": supernatural,
        "attention_control_terms": control,
        "verified_fact": False,
        "automatic_publication_allowed": False,
        "human_review_required": evidence_required,
    }


def analyze(
    codepoints: Iterable[object],
    claims: Iterable[object] = (),
    *,
    stop_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    """Run a bounded analysis and return a tamper-evident local envelope."""

    _check_stop(stop_check)
    symbol_inputs = tuple(codepoints)
    claim_inputs = tuple(claims)
    if len(symbol_inputs) > MAX_SYMBOLS:
        raise SymbolIntelligenceBlocked("too_many_symbols")
    if len(claim_inputs) > MAX_CLAIMS:
        raise SymbolIntelligenceBlocked("too_many_claims")

    symbols = tuple(decode_symbol(item) for item in symbol_inputs)
    claim_results = tuple(classify_claim(item) for item in claim_inputs)
    _check_stop(stop_check)

    payload = {
        "schema": "oap.symbol-intelligence.receipt.v1",
        "scope": "caller_supplied_unicode_and_claims",
        "symbols": symbols,
        "claims": claim_results,
        "source_lookup_performed": False,
        "ocr_performed": False,
        "registry_write_performed": False,
        "receipt_persisted": False,
        "production_claim_allowed": False,
        "human_authority_final": True,
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return {
        **payload,
        "receipt_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
    }


def status() -> dict[str, Any]:
    """Expose exact capability boundaries without cosmetic Green."""

    return {
        "component": "SMI Symbol Intelligence",
        "unicode_decode_ready": True,
        "bounded_claim_triage_ready": True,
        "deterministic_local_receipt_ready": True,
        "image_ocr_ready": False,
        "video_transcription_ready": False,
        "authoritative_source_adapter_ready": False,
        "registry_persistence_ready": False,
        "runtime_wired": False,
        "production_ready": False,
        "human_authority_final": True,
    }
