from __future__ import annotations

import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mission_control import authority, movement_certification, web_security


class _Result:
    def __init__(self, value):
        self.value = value

    def fetchone(self):
        return self.value

    def fetchall(self):
        return self.value


class _Connection:
    def __init__(self, steps):
        self.steps = list(steps)
        self.committed = False
        self.queries: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        if not self.steps:
            raise AssertionError(f"unexpected SQL: {sql}")
        expected, value = self.steps.pop(0)
        assert expected in sql
        return _Result(value)

    def commit(self):
        self.committed = True


def _connect(connection):
    @contextmanager
    def factory(*, readonly=False):
        del readonly
        yield connection

    return factory


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
    assert "CHECK (role_granted = FALSE)" in schema_sql
    assert "terms_version TEXT NOT NULL" in schema_sql
    assert "terms_digest TEXT NOT NULL" in schema_sql
    assert "retention_expires_at" in schema_sql
    assert "applicant_message TEXT NOT NULL" in schema_sql
    assert "FOREIGN KEY (application_id, identity_id)" in schema_sql
    assert movement_certification._migration_statements()


def test_free_text_is_rejected_instead_of_silently_truncated():
    with pytest.raises(ValueError, match="service_zone_too_long"):
        movement_certification._text(
            "x" * 41,
            name="service_zone",
            maximum=40,
        )


def test_registration_suffix_is_ascii_and_bounded():
    assert movement_certification._registration("ab12") == "AB12"
    with pytest.raises(ValueError, match="invalid_registration_last4"):
        movement_certification._registration("A£12")


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
    assert movement_certification.APPLICATION_NOTICE_VERSION in html
    assert "deletion after 90 days" in html
    assert "Do not submit licence numbers" in html


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


def test_review_page_separates_private_reason_from_applicant_message(
    client, monkeypatch
):
    monkeypatch.setattr(
        movement_certification,
        "review_queue",
        lambda identity: [
            {
                "application_id": "22222222-2222-4222-8222-222222222222",
                "identity_id": identity,
                "role_type": "rider",
                "vehicle_type": "ebike",
                "service_zone": "CR4",
                "state": "SUBMITTED",
                "external_compliance_state": "PROVIDER_REQUIRED",
                "vehicle_label": "Cargo e-bike",
                "registration_last4": "",
                "applicant_response": "",
                "terms_version": movement_certification.APPLICATION_NOTICE_VERSION,
                "retention_expires_at": "2026-11-26T00:00:00+00:00",
                "allowed_decisions": ("NEEDS_INFO", "REJECTED"),
            }
        ],
    )
    monkeypatch.setattr(
        movement_certification,
        "schema_status",
        lambda: {"ready": True, "expired_records": 0},
    )

    response = client.get("/mission/movement-certification")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Private review reason" in html
    assert "Applicant-facing message" in html
    assert "do not enter documents" in html


def test_review_api_never_reports_role_granted(client, monkeypatch):
    headers = _csrf_headers(client)
    captured = {}

    def review_application(**kwargs):
        captured.update(kwargs)
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
        json={
            "decision": "INTERNAL_APPROVED",
            "reason": "Internal checks complete",
            "applicant_message": "Internal review complete",
        },
    )

    assert response.status_code == 200
    review = response.get_json()["review"]
    assert review["role_granted"] is False
    assert review["external_compliance_required"] is True
    assert captured["applicant_message"] == "Internal review complete"


def test_resubmit_api_uses_authenticated_owner_identity(client, monkeypatch):
    headers = _csrf_headers(client)
    captured = {}

    def resubmit_application(**kwargs):
        captured.update(kwargs)
        return {
            "application_id": kwargs["application_id"],
            "state": "SUBMITTED",
            "role_granted": False,
        }

    monkeypatch.setattr(
        movement_certification,
        "resubmit_application",
        resubmit_application,
    )
    response = client.post(
        "/movement/worker-applications/22222222-2222-4222-8222-222222222222/resubmit",
        headers=headers,
        json={
            "service_zone": "CR4",
            "response_message": "Clarified safely",
            "declarations": {"age_18_or_over": True, "terms_accepted": True},
        },
    )

    assert response.status_code == 200
    assert captured["identity_id"] == "11111111-1111-4111-8111-111111111111"
    assert captured["response_message"] == "Clarified safely"


def test_cancel_api_uses_authenticated_owner_identity(client, monkeypatch):
    headers = _csrf_headers(client)
    captured = {}

    def cancel_application(**kwargs):
        captured.update(kwargs)
        return {
            "application_id": kwargs["application_id"],
            "state": "CANCELLED",
            "personal_fields_scrubbed": True,
            "role_granted": False,
        }

    monkeypatch.setattr(
        movement_certification,
        "cancel_application",
        cancel_application,
    )
    response = client.post(
        "/movement/worker-applications/22222222-2222-4222-8222-222222222222/cancel",
        headers=headers,
        json={},
    )

    assert response.status_code == 200
    assert captured["identity_id"] == "11111111-1111-4111-8111-111111111111"


def test_expired_purge_requires_human_authority(client, monkeypatch):
    headers = _csrf_headers(client)

    def deny(**kwargs):
        del kwargs
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(
        movement_certification,
        "purge_expired_applications",
        deny,
    )
    response = client.post(
        "/mission/movement-certification/purge-expired",
        headers=headers,
        json={"confirm": "PURGE_EXPIRED"},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "level_zero_human_authority_required"


def test_review_rejects_terminal_state_transition_under_row_lock(monkeypatch):
    connection = _Connection(
        [("SELECT state,external_compliance_state", ("REJECTED", "PROVIDER_REQUIRED"))]
    )
    monkeypatch.setattr(
        movement_certification.postgres_db,
        "connect",
        _connect(connection),
    )
    monkeypatch.setattr(
        movement_certification.authority,
        "require_human_authority",
        lambda current, reviewer: {"identity_id": reviewer},
    )

    with pytest.raises(ValueError, match="invalid_certification_state_transition"):
        movement_certification.review_application(
            reviewer_identity_id="11111111-1111-4111-8111-111111111111",
            application_id="22222222-2222-4222-8222-222222222222",
            decision="INTERNAL_APPROVED",
            reason="Attempt to reopen a terminal record",
        )

    assert connection.committed is False
    assert "FOR UPDATE" in connection.queries[0][0]
    assert len(connection.queries) == 1


def test_review_records_allowed_transition_without_role_grant(monkeypatch):
    now = datetime.now(timezone.utc)
    connection = _Connection(
        [
            ("SELECT state,external_compliance_state", ("SUBMITTED", "PROVIDER_REQUIRED")),
            ("UPDATE oap_movement_worker_applications", None),
            (
                "INSERT INTO oap_movement_certification_reviews",
                ("33333333-3333-4333-8333-333333333333", now),
            ),
        ]
    )
    monkeypatch.setattr(
        movement_certification.postgres_db,
        "connect",
        _connect(connection),
    )
    monkeypatch.setattr(
        movement_certification.authority,
        "require_human_authority",
        lambda current, reviewer: {"identity_id": reviewer},
    )

    result = movement_certification.review_application(
        reviewer_identity_id="11111111-1111-4111-8111-111111111111",
        application_id="22222222-2222-4222-8222-222222222222",
        decision="NEEDS_INFO",
        reason="A bounded internal reason",
        applicant_message="Please clarify the service zone without sending documents.",
    )

    assert result["decision"] == "NEEDS_INFO"
    assert result["role_granted"] is False
    assert connection.committed is True
    insert_sql = connection.queries[2][0]
    assert "applicant_message,role_granted" in insert_sql
    assert "FALSE" in insert_sql


def test_needs_info_requires_separate_applicant_message():
    with pytest.raises(ValueError, match="applicant_message_required"):
        movement_certification.review_application(
            reviewer_identity_id="11111111-1111-4111-8111-111111111111",
            application_id="22222222-2222-4222-8222-222222222222",
            decision="NEEDS_INFO",
            reason="Private internal reason",
        )


def test_resubmit_is_owner_scoped_and_only_accepts_needs_info(monkeypatch):
    connection = _Connection(
        [
            ("SELECT state,vehicle_type", ("NEEDS_INFO", "ebike")),
            ("UPDATE oap_movement_worker_applications", None),
            ("UPDATE oap_movement_vehicles", None),
        ]
    )
    monkeypatch.setattr(
        movement_certification.postgres_db,
        "connect",
        _connect(connection),
    )
    identity = "11111111-1111-4111-8111-111111111111"
    application = "22222222-2222-4222-8222-222222222222"

    result = movement_certification.resubmit_application(
        identity_id=identity,
        application_id=application,
        service_zone="CR4",
        vehicle_label="Cargo e-bike",
        registration_last4="",
        declarations={"age_18_or_over": True, "terms_accepted": True},
        response_message="Service zone clarified without personal documents.",
    )

    assert result["state"] == "SUBMITTED"
    assert result["role_granted"] is False
    assert connection.committed is True
    assert connection.queries[0][1] == (application, identity)


def test_cancel_is_owner_scoped_and_scrubs_optional_data(monkeypatch):
    connection = _Connection(
        [
            ("SELECT state", ("UNDER_REVIEW",)),
            ("SET state='CANCELLED'", None),
            ("SET display_label=''", None),
        ]
    )
    monkeypatch.setattr(
        movement_certification.postgres_db,
        "connect",
        _connect(connection),
    )
    identity = "11111111-1111-4111-8111-111111111111"
    application = "22222222-2222-4222-8222-222222222222"

    result = movement_certification.cancel_application(
        identity_id=identity,
        application_id=application,
    )

    assert result["state"] == "CANCELLED"
    assert result["personal_fields_scrubbed"] is True
    assert connection.committed is True
    assert connection.queries[0][1] == (application, identity)
