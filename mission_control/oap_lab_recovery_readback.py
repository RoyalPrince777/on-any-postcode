"""Read-only LAB recovery read-back verifier for existing governed stores.

The existing storage owner provides immutable records and an independently
retained anchor. This module performs no I/O, creates no table, and cannot
claim durable persistence, source independence, or scientific truth.
"""
from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from mission_control.oap_lab_claim_edge import ClaimEdgeBlocked
from mission_control.oap_lab_evidence_review import verify_recovery_chain


def verify_lab_readback(
    records: tuple[Mapping[str, object], ...],
    *,
    expected_last_hash: str,
    authenticated_owner_id: str,
    stored_owner_id: str,
    stored_claim_id: str,
    anchor_owner_id: str,
    anchor_claim_id: str,
    anchor_retained_separately: bool,
    stopped: bool = False,
) -> dict[str, object]:
    """Read-back equality and scope; NOT a durable-store attestation."""
    if type(stopped) is not bool:
        raise ClaimEdgeBlocked("explicit_stop_state_required")
    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    try:
        owner = str(UUID(authenticated_owner_id))
        claim = str(UUID(stored_claim_id))
        if owner != str(UUID(stored_owner_id)) or owner != str(UUID(anchor_owner_id)):
            raise ClaimEdgeBlocked("recovery_owner_mismatch")
        if claim != str(UUID(anchor_claim_id)):
            raise ClaimEdgeBlocked("recovery_claim_mismatch")
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("recovery_identity_invalid") from exc
    if anchor_retained_separately is not True:
        raise ClaimEdgeBlocked("independent_recovery_anchor_required")
    if not isinstance(expected_last_hash, str) or (
        len(expected_last_hash) != 64
        or any(c not in "0123456789abcdef" for c in expected_last_hash)
    ):
        raise ClaimEdgeBlocked("valid_anchor_hash_required")
    if not isinstance(records, tuple) or not records:
        raise ClaimEdgeBlocked("recovery_records_required")
    for record in records:
        if not isinstance(record, Mapping):
            raise ClaimEdgeBlocked("invalid_recovery_record")
        state = record.get("state")
        if not isinstance(state, Mapping):
            raise ClaimEdgeBlocked("recovery_state_required")
        if state.get("owner_id") != owner or state.get("claim_id") != claim:
            raise ClaimEdgeBlocked("recovery_record_scope_mismatch")
        if any(state.get(key) is not False for key in (
            "scientific_truth_established", "canonical_promotion_authorised",
            "publication_authorised", "execution_authorised",
        )) or any(key in state and state[key] is not False for key in (
            "storage_authenticity_verified", "independent_anchor_authenticity_verified",
            "durable_persistence_verified", "external_store_readback_verified",
            "namespace_independence_authenticated", "anchor_authenticity_verified",
            "independent_recovery_verified", "release_ready",
        )) or ("resume_mode" in state and state["resume_mode"] != "review_only"):
            raise ClaimEdgeBlocked("recovery_cannot_restore_authority")
    outcome = verify_recovery_chain(records, expected_last_hash=expected_last_hash)
    return {
        "owner_id": owner,
        "claim_id": claim,
        "history_integrity_verified": outcome["history_integrity_verified"],
        "readback_matches_supplied_anchor": True,
        "version_count": outcome["version_count"],
        "resume_mode": "review_only",
        "storage_authenticity_verified": False,
        "independent_anchor_authenticity_verified": False,
        "durable_persistence_verified": False,
        "independent_recovery_verified": False,
        "release_ready": False,
        "scientific_truth_established": False,
        "publication_authorised": False,
        "execution_authorised": False,
    }


def verify_separate_readback_snapshots(
    history_snapshot: Mapping[str, object],
    anchor_snapshot: Mapping[str, object],
    *,
    authenticated_owner_id: str,
    stopped: bool = False,
) -> dict[str, object]:
    """Check two supplied read snapshots, without claiming store authenticity.

    Namespace separation and retrieval evidence are caller-supplied metadata,
    not a substitute for independent, authenticated real-store read-back.
    """
    if type(stopped) is not bool:
        raise ClaimEdgeBlocked("explicit_stop_state_required")
    if stopped:
        raise ClaimEdgeBlocked("stop_asserted")
    if not isinstance(history_snapshot, Mapping) or not isinstance(anchor_snapshot, Mapping):
        raise ClaimEdgeBlocked("two_readback_snapshots_required")
    owner = _uuid_for_snapshot(authenticated_owner_id)
    for item in (history_snapshot, anchor_snapshot):
        if item.get("owner_id") != owner:
            raise ClaimEdgeBlocked("snapshot_owner_mismatch")
        if not isinstance(item.get("retrieval_id"), str) or not item["retrieval_id"].strip():
            raise ClaimEdgeBlocked("retrieval_reference_required")
        if not isinstance(item.get("storage_namespace"), str) or not item["storage_namespace"].strip():
            raise ClaimEdgeBlocked("storage_namespace_required")
    history_namespace = history_snapshot["storage_namespace"]
    anchor_namespace = anchor_snapshot["storage_namespace"]
    # Comparison normalisation prevents cosmetic whitespace from masquerading
    # as separation; it does NOT authenticate the declared store origins.
    if history_namespace.strip() == anchor_namespace.strip():
        raise ClaimEdgeBlocked("independent_anchor_namespace_required")
    if history_snapshot["retrieval_id"].strip() == anchor_snapshot["retrieval_id"].strip():
        raise ClaimEdgeBlocked("independent_retrieval_reference_required")
    if history_snapshot.get("claim_id") != anchor_snapshot.get("claim_id"):
        raise ClaimEdgeBlocked("snapshot_claim_mismatch")
    records = history_snapshot.get("records")
    if not isinstance(records, tuple):
        raise ClaimEdgeBlocked("immutable_snapshot_records_required")
    outcome = verify_lab_readback(
        records,
        expected_last_hash=anchor_snapshot.get("last_hash"),
        authenticated_owner_id=owner,
        stored_owner_id=history_snapshot["owner_id"],
        stored_claim_id=history_snapshot["claim_id"],
        anchor_owner_id=anchor_snapshot["owner_id"],
        anchor_claim_id=anchor_snapshot["claim_id"],
        anchor_retained_separately=True,
    )
    return {
        **outcome,
        "distinct_declared_namespaces": True,
        "distinct_retrieval_references": True,
        "external_store_readback_verified": False,
        "namespace_independence_authenticated": False,
        "anchor_authenticity_verified": False,
        # Supplied snapshot metadata cannot attest real-store recovery or release.
        "independent_recovery_verified": False,
        "release_ready": False,
    }


def _uuid_for_snapshot(value: object) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ClaimEdgeBlocked("snapshot_owner_invalid") from exc
