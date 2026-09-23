"""Four independent Mail gates: neither a preview nor a test receipt is release proof."""
from __future__ import annotations

import app as app_module

from mission_control import mail_preflight, postgres_db


def test_mailbox_not_accessible_anonymously(anonymous_client):
    response = anonymous_client.get("/mail/app")
    assert response.status_code in (302, 303, 401, 403)
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_mailbox_preview_is_explicitly_not_a_delivery_service(client):
    response = client.get("/mail/app")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "No email delivery" in page
    assert "This preview is not a released email service" in page
    assert "OAP Store listing" not in page


def test_no_mail_send_or_receive_executor(client, csrf):
    for path in ("/mail/send", "/mail/receive", "/mail/forward", "/mail/deliver"):
        response = client.post(
            path, json={"owner_consent": True, "human_approved": True},
            headers={"X-OAP-CSRF": csrf["csrf_token"]},
        )
        assert response.status_code in (404, 405)
    assert "oap.mail.delivery" not in str(app_module.app.url_map)


def test_store_listing_remains_uninstallable(client):
    response = client.get("/oap-store/apps/oap.mail")
    assert response.status_code == 200
    record = response.get_json()
    assert record["informational_only"] is True
    assert record["public_release_state"] == "release_pending"
    assert record["delivery_enabled"] is False
    assert record["install_enabled"] is False
    assert record["package_available"] is False
    assert client.post("/oap-store/apps/oap.mail/install").status_code in (404, 405)


def test_mail_migration_needs_independent_proof_and_has_no_live_cli(monkeypatch):
    from mission_control import mail_migration

    operations = []

    def no_database(*_args, **_kwargs):
        operations.append("database")
        raise AssertionError("unverified migration opened database")

    monkeypatch.setattr(mail_preflight, "report", lambda: {
        "database_configured": True,
        "database_reachable": True,
        "base_schema_ready": True,
        "target_mapping_proven": False,
        "recovery_point_verified": False,
        "independent_release_evidence_verified": False,
        "live_migration_authorized": False,
    })
    monkeypatch.setattr(postgres_db, "postgres_status", no_database)
    monkeypatch.setattr(postgres_db, "connect", no_database)
    try:
        mail_migration.init_schema(assume_yes=True)
    except RuntimeError as exc:
        assert str(exc) == "mail_independent_recovery_evidence_required"
    else:
        raise AssertionError("Mail migration bypassed independent recovery proof")
    assert operations == []
    assert "oap-init-mail" not in app_module.app.cli.commands
