"""Founder-only API/UI contract for OAP Global Affairs."""
import app as app_module
from mission_control import global_affairs, web_security

OWNER = "11111111-1111-4111-8111-111111111111"
RID = "22222222-2222-4222-8222-222222222222"


def _client(monkeypatch, *, founder=True):
    monkeypatch.setattr(
        web_security, "current_authenticated_user",
        lambda: {"id": OWNER, "name": "Founder", "email": "founder@example.test"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: founder)
    return app_module.app.test_client()


def _csrf(client):
    with client.session_transaction() as session:
        session[web_security.CSRF_SESSION_KEY] = "a" * 48
    return {"X-OAP-CSRF": "a" * 48}


def test_console_is_founder_only_and_no_store(monkeypatch):
    blocked = _client(monkeypatch, founder=False)
    assert blocked.get("/global-affairs").status_code == 403

    client = _client(monkeypatch)
    response = client.get("/global-affairs")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert b"Organiser = what we are doing" in response.data


def test_evidence_put_and_get_use_authenticated_owner(monkeypatch):
    captured = {}

    def save(owner, record_id, value, **kwargs):
        captured["owner"] = owner
        captured["record_id"] = record_id
        assert isinstance(value, global_affairs.EvidenceRecord)
        return {
            "record_type": "evidence", "record_id": record_id,
            "version": 1, "digest": "b" * 64,
            "data": value.__dict__ if hasattr(value, "__dict__") else {},
            "audit_readback_verified": True,
            "external_legal_status_conferred": False,
            "changed": True,
        }

    monkeypatch.setattr(global_affairs, "save_evidence", save)
    monkeypatch.setattr(
        global_affairs, "get",
        lambda owner, **kwargs: {
            "record_type": kwargs["record_type"],
            "record_id": kwargs["record_id"],
            "version": 1,
            "digest": "b" * 64,
            "data": {"status": "VERIFIED"},
            "audit_readback_verified": True,
            "external_legal_status_conferred": False,
        },
    )
    client = _client(monkeypatch)
    headers = _csrf(client)
    payload = {
        "expected_last_hash": "",
        "data": {
            "subject_ref": "organisation:test",
            "claim_type": "relationship",
            "claim_text": "Bounded verified relationship claim.",
            "status": "VERIFIED",
            "evidence_class": "C",
        },
    }
    response = client.put(
        f"/api/global-affairs/evidence/{RID}", json=payload, headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert captured == {"owner": OWNER, "record_id": RID}

    read = client.get(f"/api/global-affairs/evidence/{RID}")
    assert read.status_code == 200
    assert read.get_json()["external_legal_status_conferred"] is False


def test_put_requires_csrf_and_stop_maps_to_locked(monkeypatch):
    client = _client(monkeypatch)
    payload = {
        "data": {
            "representative_ref": "person:founder",
            "permission": "lead_meeting",
            "decision": "ALLOW",
            "scope": "Meeting only.",
            "founder_approved": True,
        },
    }
    assert client.put(
        f"/api/global-affairs/authority/{RID}", json=payload,
    ).status_code == 403

    headers = _csrf(client)
    monkeypatch.setattr(
        global_affairs, "save_authority",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PermissionError("STOP: global affairs write blocked")
        ),
    )
    payload["stopped"] = True
    stopped = client.put(
        f"/api/global-affairs/authority/{RID}", json=payload, headers=headers,
    )
    assert stopped.status_code == 423


def test_credential_verify_and_recovery_are_founder_scoped(monkeypatch):
    monkeypatch.setattr(
        global_affairs, "verify_credential",
        lambda owner, record_id: {
            "valid": True,
            "reason": "internal_oap_credential_valid",
            "holder_ref": "person:founder",
            "role_label": "Cultural Representative",
            "public_claim": "OAP internal representative credential",
            "external_legal_status_conferred": False,
        },
    )
    monkeypatch.setattr(
        global_affairs, "recovery_readback",
        lambda owner, **kwargs: {
            "authority_decision": "BLOCK",
            "authority_reason": "authority_revoked",
            "revoked_or_expired_preserved": True,
            "credential_valid": False,
            "external_legal_status_conferred": False,
        },
    )
    client = _client(monkeypatch)
    verify = client.get(f"/api/global-affairs/credential/{RID}/verify")
    assert verify.status_code == 200
    assert verify.get_json()["external_legal_status_conferred"] is False

    headers = _csrf(client)
    recovery = client.post(
        f"/api/global-affairs/recovery/{RID}",
        json={"credential_record_id": RID},
        headers=headers,
    )
    assert recovery.status_code == 200
    assert recovery.get_json()["revoked_or_expired_preserved"] is True
