from __future__ import annotations

from mission_control import certification, web_security

AUTH_ID = "11111111-1111-4111-8111-111111111111"
TARGET_ID = "22222222-2222-4222-8222-222222222222"


def test_certification_roles_are_identity_labels_not_permissions():
    assert certification.CERTIFICATIONS == {
        "creator": {
            "role_id": "certified_creator",
            "name": "Certified Creator",
            "purpose": "OAP creator identity certification for governed creator surfaces.",
        },
        "merchant": {
            "role_id": "certified_merchant",
            "name": "Certified Merchant",
            "purpose": "OAP merchant identity certification for governed business surfaces.",
        },
    }
    assert certification.CERTIFICATION_AUTHORITY_LEVEL == 5
    assert set(certification.ROLE_IDS) == {"certified_creator", "certified_merchant"}


def test_certification_status_is_founder_only(anonymous_client):
    response = anonymous_client.get("/mission/certifications/status")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_can_read_redacted_certification_status(client, monkeypatch):
    monkeypatch.setattr(
        certification,
        "status",
        lambda: {
            "software_ready": True,
            "runtime_ready": False,
            "grants_permissions": False,
            "grants_founder_access": False,
        },
    )

    response = client.get("/mission/certifications/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "software_ready": True,
        "runtime_ready": False,
        "grants_permissions": False,
        "grants_founder_access": False,
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_grant_requires_csrf(client, monkeypatch):
    called = False

    def fake_grant(**_kwargs):
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(certification, "grant", fake_grant)
    response = client.post(
        "/mission/certifications/grant",
        json={
            "identity_id": TARGET_ID,
            "kind": "creator",
            "human_authority_approved": True,
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_invalid"
    assert called is False


def test_founder_grant_passes_exact_identity_and_explicit_approval(
    client, csrf, monkeypatch
):
    observed = {}

    def fake_grant(**kwargs):
        observed.update(kwargs)
        return {
            "identity_id": TARGET_ID,
            "certification": "creator",
            "certified": True,
            "grants_permissions": False,
            "grants_founder_access": False,
            "human_authority_final": True,
        }

    monkeypatch.setattr(certification, "grant", fake_grant)
    token = csrf["csrf_token"]
    response = client.post(
        "/mission/certifications/grant",
        json={
            "identity_id": TARGET_ID,
            "kind": "creator",
            "human_authority_approved": True,
            "csrf_token": token,
        },
        headers={"X-CSRF-Token": token},
    )

    assert response.status_code == 201
    assert observed == {
        "target_identity_id": TARGET_ID,
        "certification_kind": "creator",
        "granted_by_identity_id": AUTH_ID,
        "human_authority_approved": True,
    }
    payload = response.get_json()
    assert payload["certified"] is True
    assert payload["grants_permissions"] is False
    assert payload["grants_founder_access"] is False


def test_founder_revoke_remains_explicit_and_bounded(client, csrf, monkeypatch):
    observed = {}

    def fake_revoke(**kwargs):
        observed.update(kwargs)
        return {
            "identity_id": TARGET_ID,
            "certification": "merchant",
            "certified": False,
            "grants_permissions": False,
            "grants_founder_access": False,
            "human_authority_final": True,
        }

    monkeypatch.setattr(certification, "revoke", fake_revoke)
    token = csrf["csrf_token"]
    response = client.post(
        "/mission/certifications/revoke",
        json={
            "identity_id": TARGET_ID,
            "kind": "merchant",
            "human_authority_approved": True,
        },
        headers={"X-CSRF-Token": token},
    )

    assert response.status_code == 200
    assert observed == {
        "target_identity_id": TARGET_ID,
        "certification_kind": "merchant",
        "revoked_by_identity_id": AUTH_ID,
        "human_authority_approved": True,
    }
    assert response.get_json()["certified"] is False


def test_engine_refuses_implicit_approval_before_touching_store():
    try:
        certification.grant(
            target_identity_id=TARGET_ID,
            certification_kind="merchant",
            granted_by_identity_id=AUTH_ID,
            human_authority_approved=False,
        )
    except PermissionError as exc:
        assert str(exc) == "human_authority_approval_required"
    else:  # pragma: no cover
        raise AssertionError("certification grant must fail closed without approval")


def test_certification_routes_do_not_change_founder_auth_contract():
    assert certification.CERTIFICATION_AUTHORITY_LEVEL == 5
    assert web_security.authenticated_identity is not None
