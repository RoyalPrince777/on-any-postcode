"""Fail-closed property-advertising contract; not connected to public Market routes.

A property advertisement is not a product, an ownership title, a property sale,
or an invoice. No live publishing, payment, outbound contact or migration at import.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

CATEGORIES = frozenset({"house", "flat", "land", "commercial", "development", "luxury", "rental"})
CURRENCIES = frozenset({"GBP", "GHS"})
STATES = frozenset({"DRAFT", "APPROVED", "ACTIVE", "WITHDRAWN"})
MAX_MEDIA = 8


def _required(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError("invalid_" + field)
    return value.strip()


def _uuid(value: object, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_" + field) from exc


def _contact(url: object) -> str:
    address = _required(url, "advertiser_contact", 512)
    parts = urlsplit(address)
    if parts.scheme != "https" or not parts.netloc or parts.username or parts.password:
        raise ValueError("invalid_advertiser_contact")
    return address


def _money(value: object) -> str:
    try:
        number = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid_property_price") from exc
    if not number.is_finite() or number < 0 or number > Decimal("1000000000000"):
        raise ValueError("invalid_property_price")
    return str(number)


def property_draft(payload: dict[str, Any], *, publisher_id: object) -> dict[str, Any]:
    """Validate a property draft WITHOUT publishing it or claiming ownership."""
    category = _required(payload.get("category"), "category", 32).lower()
    if category not in CATEGORIES:
        raise ValueError("invalid_category")
    currency = _required(payload.get("currency"), "currency", 3).upper()
    if currency not in CURRENCIES:
        raise ValueError("unsupported_property_currency")
    media = payload.get("media", [])
    if not isinstance(media, list) or len(media) > MAX_MEDIA:
        raise ValueError("invalid_property_media")
    for item in media:
        if not isinstance(item, dict) or item.get("rights_confirmed") is not True:
            raise ValueError("property_media_rights_required")
        _required(item.get("asset_ref"), "media_asset_ref", 180)
    return {
        "publisher_id": _uuid(publisher_id, "publisher_id"),
        "advertiser_id": _uuid(payload.get("advertiser_id"), "advertiser_id"),
        "property_ref": _required(payload.get("property_ref"), "property_ref", 160),
        "title": _required(payload.get("title"), "title", 160),
        "description": _required(payload.get("description"), "description", 3000),
        "category": category,
        "country": _required(payload.get("country"), "country", 120),
        "locality": _required(payload.get("locality"), "locality", 160),
        "postcode": str(payload.get("postcode") or "").strip()[:32],
        "price": _money(payload.get("price")),
        "currency": currency,
        "advertiser_contact": _contact(payload.get("advertiser_contact")),
        "media": media,
        "state": "DRAFT",
        "authority_evidence_ref": None,
        "approval_receipt": None,
        "published_receipt": None,
        "withdrawn_receipt": None,
    }


def approve(record: dict[str, Any], *, evidence_ref: object, approved_by: object) -> dict[str, Any]:
    if record.get("state") != "DRAFT":
        raise ValueError("property_not_draft")
    return {
        **record, "state": "APPROVED",
        "authority_evidence_ref": _required(evidence_ref, "authority_evidence_ref", 180),
        "approval_receipt": {
            "approved_by": _uuid(approved_by, "approved_by"),
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }


def publish(record: dict[str, Any], *, actor_id: object, channel: object) -> dict[str, Any]:
    if record.get("state") != "APPROVED" or not record.get("authority_evidence_ref"):
        raise PermissionError("property_approval_required")
    if _uuid(actor_id, "actor_id") != record.get("publisher_id"):
        raise PermissionError("property_publisher_required")
    return {
        **record, "state": "ACTIVE",
        "published_receipt": {
            "actor_id": record["publisher_id"],
            "channel": _required(channel, "publication_channel", 512),
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }


def edit(record: dict[str, Any], changes: dict[str, Any], *, actor_id: object) -> dict[str, Any]:
    if _uuid(actor_id, "actor_id") != record.get("publisher_id"):
        raise PermissionError("property_publisher_required")
    if record.get("state") not in {"DRAFT", "APPROVED", "ACTIVE"}:
        raise ValueError("property_not_editable")
    immutable = {"publisher_id", "advertiser_id", "state", "authority_evidence_ref",
                 "approval_receipt", "published_receipt", "withdrawn_receipt"}
    if immutable.intersection(changes):
        raise PermissionError("property_guarded_field")
    allowed = {"property_ref", "title", "description", "category", "country",
               "locality", "postcode", "price", "currency", "advertiser_contact", "media"}
    if set(changes) - allowed:
        raise ValueError("invalid_property_change")
    candidate = property_draft({**record, **changes}, publisher_id=record["publisher_id"])
    # Material edits require new approval. Never keep a stale public approval.
    return {**candidate, "state": "DRAFT"}


def withdraw(record: dict[str, Any], *, actor_id: object, reason: object) -> dict[str, Any]:
    if _uuid(actor_id, "actor_id") != record.get("publisher_id"):
        raise PermissionError("property_publisher_required")
    if record.get("state") == "WITHDRAWN":
        return record
    return {
        **record, "state": "WITHDRAWN",
        "withdrawn_receipt": {
            "actor_id": record["publisher_id"],
            "reason": _required(reason, "withdrawal_reason", 240),
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }


def public_record(record: dict[str, Any]) -> dict[str, Any] | None:
    """Public property projection only; no private authority records or fee ledger."""
    if record.get("state") != "ACTIVE" or not record.get("published_receipt"):
        return None
    keys = ("property_ref", "title", "description", "category", "country",
            "locality", "postcode", "price", "currency", "advertiser_contact", "media")
    return {key: record[key] for key in keys}
