"""First-party Living Catalogue metadata normalization (no publishing authority).

This module validates optional discovery metadata. It does not change existing
rights, entitlement, streaming, or payment decisions.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

LANGUAGE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,3}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")
ISRC = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$")
FIELDS = frozenset({"genre", "language", "country", "isrc", "instruments"})
MAX_INSTRUMENTS = 12


def _label(value: object, *, max_length: int = 80) -> str:
    if not isinstance(value, str):
        raise TypeError("expected text")
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > max_length or any(ord(c) < 32 for c in cleaned):
        raise ValueError("invalid metadata label")
    return cleaned


def normalize_metadata(data: Mapping[str, object]) -> dict[str, object]:
    """Return canonical, bounded metadata; reject unknown fields and bad values.

    Geographic origin must only be published following a separate consent check.
    A valid ISRC is a format check, not proof of registration or ownership.
    """
    if not isinstance(data, Mapping):
        raise TypeError("metadata must be a mapping")
    unknown = set(data) - FIELDS
    if unknown:
        raise ValueError("unknown metadata fields")
    result: dict[str, object] = {}
    if "genre" in data:
        result["genre"] = _label(data["genre"])
    if "language" in data:
        language = _label(data["language"], max_length=35)
        if not LANGUAGE.fullmatch(language):
            raise ValueError("invalid language code")
        result["language"] = language.lower()
    if "country" in data:
        country = _label(data["country"], max_length=2)
        if not COUNTRY.fullmatch(country):
            raise ValueError("invalid country code")
        result["country"] = country
    if "isrc" in data:
        isrc = _label(data["isrc"], max_length=12)
        if not ISRC.fullmatch(isrc):
            raise ValueError("invalid ISRC format")
        result["isrc"] = isrc
    if "instruments" in data:
        instruments = data["instruments"]
        if not isinstance(instruments, (list, tuple)) or len(instruments) > MAX_INSTRUMENTS:
            raise ValueError("invalid instruments")
        labels = [_label(value) for value in instruments]
        if len({value.casefold() for value in labels}) != len(labels):
            raise ValueError("duplicate instruments")
        result["instruments"] = labels
    return result
