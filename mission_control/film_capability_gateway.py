"""Three bounded first-party SMI capabilities inspired by the original film profiles.

These are real read-only application functions. The film characters themselves,
physical androids, hardware motherboard, independent agent brains, self-learning
models, physical sensing, and unrestricted autonomy are NOT implemented.

M3GAN: consent-scoped public OAP Direct booking discovery.
AMELIA: defensive action admission review, without taking action.
BLACK BOX: HMAC-authenticated software manifest with no external/device execution.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping
from typing import Any

from . import silicon_architecture, travel_marketplace, travel_supply_core

MOTHERBOARD_KEY_ENV = "OAP_SMI_MOTHERBOARD_HMAC_KEY"
MOTHERBOARD_SCHEMA = "oap.smi.motherboard.readonly.v1"
_ALLOWED_CAPABILITIES = frozenset({"inspect_public_evidence", "inspect_smi_status"})
_ALLOWED_AMELIA_ACTIONS = frozenset({
    "inspect_public_evidence",
    "inspect_booking_availability",
    "inspect_runtime_status",
    "review_security_receipt",
})
_DENIED_AMELIA_ACTIONS = frozenset({
    *silicon_architecture.BLOCKED_HARDWARE_AUTONOMY,
    "private_message_access",
    "secret_export",
    "camera_capture",
    "microphone_capture",
    "physical_actuation",
    "infiltration",
    "surveillance",
    "remote_code_execution",
    "self_modify",
})
_WORKLOAD_ID = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")
_SIGNATURE = re.compile(r"^[a-f0-9]{64}$")
_MOTHERBOARD_FIELDS = frozenset({
    "schema", "component", "workload_id", "capabilities", "network_access",
    "device_access", "writes_enabled",
})


def _bounded_text(value: object, *, name: str, limit: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"invalid_{name}")
    clean = " ".join(value.split())
    if not clean or len(clean) > limit:
        raise ValueError(f"invalid_{name}")
    return clean


def _envelope(component: str) -> dict[str, Any]:
    return {
        "component": component,
        "canonical_brain": "SMI",
        "creates_agent": False,
        "brain_count_added": 0,
        "operation_performed": False,
        "payment_performed": False,
        "human_authority_final": True,
    }


def m3gan_consented_booking(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Interpret a consented user query and read *actual* certified OAP offers."""

    if payload.get("consent") is not True:
        return {
            **_envelope("m3gan"),
            "state": "blocked",
            "reason": "explicit_consent_required",
            "data_read_performed": False,
        }
    query = _bounded_text(payload.get("request"), name="request", limit=240).casefold()
    matches = []
    if any(word in query for word in ("barber", "barbers", "haircut", "hair cut")):
        matches.append("barber")
    if any(word in query for word in ("event", "events", "concert", "ticket", "gig")):
        matches.append("event")
    if len(matches) != 1:
        return {
            **_envelope("m3gan"),
            "state": "needs_specific_category",
            "categories": ["barber", "event"],
            "data_read_performed": False,
        }
    category = matches[0]
    if category not in travel_supply_core.SUPPLY_CATEGORIES:
        return {
            **_envelope("m3gan"),
            "state": "not_ready",
            "category": category,
            "reason": "certified_category_not_installed",
            "data_read_performed": False,
        }
    try:
        stock = travel_marketplace.public_offers(category=category, limit=5)
    except (RuntimeError, ValueError):
        stock = {"ready": False, "offers": [], "error": "supply_unavailable"}
    if stock.get("ready") is not True:
        return {
            **_envelope("m3gan"),
            "state": "not_ready",
            "category": category,
            "reason": str(stock.get("error") or "supply_unavailable")[:100],
            "source": "oap_direct",
            "data_read_performed": True,
        }
    offers = []
    for item in list(stock.get("offers") or [])[:5]:
        if (item.get("category") != category or
            item.get("certified_supplier") is not True or
            item.get("observed_not_inferred") is not True or
            type(item.get("available_quantity")) is not int or
            item["available_quantity"] <= 0):
            continue
        offers.append({
            key: item.get(key) for key in (
                "listing_id", "title", "place_label", "starts_at", "ends_at",
                "available_quantity", "unit_price_minor", "currency",
                "supplier_name", "source", "observed_at",
            )
        })
    return {
        **_envelope("m3gan"),
        "state": "offers_found" if offers else "no_verified_offers",
        "category": category,
        "offers": offers,
        "count": len(offers),
        "source": "oap_direct",
        "data_read_performed": True,
        "booking_confirmed": False,
        "no_customer_message_stored": True,
    }


def amelia_defensive_review(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Review typed actions; never execute, infiltrate, elevate or self-approve."""

    action = _bounded_text(payload.get("action"), name="action", limit=72).casefold()
    source_verified = payload.get("source_verified") is True
    if action in _DENIED_AMELIA_ACTIONS:
        decision, reason = "hold", "consequential_or_disallowed_action"
    elif action not in _ALLOWED_AMELIA_ACTIONS:
        decision, reason = "hold", "unrecognised_action"
    elif not source_verified:
        decision, reason = "hold", "source_evidence_required"
    else:
        decision, reason = "review_only", "bounded_evidence_review_permitted"
    return {
        **_envelope("amelia"),
        "action": action,
        "decision": decision,
        "reason": reason,
        "action_executed": False,
        "adversarial_review_required": True,
        "guardian_required": True,
        "shere_khan_review_preserved": True,
        "bagheera_review_preserved": True,
    }


def _manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            dict(manifest), sort_keys=True, ensure_ascii=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError):
        raise ValueError("invalid_manifest") from None
    if len(encoded) > 2048:
        raise ValueError("manifest_too_large")
    return encoded


def verify_black_box_manifest(
    payload: Mapping[str, Any], *, secret: str | None = None
) -> dict[str, Any]:
    """Verify integrity and read-only *policy*, not hardware-backed isolation.

    Server-held HMAC key is never returned. A valid signature verifies that the
    canonical manifest was signed by someone with the secret; it does NOT prove
    secure boot, physical containment or that a workload has run.
    """

    report = {
        **_envelope("black_box"),
        "state": "blocked",
        "integrity_verified": False,
        "admitted_read_only": False,
        "network_used": False,
        "device_used": False,
        "writes_performed": False,
        "hardware_attestation": False,
        "physical_motherboard_built": False,
        "sandbox_process_started": False,
    }
    manifest = payload.get("manifest")
    signature = payload.get("signature")
    if not isinstance(manifest, dict) or not isinstance(signature, str):
        return {**report, "reason": "manifest_and_signature_required"}
    if set(manifest) != _MOTHERBOARD_FIELDS:
        return {**report, "reason": "manifest_schema_invalid"}
    if manifest.get("schema") != MOTHERBOARD_SCHEMA or manifest.get("component") != "black_box":
        return {**report, "reason": "manifest_schema_invalid"}
    workload = manifest.get("workload_id")
    if not isinstance(workload, str) or not _WORKLOAD_ID.fullmatch(workload):
        return {**report, "reason": "invalid_workload_id"}
    caps = manifest.get("capabilities")
    if (not isinstance(caps, list) or not caps or len(caps) > 2
        or any(not isinstance(c, str) for c in caps)
        or len(set(caps)) != len(caps)
        or not set(caps).issubset(_ALLOWED_CAPABILITIES)):
        return {**report, "reason": "capability_policy_denied"}
    if any(manifest.get(k) is not False for k in ("network_access", "device_access", "writes_enabled")):
        return {**report, "reason": "isolation_policy_denied"}
    if not _SIGNATURE.fullmatch(signature):
        return {**report, "reason": "invalid_signature"}
    key = secret if secret is not None else os.environ.get(MOTHERBOARD_KEY_ENV, "")
    if not isinstance(key, str) or len(key.encode("utf-8")) < 32:
        return {**report, "reason": "signing_key_unconfigured"}
    data = _manifest_bytes(manifest)
    mac = hmac.new(key.encode("utf-8"), data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, mac):
        return {**report, "reason": "invalid_signature"}
    return {
        **report,
        "state": "admitted_read_only",
        "integrity_verified": True,
        "admitted_read_only": True,
        "reason": "signed_read_only_manifest_policy_passed",
        "workload_id": workload,
        "manifest_sha256": hashlib.sha256(data).hexdigest(),
    }


def evaluate(profile: object, payload: object) -> dict[str, Any]:
    """Dispatch three actual bounded application functions; no model instances."""

    if not isinstance(payload, dict):
        raise TypeError("json_object_required")
    if profile == "m3gan":
        return m3gan_consented_booking(payload)
    if profile == "amelia":
        return amelia_defensive_review(payload)
    if profile == "black_box":
        return verify_black_box_manifest(payload)
    raise ValueError("unknown_original_three_profile")


def status() -> dict[str, Any]:
    return {
        "component": "SMI Original Three Bounded Capability Gateway",
        "implemented_profiles": ("m3gan", "amelia", "black_box"),
        "m3gan_runtime": "consent_scoped_first_party_offer_read",
        "amelia_runtime": "typed_defensive_review_no_execution",
        "black_box_runtime": "server_keyed_hmac_manifest_policy_check",
        "motherboard_key_configured": len(os.environ.get(MOTHERBOARD_KEY_ENV, "").encode()) >= 32,
        "network_isolation_enforced_at_os_level": False,
        "hardware_isolation_proven": False,
        "physical_motherboard_built": False,
        "robotics_perception_or_actuation_enabled": False,
        "autonomous_learning_enabled": False,
        "live_film_character_equivalence": False,
        "one_smi_brain": True,
        "creates_agents": False,
        "independent_execution_authority": False,
        "human_authority_final": True,
    }
