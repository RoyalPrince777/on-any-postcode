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

    certification_views._database_startup_probe()
    payload = _last_json(capsys)

    assert payload["level"] == "info"
    assert payload["reachable"] is True
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
