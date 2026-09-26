from uuid import uuid4

import pytest

from mission_control import music_evidence as evidence


def _ids():
    return str(uuid4()), str(uuid4())


def _receipt(owner, release, kind, previous=evidence.GENESIS_HASH, payload=b"proof"):
    return evidence.build_receipt(
        owner_identity_id=owner,
        release_id=release,
        evidence_kind=kind,
        evidence_bytes=payload,
        previous_receipt_hash=previous,
        source_reference="first-party evidence",
        authority_reference="independent review",
    )


def test_receipt_hash_chain_detects_tamper_and_reordering():
    owner, release = _ids()
    one = _receipt(owner, release, "source_page")
    two = _receipt(owner, release, "recording_rights", one["receipt_hash"], b"recording")
    assert evidence.verify_receipt_chain([one, two])["chain_verified"] is True

    tampered = dict(two)
    tampered["evidence_sha256"] = "f" * 64
    assert evidence.verify_receipt_chain([one, tampered])["chain_verified"] is False
    assert evidence.verify_receipt_chain([two, one])["chain_verified"] is False


def test_receipts_hash_actual_bytes_and_reject_claimed_hash_injection():
    owner, release = _ids()
    result = _receipt(owner, release, "asset_provenance", payload=b"asset bytes")
    import hashlib
    assert result["evidence_sha256"] == hashlib.sha256(b"asset bytes").hexdigest()
    with pytest.raises(ValueError, match="invalid_evidence_bytes"):
        evidence.build_receipt(
            owner_identity_id=owner, release_id=release,
            evidence_kind="asset_provenance", evidence_bytes="claimed hash",
        )


def test_private_distribution_gate_requires_complete_chain_and_recovery():
    owner, release = _ids()
    kinds = [
        "source_page", "recording_rights", "composition_rights",
        "asset_provenance", "territory_permission", "attribution", "human_approval",
    ]
    rows = []
    previous = evidence.GENESIS_HASH
    for kind in kinds:
        row = _receipt(owner, release, kind, previous, kind.encode())
        rows.append(row)
        previous = row["receipt_hash"]

    blocked = evidence.private_distribution_gate(rows, recovery_readback_proven=False)
    assert blocked["private_handoff_ready"] is False
    assert blocked["external_distribution_enabled"] is False
    assert blocked["playback_enabled"] is False

    ready = evidence.private_distribution_gate(rows, recovery_readback_proven=True)
    assert ready["private_handoff_ready"] is True
    assert ready["missing_evidence_kinds"] == []
    assert ready["rights_verified_by_software"] is False
    assert ready["external_distribution_enabled"] is False
    assert ready["public_catalogue_enabled"] is False


def test_missing_recording_or_composition_rights_fails_closed():
    owner, release = _ids()
    row = _receipt(owner, release, "source_page")
    result = evidence.private_distribution_gate([row], recovery_readback_proven=True)
    assert result["private_handoff_ready"] is False
    assert "recording_rights" in result["missing_evidence_kinds"]
    assert "composition_rights" in result["missing_evidence_kinds"]


def test_civilization_projection_only_surfaces_evidence_bound_links():
    receipt_id = str(uuid4())
    result = evidence.civilization_projection([
        {"level": "country", "value": "Ghana", "evidence_receipt_id": receipt_id},
        {"level": "culture", "value": "Akan", "evidence_receipt_id": receipt_id},
        {"level": "culture", "value": "Akan", "evidence_receipt_id": receipt_id},
        {"level": "made_up", "value": "x", "evidence_receipt_id": receipt_id},
        {"level": "genre", "value": "<script>" * 100, "evidence_receipt_id": receipt_id},
    ])
    assert result["graph"]["country"] == [{"value": "Ghana", "evidence_receipt_id": receipt_id}]
    assert result["graph"]["culture"] == [{"value": "Akan", "evidence_receipt_id": receipt_id}]
    assert result["graph"]["genre"] == []
    assert result["inference_performed"] is False
    assert result["public_claims_enabled"] is False


def test_schema_is_owner_scoped_append_only_and_bound_to_existing_release():
    sql = "\n".join(evidence.SCHEMA_STATEMENTS)
    assert "REFERENCES oap_music_releases(release_id)" in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "receipt_hash TEXT NOT NULL UNIQUE" in sql
    assert "UPDATE oap_music_evidence_receipts" not in sql
    assert "DELETE FROM oap_music_evidence_receipts" not in sql


def test_caller_cannot_make_public_or_playable_with_flags():
    owner, release = _ids()
    row = _receipt(owner, release, "human_approval")
    poisoned = dict(row)
    poisoned.update({
        "rights_verified": True,
        "playback_enabled": True,
        "public_catalogue_enabled": True,
        "distribution_authorised": True,
    })
    result = evidence.private_distribution_gate([poisoned], recovery_readback_proven=True)
    assert result["private_handoff_ready"] is False
    assert result["external_distribution_enabled"] is False
    assert result["playback_enabled"] is False
    assert result["public_catalogue_enabled"] is False
