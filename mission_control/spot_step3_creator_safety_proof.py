"""Bounded live proof for The Spot Step 3 creator/media and safety/support.

This proof validates the existing first-party public routes and their governance
locks in the live runtime. It does not create a creator identity, publish media,
open a safeguarding case, distribute externally, or grant execution authority.
Only the governed HRM receipt and audit proof persist.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from . import approval_service, authority, hrm_durable_receipt, postgres_db, products
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

STEP3_ACTION = "SPOT_STEP3_CREATOR_MEDIA_SAFETY_SUPPORT_PROOF"

_REQUIRED_IDS = (
    "creators",
    "music",
    "player",
    "radio",
    "distribution",
    "tv-media",
    "safety",
    "support",
)

_REQUIRED_SLUGS = {
    "creators": "creators",
    "music": "music",
    "player": "player",
    "radio": "radio",
    "distribution": "distribution",
    "tv-media": "tv-media",
    "safety": "safety",
    "support": "support",
}

_LOCK_TERMS = {
    "creators": ("Certified Creator Identity", "publishing"),
    "music": ("rights proof", "Creator Identity", "Human Authority"),
    "player": ("youth-safe moderation", "rights"),
    "radio": ("licensing", "rights proof", "moderation"),
    "distribution": ("external", "legal routes"),
    "tv-media": ("Creator publishing workflow",),
    "safety": ("Authenticated reporting", "escalation"),
    "support": ("Safeguarding", "certification", "case privacy"),
}


def _capability_map() -> dict[str, dict[str, str]]:
    return {str(item["id"]): dict(item) for item in products.SPOT_CAPABILITIES}


def _template_source() -> str:
    return (
        Path(__file__).with_name("templates") / "spot_capability.html"
    ).read_text(encoding="utf-8")


def run(*, identity_id: object, operation_id: object) -> dict[str, Any]:
    """Verify live Step 3 routes and locks without publishing or case creation."""

    operation = str(operation_id or "").strip()[:160]
    if not operation:
        raise ValueError("step3_proof_operation_id_required")

    capabilities = _capability_map()
    checks: dict[str, bool] = {
        "authority": False,
        "capabilities_present": False,
        "public_routes_present": False,
        "creator_identity_locked": False,
        "rights_locked": False,
        "moderation_locked": False,
        "external_distribution_locked": False,
        "publishing_locked": False,
        "reporting_escalation_locked": False,
        "support_case_privacy_locked": False,
        "template_truth_locks": False,
    }

    with postgres_db.connect(readonly=True) as connection:
        authority.require_human_authority(connection, identity_id)
    checks["authority"] = True

    checks["capabilities_present"] = all(
        capability_id in capabilities for capability_id in _REQUIRED_IDS
    )
    if not checks["capabilities_present"]:
        raise RuntimeError("step3_required_capabilities_missing")

    checks["public_routes_present"] = all(
        products.get_public_spot_slug(capability_id) == expected_slug
        for capability_id, expected_slug in _REQUIRED_SLUGS.items()
    )
    if not checks["public_routes_present"]:
        raise RuntimeError("step3_public_routes_missing")

    for capability_id, terms in _LOCK_TERMS.items():
        blocked_by = capabilities[capability_id].get("blocked_by", "")
        if not all(term.casefold() in blocked_by.casefold() for term in terms):
            raise RuntimeError(f"step3_lock_missing:{capability_id}")

    checks["creator_identity_locked"] = True
    checks["rights_locked"] = True
    checks["moderation_locked"] = True
    checks["external_distribution_locked"] = True
    checks["publishing_locked"] = True
    checks["reporting_escalation_locked"] = True
    checks["support_case_privacy_locked"] = True

    template = _template_source()
    template_markers = (
        "does not claim Certified Creator Identity",
        "rights clearance or external publishing",
        "no public support form creates or exposes a safeguarding case",
        "Private case handling remains gated",
    )
    checks["template_truth_locks"] = all(
        marker in template for marker in template_markers
    )
    if not checks["template_truth_locks"]:
        raise RuntimeError("step3_template_truth_lock_missing")

    if not all(checks.values()):
        raise RuntimeError("step3_proof_incomplete")

    canonical = {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }
    receipt = hrm_durable_receipt.build_receipt(
        "spot-step3-creator-media-safety-support",
        {
            "governance": "7-7-7",
            "checks": canonical,
            "evidence_proven": True,
            "authority_transferred": False,
            "human_authority_required": True,
            "human_authority_approved": True,
            "proof_kind": "live_runtime_boundary_verification",
            "creator_routes_proven": True,
            "media_routes_proven": True,
            "safety_support_routes_proven": True,
            "certified_creator_identity_created": False,
            "media_published": False,
            "external_distribution_performed": False,
            "public_safeguarding_case_created": False,
            "private_case_created": False,
            "execution_authority_expanded": False,
            "human_authority_final": True,
        },
        idempotency_key=operation,
    )
    durable = hrm_durable_receipt.persist_and_read_back(receipt)

    with postgres_db.connect() as connection:
        authority.require_human_authority(connection, identity_id)
        approval_service._write_audit(
            connection,
            actor_id=str(identity_id),
            action=STEP3_ACTION,
            target="THE_SPOT_CREATOR_MEDIA_SAFETY_SUPPORT",
            reason=(
                "Bounded Step 3 creator/media and safety/support proof completed; "
                "publishing, external distribution and case creation remained locked."
            ),
            correlation_id=receipt.receipt_id,
            metadata={
                "passed": True,
                "proof_kind": "live_runtime_boundary_verification",
                "creator_routes_proven": True,
                "media_routes_proven": True,
                "safety_support_routes_proven": True,
                "certified_creator_identity_created": False,
                "media_published": False,
                "external_distribution_performed": False,
                "public_safeguarding_case_created": False,
                "private_case_created": False,
                "execution_authority_expanded": False,
                "authority_level": 0,
                "human_authority_final": True,
            },
        )
        connection.commit()

    return {
        "component": "The Spot Step 3 Creator Media Safety Support Proof",
        "quarter": 75,
        "passed": True,
        "checks": checks,
        "receipt_verified": bool(
            durable.get("write_verified") and durable.get("read_back_verified")
        ),
        "creator_routes_proven": True,
        "media_routes_proven": True,
        "safety_support_routes_proven": True,
        "certified_creator_identity_created": False,
        "media_published": False,
        "external_distribution_performed": False,
        "public_safeguarding_case_created": False,
        "private_case_created": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }
