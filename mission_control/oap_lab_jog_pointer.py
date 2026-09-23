"""OAP LAB review-only pointer for existing Organiser and graph consumers.

No route, persistence, graph mutation, auto memory ingestion or HRM approval.
The existing authenticated owner and durable stores remain the authorities.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked


def _uuid(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("canonical_owner_or_mission_id_required") from exc


def research_jog_pointer(
    handoff: Mapping[str, object],
    *,
    authenticated_owner_id: str,
    stored_owner_id: str,
    stored_mission_id: str,
    stored_notebook_id: str,
    stopped: bool = False,
) -> dict[str, object]:
    """Project a verified handoff as a minimal reference, not memory content.

    The caller must fetch the handoff and owner record from the existing
    owner-scoped store; this pure function cannot authenticate a caller or
    establish whether persistence occurred.
    """
    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    if not isinstance(handoff, Mapping):
        raise ClaimEdgeBlocked("verified_handoff_required")
    owner = _uuid(authenticated_owner_id)
    if owner != _uuid(stored_owner_id):
        raise ClaimEdgeBlocked("owner_scope_mismatch")
    mission = _uuid(stored_mission_id)
    if handoff.get("mission_id") != mission:
        raise ClaimEdgeBlocked("mission_scope_mismatch")
    if (not isinstance(stored_notebook_id, str)
            or not stored_notebook_id.strip()
            or handoff.get("notebook_id") != stored_notebook_id):
        raise ClaimEdgeBlocked("notebook_scope_mismatch")
    for key in ("claim_id", "claim_receipt_sha256", "review_receipt_sha256"):
        value = handoff.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ClaimEdgeBlocked("incomplete_handoff")
        if key.endswith("sha256") and (
            len(value) != 64 or any(char not in "0123456789abcdef" for char in value)
        ):
            raise ClaimEdgeBlocked("invalid_receipt_hash")
    if _uuid(handoff["claim_id"]) != handoff["claim_id"]:
        raise ClaimEdgeBlocked("claim_id_not_canonical")
    if handoff.get("handoff") != "read_only_research_review":
        raise ClaimEdgeBlocked("unverified_handoff_state")
    if handoff.get("jog_memory_pointer_only") is not True:
        raise ClaimEdgeBlocked("pointer_only_required")
    if any(handoff.get(key) is not False for key in (
        "durable_storage_verified", "independent_origin_verified",
        "scientific_truth_established", "canonical_promotion_authorised",
        "publication_authorised", "execution_authorised",
    )):
        raise ClaimEdgeBlocked("unverified_capability_escalation")
    return {
        "kind": "OAP_LAB_RESEARCH_POINTER",
        "owner_id": owner,
        "mission_id": mission,
        "notebook_id": stored_notebook_id,
        "claim_id": handoff["claim_id"],
        "claim_receipt_sha256": handoff["claim_receipt_sha256"],
        "review_receipt_sha256": handoff["review_receipt_sha256"],
        "visibility": "owner_private",
        "graph_mode": "reference_only_no_graph_write",
        "organiser_mode": "read_only_resume_pointer",
        "hrm_mode": "no_authority_receipt",
        "raw_sources_retained": False,
        "claim_text_retained": False,
        "publication_authorised": False,
        "execution_authorised": False,
        "durable_storage_verified": False,
        "scientific_truth_established": False,
    }
