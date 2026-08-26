from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from mission_control import authority, movement_certification, web_security


def _csrf_headers(client):
    token = "movement-certification-csrf-test-token-1234567890"
    with client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token
    return {"X-OAP-CSRF": token}


def test_motor_vehicle_application_requires_licence_and_insurance_declarations():
    with pytest.raises(ValueError, match="motor_vehicle_declarations_required"):
        movement_certification._declarations(
            {"age_18_or_over": True, "terms_accepted": True},
            vehicle="car",
        )


def test_ebike_application_does_not_invent_motor_vehicle_requirements():
    result = movement_certification._declarations(
        {"age_18_or_over": True, "terms_accepted": True},
        vehicle="ebike",
    )

    assert result["age_18_or_over"] is True
    assert result["terms_accepted"] is True
    assert result["licence_declared"] is False
    assert result["insurance_declared"] is False


def test_role_vehicle_compatibility_is_bounded():
    assert movement_certification._vehicle("car", role="driver") == "car"
    assert movement_certification._vehicle("ebike", role="rider") == "ebike"
    assert movement_certification._vehicle("ebike", role="courier") == "ebike"

    with pytest.raises(ValueError, match="invalid_vehicle_for_role"):
        movement_certification._vehicle("bicycle", role="driver")


def test_certification_migration_checksum_and_fail_closed_role_grant():
    path = Path("migrations/0006_movement_certification.sql")
    text = path.read_text(encoding="utf-8")
    schema_sql, migration_record = text.split("\nINSERT INTO oap_schema_migrations", 1)
    checksum = hashlib.sha256((schema_sql + "\n").encode()).hexdigest()

    assert checksum == movement_certification.MIGRATION_CHECKSUM
    assert movement_certification.MIGRATION_VERSION in migration_record
    assert movement_certification.MIGRATION_CHECKSUM in migration_record
    assert "oap_movement_worker_applications" in schema_sql
    assert "oap_movement_vehicles" in schema_sql
    assert "oap_movement_certification_reviews" in schema_sql
    assert "INSERT INTO oap_identity_roles" not in schema_sql
    assert "role_granted BOOLEAN NOT NULL DEFAULT FALSE" in schema_sql


def test_certification_applicant_page_requires_authentication(anonymous_client):
    response = anonymous_client.get("/movement/certification")

    assert response.status_code == 302
    assert "/enter-my-world" in response.headers["Location"]
    assert "next=/movement/certification" in response.headers["Location"]


def test_authenticated_applicant_page_states_role_grant_boundary(client, monkeypatch):
    monkeypatch.setattr(movement_certification, "own_applications", lambda identity: [])
    monkeypatch.setattr(
        movement_certification,
        "schema_status",
        lambda: {
            "ready": True,
            "external_compliance_provider_connected": False,
            "automatic_role_grant_enabled": False,
        },
    )

    response = client.get("/movement/certification")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Movement Certification" in html
    assert "Role grant stays locked" in html
    assert "Submitting this form is not certification" in html
    assert "licence number" in html
    assert "date of birth" in html


def test_worker_application_api_requires_authentication(anonymous_client):
    response = anonymous_client.post("/movement/worker-applications", json={})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_worker_application_api_submits_without_role_grant(client, monkeypatch):
    headers = _csrf_headers(client)
    captured = {}

    def submit_application(**kwargs):
        captured.update(kwargs)
        return {
            "application_id": "22222222-2222-4222-8222-222222222222",
            "role_type": "rider",
            "vehicle_type": "ebike",
            "state": "SUBMITTED",
            "external_compliance_state": "PROVIDER_REQUIRED",
            "role_granted": False,
            "external_compliance_required": True,
        }

    monkeypatch.setattr(movement_certification, "submit_application", submit_application)
    response = client.post(
        "/movement/worker-applications",
        headers=headers,
        json={
            "role_type": "rider",
            "vehicle_type": "ebike",
            "service_zone": "CR4",
            "declarations": {"age_18_or_over": True, "terms_accepted": True},
        },
    )

    assert response.status_code == 201
    payload = response.get_json()["application"]
    assert payload["role_granted"] is False
    assert payload["external_compliance_required"] is True
    assert captured["role_type"] == "rider"
    assert captured["vehicle_type"] == "ebike"


def test_human_authority_review_page_fails_closed_for_non_authority(client, monkeypatch):
    def deny(identity):
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(movement_certification, "review_queue", deny)
    response = client.get("/mission/movement-certification")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "level_zero_human_authority_required"


def test_review_api_never_reports_role_granted(client, monkeypatch):
    headers = _csrf_headers(client)

    def review_application(**kwargs):
        return {
            "review_id": "33333333-3333-4333-8333-333333333333",
            "application_id": kwargs["application_id"],
            "decision": "INTERNAL_APPROVED",
            "role_granted": False,
            "external_compliance_state": "PROVIDER_REQUIRED",
            "external_compliance_required": True,
        }

    monkeypatch.setattr(movement_certification, "review_application", review_application)
    response = client.post(
        "/mission/movement-certification/22222222-2222-4222-8222-222222222222/review",
        headers=headers,
        json={"decision": "INTERNAL_APPROVED", "reason": "Internal checks complete"},
    )

    assert response.status_code == 200
    review = response.get_json()["review"]
    assert review["role_granted"] is False
    assert review["external_compliance_required"] is True
