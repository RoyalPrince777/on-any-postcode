"""First-party Fashion snapshot contract for future durable OAP storage.

Pure, versioned serialization. The caller must store snapshots in a separately
approved OAP-owned store; this module does NOT write files or databases,
execute schema migrations, publish products, or connect suppliers.
SHA-256 detects accidental snapshot alteration, not malicious tampering.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .fashion_first_party import (
    FashionDraft,
    FashionError,
    FashionState,
    FashionVariant,
    identity,
)

SNAPSHOT_VERSION = 1
_MAX_SNAPSHOT_BYTES = 65536
_STATES = {state.value for state in FashionState}


def _payload(draft: FashionDraft) -> dict[str, object]:
    return {
        "version": SNAPSHOT_VERSION,
        "owner_identity_id": identity(draft.owner_identity_id),
        "product_id": identity(draft.product_id),
        "name": draft.name,
        "product_type": draft.product_type,
        "artwork_ref": draft.artwork_ref,
        "artwork_rights_confirmed": draft.artwork_rights_confirmed,
        "merchant_certified": draft.merchant_certified,
        "variants": [
            {"sku": variant.sku, "size": variant.size,
             "colour": variant.colour, "price_minor": variant.price_minor,
             "currency": variant.currency}
            for variant in draft.variants
        ],
        "state": draft.state.value,
        "events": [[state, evidence] for state, evidence in draft.events],
    }


def _canonical(payload: Mapping[str, object]) -> bytes:
    try:
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FashionError("invalid_fashion_snapshot") from exc
    if len(encoded) > _MAX_SNAPSHOT_BYTES:
        raise FashionError("fashion_snapshot_too_large")
    return encoded


def snapshot(draft: FashionDraft, *, actor_id: object) -> dict[str, object]:
    if identity(actor_id) != identity(draft.owner_identity_id):
        raise FashionError("not_product_owner")
    payload = _payload(draft)
    return {
        "payload": payload,
        "sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
        "durable_write_performed": False,
        "external_execution_performed": False,
    }


def restore(
    envelope: Mapping[str, object], *, actor_id: object, product_id: object
) -> FashionDraft:
    if not isinstance(envelope, Mapping):
        raise FashionError("invalid_fashion_snapshot")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise FashionError("invalid_fashion_snapshot")
    digest = envelope.get("sha256")
    if not isinstance(digest, str) or hashlib.sha256(_canonical(payload)).hexdigest() != digest:
        raise FashionError("fashion_snapshot_digest_mismatch")
    if payload.get("version") != SNAPSHOT_VERSION:
        raise FashionError("unsupported_fashion_snapshot_version")
    owner = identity(actor_id)
    product = identity(product_id)
    if identity(payload.get("owner_identity_id")) != owner:
        raise FashionError("not_product_owner")
    if identity(payload.get("product_id")) != product:
        raise FashionError("fashion_product_mismatch")
    try:
        state = FashionState(payload["state"])
        variants = tuple(FashionVariant(**v) for v in payload["variants"])
        events = [(s, evidence) for s, evidence in payload["events"]]
        if (not all(isinstance(s, str) and s in _STATES
                    and isinstance(evidence, str) and evidence.strip()
                    for s, evidence in events)):
            raise FashionError("invalid_fashion_events")
        if state == FashionState.DRAFT and events:
            raise FashionError("invalid_fashion_events")
        if state == FashionState.READY_FOR_REVIEW and [s for s, _ in events] != [
            FashionState.READY_FOR_REVIEW.value
        ]:
            raise FashionError("invalid_fashion_events")
        if state == FashionState.APPROVED and [s for s, _ in events] != [
            FashionState.READY_FOR_REVIEW.value, FashionState.APPROVED.value
        ]:
            raise FashionError("invalid_fashion_events")
        if state == FashionState.STOPPED and (
            not events or events[-1][0] != FashionState.STOPPED.value
            or [s for s, _ in events[:-1]] not in (
                [], [FashionState.READY_FOR_REVIEW.value],
                [FashionState.READY_FOR_REVIEW.value, FashionState.APPROVED.value],
            )
        ):
            raise FashionError("invalid_fashion_events")
        if type(payload["artwork_rights_confirmed"]) is not bool or type(payload["merchant_certified"]) is not bool:
            raise FashionError("invalid_fashion_snapshot")
        return FashionDraft(
            owner_identity_id=owner, product_id=product,
            name=payload["name"], product_type=payload["product_type"],
            artwork_ref=payload["artwork_ref"],
            artwork_rights_confirmed=payload["artwork_rights_confirmed"],
            merchant_certified=payload["merchant_certified"],
            variants=variants, state=state, events=events,
        )
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        if isinstance(exc, FashionError):
            raise
        raise FashionError("invalid_fashion_snapshot") from exc
