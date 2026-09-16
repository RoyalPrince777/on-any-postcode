from __future__ import annotations

import base64
import json

from mission_control import certification_views, hrm_readonly_probe

_HRM_ENV_KEYS = (
    "OAP_HRM_DATABASE_URL",
    "OAP_SMI_HRM_DATABASE_URL",
    "OAP_HRM_DATABASE_URL_B64",
    "OAP_SMI_HRM_DATABASE_URL_B64",
)


def _clear(monkeypatch) -> None:
    for key in _HRM_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_hrm_probe_is_unconfigured_without_alias(monkeypatch):
    _clear(monkeypatch)

    status = hrm_readonly_probe.status()

    assert status["configured"] is False
    assert status["reachable"] is False
    assert status["source"] == "unconfigured"
    assert status["error"] == "hrm_database_url_not_configured"
    assert status["write_performed"] is False
    assert status["schema_changed"] is False
    assert status["secret_exposed"] is False


def test_direct_hrm_alias_beats_encoded_fallback(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OAP_HRM_DATABASE_URL", "postgresql://direct/internal")
    monkeypatch.setenv(
        "OAP_HRM_DATABASE_URL_B64",
        base64.b64encode(b"postgresql://encoded/fallback").decode("ascii"),
    )

    url, source = hrm_readonly_probe._database_config()

    assert url == "postgresql://direct/internal"
    assert source == "oap_hrm_database_url"


def test_malformed_hrm_b64_fails_closed(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("OAP_HRM_DATABASE_URL_B64", "not-valid-base64!!")

    status = hrm_readonly_probe.status()

    assert status["configured"] is False
    assert status["source"] == "oap_hrm_database_url_b64"
    assert status["reachable"] is False
    assert status["secret_exposed"] is False


def test_hrm_startup_proof_never_emits_secret_fields(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.hrm_readonly_probe,
        "status",
        lambda: {
            "backend": "independent_hrm_postgres_candidate",
            "source": "oap_hrm_database_url",
            "configured": True,
            "reachable": True,
            "error": None,
            "url": "postgresql://secret:password@example.invalid/db",
        },
    )

    certification_views._hrm_candidate_startup_probe()
    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "backend": "independent_hrm_postgres_candidate",
        "configured": True,
        "event": "oap_hrm_candidate_startup_probe",
        "level": "info",
        "read_only": True,
        "reachable": True,
        "schema_changed": False,
        "secret_exposed": False,
        "source": "oap_hrm_database_url",
        "write_performed": False,
    }
    rendered = json.dumps(payload)
    assert "password" not in rendered
    assert "example.invalid" not in rendered
