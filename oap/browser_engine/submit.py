"""Bounded first-party form submission runtime for certified OAP Engine forms."""
from __future__ import annotations

from urllib.parse import urlencode, urlsplit

MAX_FIELDS = 32
MAX_FIELD_NAME_BYTES = 256
MAX_FIELD_VALUE_BYTES = 4096
CERTIFIED_GET_ACTIONS = frozenset({"/search"})
SENSITIVE_NAMES = frozenset({
    "password",
    "passcode",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
})


def _byte_len(value: str) -> int:
    return len(value.encode("utf-8"))


def _safe_field_name(raw: object) -> str:
    name = str(raw or "").strip()
    if not name or _byte_len(name) > MAX_FIELD_NAME_BYTES:
        raise ValueError("invalid_form_field_name")
    if name.lower() in SENSITIVE_NAMES:
        raise ValueError("sensitive_form_field_not_allowed")
    return name


def _safe_field_value(raw: object) -> str:
    value = str(raw or "")
    if _byte_len(value) > MAX_FIELD_VALUE_BYTES:
        raise ValueError("form_field_value_too_large")
    return value


def build_certified_get_target(
    action: object,
    fields: object,
) -> str:
    """Build one certified same-origin GET target.

    The runtime deliberately accepts relative OAP paths only. Arbitrary origins,
    fragments, POST bodies and secret-bearing fields remain outside v1.
    """

    raw_action = str(action or "").strip()
    parsed = urlsplit(raw_action)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        raise ValueError("form_action_must_be_first_party_path")
    if parsed.path not in CERTIFIED_GET_ACTIONS:
        raise ValueError("unsupported_form_action")
    if parsed.query:
        raise ValueError("form_action_query_not_allowed")
    if not isinstance(fields, dict):
        raise TypeError("form_fields_must_be_object")
    if len(fields) > MAX_FIELDS:
        raise ValueError("form_field_limit")

    encoded: list[tuple[str, str]] = []
    for key, value in fields.items():
        encoded.append((_safe_field_name(key), _safe_field_value(value)))

    query = urlencode(encoded, doseq=False)
    return parsed.path + (f"?{query}" if query else "")
