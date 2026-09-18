from __future__ import annotations

import base64
import json

from mission_control import certification_views, postgres_db

_DB_ENV_KEYS = (
    "OAP_DATABASE_AUTHORITY",
    "OAP_FALLBACK_DATABASE_URL_B64",
    "OAP_FALLBACK_DATABASE_URL",
    "OAP_PRIMARY_DATABASE_URL_B64",
    "OAP_PRIMARY_DATABASE_URL",
    "DATABASE_URL",
    "OAP_DB_SECRET_B64",
    "OAP_NEON_DATABASE_URL_B64",
    "OAP_NEON_DATABASE_URL",
)


def _clear_database_env(monkeypatch) -> None:
    for key in _DB_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_platform_database_url_beats_stale_neon_alias(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("DATABASE_URL", "postgresql://render-primary/internal")
    monkeypatch.setenv("OAP_NEON_DATABASE_URL", "postgresql://legacy-neon/blocked")
    monkeypatch.setenv(
        "OAP_NEON_DATABASE_URL_B64",
        base64.b64encode(b"postgresql://legacy-neon-b64/blocked").decode("ascii"),
    )

    assert postgres_db._database_url() == "postgresql://render-primary/internal"
    assert postgres_db.database_source() == "platform_database_url"


def test_explicit_primary_override_beats_platform_database_url(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/selected")
    monkeypatch.setenv("DATABASE_URL", "postgresql://platform/secondary")
    monkeypatch.setenv("OAP_NEON_DATABASE_URL", "postgresql://legacy-neon/blocked")

    assert postgres_db._database_url() == "postgresql://primary/selected"
    assert postgres_db.database_source() == "primary_override"


def test_malformed_explicit_primary_b64_fails_closed(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL_B64", "not-valid-base64!!")
    monkeypatch.setenv("DATABASE_URL", "postgresql://platform/must-not-be-used")
    monkeypatch.setenv("OAP_NEON_DATABASE_URL", "postgresql://legacy/must-not-be-used")

    assert postgres_db._database_url() == ""
    assert postgres_db.database_source() == "primary_override"
    assert postgres_db.configured() is False


def test_legacy_neon_remains_supported_when_no_primary_exists(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_NEON_DATABASE_URL", "postgresql://legacy-neon/available")

    assert postgres_db._database_url() == "postgresql://legacy-neon/available"
    assert postgres_db.database_source() == "legacy_neon"


def test_startup_probe_is_redacted(monkeypatch, capsys):
    monkeypatch.setattr(
        certification_views.postgres_db,
        "postgres_status",
        lambda: {
            "backend": "postgresql",
            "source": "platform_database_url",
            "configured": True,
            "reachable": True,
            "initialized": False,
            "pending": ["0003_product_governance"],
            "checksum_mismatches": [],
            "error": None,
            "url": "postgresql://secret:password@example.invalid/db",
        },
    )

    certification_views._database_startup_probe()
    payload = json.loads(capsys.readouterr().out)

    assert payload == {
        "backend": "postgresql",
        "checksum_mismatch": False,
        "configured": True,
        "event": "oap_database_startup_probe",
        "initialized": False,
        "level": "warning",
        "pending_migrations": 1,
        "read_only": True,
        "reachable": True,
        "secret_exposed": False,
        "source": "platform_database_url",
    }
    rendered = json.dumps(payload)
    assert "password" not in rendered
    assert "example.invalid" not in rendered


def test_fallback_is_never_used_without_explicit_promotion(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/selected")
    monkeypatch.setenv("OAP_FALLBACK_DATABASE_URL", "postgresql://fallback/standby")

    assert postgres_db._database_url() == "postgresql://primary/selected"
    assert postgres_db.database_source() == "primary_override"
    assert postgres_db.database_authority() == "primary"


def test_explicit_fallback_promotion_selects_only_fallback(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "fallback")
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/do-not-use")
    monkeypatch.setenv("OAP_FALLBACK_DATABASE_URL", "postgresql://fallback/selected")

    assert postgres_db._database_url() == "postgresql://fallback/selected"
    assert postgres_db.database_source() == "fallback_override"
    assert postgres_db.database_authority() == "fallback"


def test_missing_promoted_fallback_fails_closed(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "fallback")
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/must-not-be-used")

    assert postgres_db._database_url() == ""
    assert postgres_db.database_source() == "fallback_unconfigured"
    assert postgres_db.configured() is False


def test_malformed_promoted_fallback_b64_fails_closed(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "fallback")
    monkeypatch.setenv("OAP_FALLBACK_DATABASE_URL_B64", "not-valid-base64!!")
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/must-not-be-used")

    assert postgres_db._database_url() == ""
    assert postgres_db.database_source() == "fallback_override"
    assert postgres_db.configured() is False


def test_invalid_database_authority_fails_closed(monkeypatch):
    _clear_database_env(monkeypatch)
    monkeypatch.setenv("OAP_DATABASE_AUTHORITY", "both")
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "postgresql://primary/must-not-be-used")
    monkeypatch.setenv("OAP_FALLBACK_DATABASE_URL", "postgresql://fallback/must-not-be-used")

    assert postgres_db._database_url() == ""
    assert postgres_db.database_source() == "invalid_authority"
    assert postgres_db.database_authority() == "invalid"
    assert postgres_db.configured() is False
