from __future__ import annotations

import json

from mission_control import certification_views


def _last_json(capsys):
    line = capsys.readouterr().out.strip().splitlines()[-1]
    return json.loads(line)


def test_database_startup_probe_marks_proven_success_info(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.postgres_db,
        "postgres_status",
        lambda: {
            "backend": "postgresql",
            "source": "platform_database_url",
            "configured": True,
            "reachable": True,
            "initialized": True,
            "pending": (),
            "checksum_mismatches": (),
            "error": None,
        },
    )

    monkeypatch.setattr(
        certification_views.postgres_db,
        "database_identity_fingerprint",
        lambda: {
            "fingerprint": "fedcba9876543210fedcba9876543210",
            "reachable": True,
            "secret_exposed": False,
            "error": None,
        },
    )

    certification_views._database_startup_probe()
    payload = _last_json(capsys)

    assert payload["level"] == "info"
    assert payload["reachable"] is True
    assert payload["database_identity_reachable"] is True
    assert payload["database_identity_fingerprint"] == "fedcba9876543210fedcba9876543210"
    assert payload["initialized"] is True
    assert payload["pending_migrations"] == 0
    assert "error" not in payload
    assert payload["secret_exposed"] is False


def test_hrm_startup_probe_marks_proven_success_info(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.hrm_readonly_probe,
        "status",
        lambda: {
            "backend": "independent_hrm_postgres_candidate",
            "source": "oap_hrm_database_url",
            "configured": True,
            "reachable": True,
            "error": None,
        },
    )

    certification_views._hrm_candidate_startup_probe()
    payload = _last_json(capsys)

    assert payload["level"] == "info"
    assert payload["reachable"] is True
    assert "error" not in payload
    assert payload["write_performed"] is False
    assert payload["schema_changed"] is False


def test_failed_probe_keeps_error_truth(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.postgres_db,
        "postgres_status",
        lambda: {
            "backend": "postgresql",
            "source": "platform_database_url",
            "configured": True,
            "reachable": False,
            "initialized": False,
            "pending": ("001",),
            "checksum_mismatches": (),
            "error": "database_unavailable",
        },
    )

    certification_views._database_startup_probe()
    payload = _last_json(capsys)

    assert payload["level"] == "error"
    assert payload["error"] == "database_unavailable"
    assert payload["reachable"] is False


def test_mail_startup_probe_preserves_recovery_hold(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.mail_preflight,
        "report",
        lambda: {
            "database_source": "platform_database_url",
            "database_configured": True,
            "database_reachable": True,
            "base_schema_ready": True,
            "mail_schema_ready": True,
            "target_mapping_proven": False,
            "recovery_point_verified": False,
            "independent_release_evidence_verified": False,
            "live_migration_authorized": False,
            "release_ready": False,
            "error": "independent_recovery_evidence_missing",
        },
    )

    certification_views._mail_startup_probe()
    payload = _last_json(capsys)

    assert payload == {
        "base_schema_ready": True,
        "database_configured": True,
        "database_reachable": True,
        "database_source": "platform_database_url",
        "error": "independent_recovery_evidence_missing",
        "event": "oap_mail_startup_probe",
        "independent_release_evidence_verified": False,
        "level": "warning",
        "live_migration_authorized": False,
        "mail_schema_ready": True,
        "read_only": True,
        "recovery_point_verified": False,
        "release_ready": False,
        "schema_changed": False,
        "secret_exposed": False,
        "target_mapping_proven": False,
    }


def test_mail_startup_probe_never_calls_green_from_schema_alone(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.mail_preflight,
        "report",
        lambda: {
            "database_source": "platform_database_url",
            "database_configured": True,
            "database_reachable": True,
            "base_schema_ready": True,
            "mail_schema_ready": True,
            "target_mapping_proven": True,
            "recovery_point_verified": False,
            "independent_release_evidence_verified": False,
            "live_migration_authorized": False,
            "release_ready": False,
            "error": None,
        },
    )

    certification_views._mail_startup_probe()
    payload = _last_json(capsys)

    assert payload["level"] == "warning"
    assert payload["mail_schema_ready"] is True
    assert payload["target_mapping_proven"] is True
    assert payload["recovery_point_verified"] is False
    assert payload["release_ready"] is False
    assert payload["schema_changed"] is False
    assert payload["secret_exposed"] is False
