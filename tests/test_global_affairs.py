"""Negative and truth-boundary coverage for OAP Global Affairs."""
import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from mission_control import global_affairs, workspaces


@pytest.fixture
def store(monkeypatch):
    rows = defaultdict(list)
    receipts = defaultdict(list)

    def list_rows(owner, *, record_type, record_id, limit=100):
        return list(reversed(rows[(owner, record_type, record_id)]))[:limit]

    def list_receipts(owner, *, record_type, record_id, limit=100):
        return list(receipts[(owner, record_type, record_id)])[:limit]

    def add(owner, *, record_type, record_id, version, digest, title, body):
        workspace_record_id = str(uuid4())
        rows[(owner, record_type, record_id)].append({
            "record_id": workspace_record_id,
            "title": title,
            "body": body,
            "status": "draft",
        })
        receipts[(owner, record_type, record_id)].append({
            "event_seq": version,
            "actor_id": owner,
            "target": f"global_affairs:{record_type}:{record_id}",
            "metadata": {
                "workspace_id": "governance",
                "global_affairs_record_type": record_type,
                "global_affairs_record_id": record_id,
                "version": version,
                "digest": digest,
                "record_id": workspace_record_id,
                "record_status": "draft",
                "external_legal_status_conferred": False,
            },
        })
        return workspace_record_id

    monkeypatch.setattr(workspaces, "list_global_affairs_records", list_rows)
    monkeypatch.setattr(workspaces, "list_global_affairs_audit_receipts", list_receipts)
    monkeypatch.setattr(workspaces, "add_global_affairs_record_atomic", add)
    return rows, receipts


def _evidence(**overrides):
    values = {
        "subject_ref": "person:founder",
        "claim_type": "relationship",
        "claim_text": "OAP representative met the named counterparty.",
        "status": "VERIFIED",
        "evidence_class": "C",
        "issuer": "Counterparty",
        "evidence_ref": "letter-001",
        "evidence_hash": "a" * 64,
        "externally_recognised": False,
        "diplomatic_status_claimed": False,
    }
    values.update(overrides)
    return global_affairs.EvidenceRecord(**values)


def _grant(**overrides):
    values = {
        "representative_ref": "person:founder",
        "permission": "lead_meeting",
        "decision": "ALLOW",
        "scope": "Discuss cooperation; no binding agreement authority.",
        "jurisdiction": "GB",
        "founder_approved": True,
    }
    values.update(overrides)
    return global_affairs.AuthorityGrant(**values)


def test_owner_scope_append_only_and_readback(store):
    owner, other = str(uuid4()), str(uuid4())
    rid = str(uuid4())
    saved = global_affairs.save_evidence(owner, rid, _evidence())
    assert saved["audit_readback_verified"] is True
    assert saved["external_legal_status_conferred"] is False
    with pytest.raises(global_affairs.GlobalAffairsUnavailable, match="not_found"):
        global_affairs.get(other, record_type="evidence", record_id=rid)

    updated = global_affairs.save_evidence(
        owner,
        rid,
        _evidence(claim_text="Meeting verified by signed counterparty letter."),
        expected_last_hash=saved["digest"],
    )
    assert updated["version"] == 2


def test_stop_stale_hash_and_tamper_fail_closed(store):
    owner, rid = str(uuid4()), str(uuid4())
    global_affairs.save_evidence(owner, rid, _evidence())
    with pytest.raises(PermissionError, match="STOP"):
        global_affairs.save_evidence(owner, str(uuid4()), _evidence(), stopped=True)
    with pytest.raises(global_affairs.GlobalAffairsUnavailable, match="stale"):
        global_affairs.save_evidence(
            owner, rid, _evidence(claim_text="Changed"), expected_last_hash="wrong",
        )
    row = store[0][(owner, "evidence", rid)][0]
    payload = json.loads(row["body"])
    payload["data"]["claim_text"] = "Forged diplomatic accreditation"
    row["body"] = json.dumps(payload)
    with pytest.raises(global_affairs.GlobalAffairsUnavailable, match="tampered"):
        global_affairs.get(owner, record_type="evidence", record_id=rid)


def test_internal_evidence_cannot_self_promote_to_diplomatic_status():
    with pytest.raises(ValueError, match="accreditation_requires"):
        _evidence(
            status="ACCREDITED",
            evidence_class="E",
            externally_recognised=False,
            diplomatic_status_claimed=True,
        )


def test_accredited_status_requires_external_primary_evidence():
    value = _evidence(
        claim_type="formal_accreditation",
        claim_text="External authority accreditation evidenced.",
        status="ACCREDITED",
        evidence_class="A",
        issuer="Recognised external authority",
        evidence_ref="official-register-123",
        externally_recognised=True,
        diplomatic_status_claimed=True,
    )
    assert value.status == "ACCREDITED"


def test_oap_cannot_self_grant_government_authority():
    with pytest.raises(ValueError, match="cannot_self_grant"):
        _grant(government_authority=True)


def test_revocation_and_expiry_block_authority(store):
    owner = str(uuid4())
    revoked_id = str(uuid4())
    global_affairs.save_authority(owner, revoked_id, _grant(revoked=True))
    revoked = global_affairs.assess_authority(owner, revoked_id)
    assert revoked["decision"] == "BLOCK"
    assert revoked["reason"] == "authority_revoked"

    expired_id = str(uuid4())
    yesterday = (datetime.now(UTC).date() - timedelta(days=1)).isoformat()
    global_affairs.save_authority(owner, expired_id, _grant(expires_on=yesterday))
    expired = global_affairs.assess_authority(owner, expired_id)
    assert expired["decision"] == "BLOCK"
    assert expired["reason"] == "authority_expired"


def test_allow_without_founder_approval_downgrades_to_review(store):
    owner, rid = str(uuid4()), str(uuid4())
    global_affairs.save_authority(owner, rid, _grant(founder_approved=False))
    result = global_affairs.assess_authority(owner, rid)
    assert result["decision"] == "REVIEW"
    assert result["reason"] == "founder_approval_required"



def test_recognised_status_requires_external_recognition():
    with pytest.raises(ValueError, match="recognised_status_requires"):
        _evidence(
            status="RECOGNISED",
            evidence_class="C",
            externally_recognised=False,
        )


@pytest.mark.parametrize("permission", [
    "claim_diplomatic_status",
    "claim_diplomatic_immunity",
    "act_as_diplomat",
    "issue_diplomatic_credential",
    "operate_embassy_or_consulate",
])
def test_external_diplomatic_permissions_cannot_be_self_granted(permission):
    with pytest.raises(ValueError, match="external_diplomatic_authority"):
        _grant(permission=permission)


def test_missing_record_with_remaining_receipt_fails_closed(store):
    owner, rid = str(uuid4()), str(uuid4())
    global_affairs.save_evidence(owner, rid, _evidence())
    store[0][(owner, "evidence", rid)].clear()
    with pytest.raises(global_affairs.GlobalAffairsUnavailable, match="count_mismatch"):
        global_affairs.get(owner, record_type="evidence", record_id=rid)



def test_mission_requires_usable_evidence_and_allowed_authority(store):
    owner = str(uuid4())
    evidence_id, authority_id, mission_id = str(uuid4()), str(uuid4()), str(uuid4())
    global_affairs.save_evidence(owner, evidence_id, _evidence())
    global_affairs.save_authority(owner, authority_id, _grant())
    mission = global_affairs.MissionRecord(
        title="Cultural relations meeting",
        purpose="Discuss a bounded cultural cooperation opportunity.",
        status="APPROVED",
        evidence_record_id=evidence_id,
        authority_record_id=authority_id,
    )
    saved = global_affairs.save_mission(owner, mission_id, mission)
    assert saved["data"]["status"] == "APPROVED"


def test_mission_blocks_without_allowed_authority(store):
    owner = str(uuid4())
    evidence_id, authority_id = str(uuid4()), str(uuid4())
    global_affairs.save_evidence(owner, evidence_id, _evidence())
    global_affairs.save_authority(owner, authority_id, _grant(revoked=True))
    mission = global_affairs.MissionRecord(
        title="Blocked delegation",
        purpose="Must not proceed under revoked authority.",
        status="APPROVED",
        evidence_record_id=evidence_id,
        authority_record_id=authority_id,
    )
    with pytest.raises(ValueError, match="mission_authority_not_allowed"):
        global_affairs.save_mission(owner, str(uuid4()), mission)


def test_internal_credential_verification_and_revocation_recovery(store):
    owner = str(uuid4())
    authority_id, credential_id = str(uuid4()), str(uuid4())
    authority = global_affairs.save_authority(owner, authority_id, _grant())
    credential = global_affairs.CredentialRecord(
        holder_ref="person:founder",
        role_label="Cultural Representative",
        authority_record_id=authority_id,
    )
    global_affairs.save_credential(owner, credential_id, credential)
    verified = global_affairs.verify_credential(owner, credential_id)
    assert verified["valid"] is True
    assert verified["external_legal_status_conferred"] is False

    global_affairs.save_authority(
        owner,
        authority_id,
        _grant(revoked=True),
        expected_last_hash=authority["digest"],
    )
    recovered = global_affairs.recovery_readback(
        owner,
        authority_record_id=authority_id,
        credential_record_id=credential_id,
    )
    assert recovered["authority_decision"] == "BLOCK"
    assert recovered["revoked_or_expired_preserved"] is True
    assert recovered["credential_valid"] is False


@pytest.mark.parametrize("role_label", [
    "Diplomat",
    "Ambassador",
    "Consul",
    "Embassy Representative",
])
def test_internal_credential_cannot_imply_external_diplomatic_status(role_label):
    with pytest.raises(ValueError, match="must_not_imply_external"):
        global_affairs.CredentialRecord(
            holder_ref="person:founder",
            role_label=role_label,
            authority_record_id=str(uuid4()),
        )


def test_credential_cannot_be_active_on_revoked_authority(store):
    owner = str(uuid4())
    authority_id = str(uuid4())
    global_affairs.save_authority(owner, authority_id, _grant(revoked=True))
    credential = global_affairs.CredentialRecord(
        holder_ref="person:founder",
        role_label="Protocol Representative",
        authority_record_id=authority_id,
    )
    with pytest.raises(ValueError, match="credential_requires_active_authority"):
        global_affairs.save_credential(owner, str(uuid4()), credential)
