import base64
import hashlib
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


def test_music_evidence_routes_are_registered():
    from flask import Flask

    from mission_control import product_core_views

    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/mission/organs/tune/releases/<release_id>/evidence" in rules
    assert "/mission/organs/tune/releases/<release_id>/civilization" in rules


def test_evidence_write_uses_authenticated_owner_and_stays_fail_closed(monkeypatch):
    from flask import Flask

    from mission_control import product_core_views

    app = Flask(__name__)
    release_id = str(uuid4())
    captured = {}
    monkeypatch.setattr(product_core_views, "_write_allowed", lambda: True)
    monkeypatch.setattr(product_core_views, "_identity", lambda **kwargs: "11111111-1111-1111-1111-111111111111")

    def append_receipt(**kwargs):
        captured.update(kwargs)
        return {"receipt_id": str(uuid4()), "receipt_hash": "a" * 64}

    monkeypatch.setattr(product_core_views._music_evidence_store, "append_receipt", append_receipt)
    payload = {
        "evidence_kind": "recording_rights",
        "evidence_base64": base64.b64encode(b"reviewed evidence").decode(),
        "source_reference": "source",
        "authority_reference": "reviewer",
    }
    with app.test_request_context("/", method="POST", json=payload):
        response = product_core_views.append_tune_release_evidence.__wrapped__()
    body = response.get_json()
    assert response.status_code == 201
    assert captured["owner_identity_id"] == "11111111-1111-1111-1111-111111111111"
    assert captured["release_id"] == release_id
    assert captured["evidence_bytes"] == b"reviewed evidence"
    assert body["rights_verified_by_software"] is False
    assert body["external_distribution_enabled"] is False
    assert body["playback_enabled"] is False


def test_evidence_read_gate_requires_recovery_receipt(monkeypatch):
    from flask import Flask

    from mission_control import product_core_views

    app = Flask(__name__)
    owner, release = _ids()
    rows = []
    previous = evidence.GENESIS_HASH
    for kind in [
        "source_page", "recording_rights", "composition_rights",
        "asset_provenance", "territory_permission", "attribution", "human_approval",
    ]:
        row = _receipt(owner, release, kind, previous, kind.encode())
        rows.append(row)
        previous = row["receipt_hash"]

    monkeypatch.setattr(product_core_views, "_identity", lambda **kwargs: owner)
    monkeypatch.setattr(product_core_views._music_evidence_store, "read_receipts", lambda **kwargs: rows)
    with app.test_request_context("/", method="GET"):
        response = product_core_views.tune_release_evidence.__wrapped__(release)
    body = response.get_json()
    assert response.status_code == 200
    assert body["chain"]["chain_verified"] is True
    assert body["distribution_gate"]["private_handoff_ready"] is False
    assert body["distribution_gate"]["recovery_readback_proven"] is False
    assert body["public_catalogue_enabled"] is False
