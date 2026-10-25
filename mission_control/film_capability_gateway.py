"""Three bounded first-party SMI capabilities inspired by the original film profiles.

These are real read-only application functions. The film characters themselves,
physical androids, hardware motherboard, independent agent brains, self-learning
models, physical sensing, and unrestricted autonomy are NOT implemented.

M3GAN: consent-scoped, source-linked search of her original film abilities.
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

from . import silicon_architecture, smi_archive

MOTHERBOARD_KEY_ENV = "OAP_SMI_MOTHERBOARD_HMAC_KEY"
MOTHERBOARD_SCHEMA = "oap.smi.motherboard.readonly.v1"
_ALLOWED_CAPABILITIES = frozenset({"inspect_public_evidence", "inspect_smi_status"})
_ALLOWED_AMELIA_ACTIONS = frozenset({
    "inspect_public_evidence",
    "inspect_film_evidence",
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


_M3GAN_NOISE = frozenset({
    "a", "about", "abilities", "ability", "and", "are", "can", "could",
    "does", "do", "explain", "for", "how", "i", "in", "is", "me",
    "m3gan", "my", "of", "please", "show", "tell", "the", "to",
    "what", "which", "with", "you", "your",
})
_M3GAN_GENERAL = frozenset({
    "abilities", "ability", "everything", "overview", "profile", "powers",
    "skills", "all", "full", "original",
})


def m3gan_consented_research(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Query *only M3GAN's* original source-backed film abilities.

    Searches the already published, immutable film-canon snapshot. Never calls a
    vendor, booking system, sensor, model or external source. Previous context
    may be supplied by the caller but is not saved to HRM or application memory.
    """

    if payload.get("consent") is not True:
        return {
            **_envelope("m3gan"),
            "state": "blocked",
            "reason": "explicit_consent_required",
            "source_access_performed": False,
        }
    query = _bounded_text(payload.get("question"), name="question", limit=240)
    history = payload.get("context", [])
    if (not isinstance(history, list) or len(history) > 3
        or any(not isinstance(item, str) for item in history)):
        raise ValueError("invalid_context")
    history_text = " ".join(
        _bounded_text(item, name="context", limit=120) for item in history
    )
    words = set(re.findall(r"[a-z0-9]+", (query + " " + history_text).casefold()))
    meaningful = words - _M3GAN_NOISE
    general = bool(words & _M3GAN_GENERAL) and not meaningful
    entries = smi_archive.FILM_CANON_ABILITIES
    sources = {item["source_id"]: item for item in smi_archive.FILM_RESEARCH_SOURCE_RECEIPTS}
    ranked: list[tuple[int, dict[str, Any]]] = []
    for entry in entries:
        if entry["reference_key"] != "m3gan":
            continue
        tags = set(re.findall(
            r"[a-z0-9]+",
            str(entry["name"]) + " " + str(entry["ability_id"]).replace("_", " ")
            + " " + str(entry["film_evidence"]),
        ))
        score = len(meaningful & tags)
        if general or not meaningful:
            score = 1
        if score < 1:
            continue
        source = sources.get(entry["source_id"])
        if source is None:
            continue
        ranked.append((score, {
            "ability_id": entry["ability_id"],
            "name": entry["name"],
            "film_evidence": entry["film_evidence"],
            "evidence_scope": entry["evidence_scope"],
            "source_id": entry["source_id"],
            "source_url": source["url"],
            "publisher": source["publisher"],
        }))
    ranked.sort(key=lambda item: (-item[0], item[1]["ability_id"]))
    matches = [item for _, item in ranked[:6]]
    return {
        **_envelope("m3gan"),
        "state": "source_backed_matches" if matches else "no_verified_match",
        "matches": matches,
        "match_count": len(matches),
        "source": "oap_founder_private_film_canon_snapshot",
        "source_access_performed": True,
        "lookup_type": "deterministic_source_search_not_model_inference",
        "question_stored": False,
        "context_stored": False,
        "external_fetch_performed": False,
        "autonomous_learning_performed": False,
        "physical_action_performed": False,
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
        return m3gan_consented_research(payload)
    if profile == "amelia":
        return amelia_defensive_review(payload)
    if profile == "black_box":
        return verify_black_box_manifest(payload)
    raise ValueError("unknown_original_three_profile")


def status() -> dict[str, Any]:
    return {
        "component": "SMI Original Three Bounded Capability Gateway",
        "implemented_profiles": ("m3gan", "amelia", "black_box"),
        "m3gan_runtime": "consent_scoped_source_backed_film_canon_lookup",
        "amelia_runtime": "typed_defensive_review_no_execution",
        "black_box_runtime": "server_keyed_hmac_manifest_policy_check",
        "other_business_missions_in_scope": False,
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
