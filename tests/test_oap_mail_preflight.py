"""Mail preflight must never make database or recovery claims from names alone."""
from __future__ import annotations

from mission_control import mail_migration, mail_preflight, postgres_db


def _sources(monkeypatch, *, configured=True, authority="primary",
             source="primary_override"):
    monkeypatch.setattr(postgres_db, "configured", lambda: configured)
    monkeypatch.setattr(postgres_db, "database_authority", lambda: authority)
    monkeypatch.setattr(postgres_db, "database_source", lambda: source)


def test_preflight_rejects_unconfigured_without_any_database_call(monkeypatch):
    _sources(monkeypatch, configured=False)
    def unexpected():
        raise AssertionError("database must not be queried")
    monkeypatch.setattr(postgres_db, "postgres_status", unexpected)
    result = mail_preflight.report()
    assert result["error"] == "database_selection_unavailable"
    assert result["target_mapping_proven"] is False
    assert result["recovery_point_verified"] is False
    assert result["release_ready"] is False


def test_preflight_rejects_invalid_database_authority(monkeypatch):
    _sources(monkeypatch, authority="invalid", source="invalid_authority")
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("must not connect")))
    assert mail_preflight.report()["error"] == "database_selection_unavailable"


def test_preflight_never_promotes_a_reachable_mail_schema_to_green(monkeypatch):
    _sources(monkeypatch, source="fallback_override", authority="fallback")
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"reachable": True, "initialized": True})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: {"schema_ready": True, "error": None})
    result = mail_preflight.report()
    assert result["database_reachable"] is True
    assert result["mail_schema_ready"] is True
    assert result["error"] == "independent_recovery_evidence_missing"
    assert result["database_source"] == "fallback_override"
    assert result["target_mapping_proven"] is False
    assert result["recovery_point_verified"] is False
    assert result["live_migration_authorized"] is False
    assert result["release_ready"] is False
    assert all("://" not in str(value) for value in result.values())


def test_preflight_does_not_query_mail_when_base_is_unready(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"reachable": False, "initialized": False})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("Mail check must not execute")))
    result = mail_preflight.report()
    assert result["error"] == "base_postgres_not_ready"
    assert result["mail_schema_ready"] is False


def test_preflight_redacts_database_failures(monkeypatch):
    _sources(monkeypatch)
    def fail():
        raise RuntimeError("postgres://username:secret@host/db")
    monkeypatch.setattr(postgres_db, "postgres_status", fail)
    result = mail_preflight.report()
    assert result["error"] == "mail_preflight_unavailable"
    assert "secret" not in str(result)
    assert result["release_ready"] is False


def test_preflight_rejects_a_secret_shaped_source_before_reading_db(monkeypatch):
    _sources(monkeypatch, source="postgres://user:secret@host/private")
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("must not connect")))
    result = mail_preflight.report()
    assert result["error"] == "database_selection_unavailable"
    assert "secret" not in str(result)
    assert result["target_mapping_proven"] is False


def test_preflight_redacts_failure_in_source_resolution(monkeypatch):
    _sources(monkeypatch)
    def fail():
        raise RuntimeError("postgres://user:secret@host/private")
    monkeypatch.setattr(postgres_db, "database_source", fail)
    result = mail_preflight.report()
    assert result["error"] == "mail_preflight_unavailable"
    assert "secret" not in str(result)
    assert result["database_source"] == "unverified"
    assert result["release_ready"] is False


def test_preflight_reachable_flag_is_required_before_mail_lookup(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"reachable": False, "initialized": True})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("must not query Mail")))
    result = mail_preflight.report()
    assert result["base_schema_ready"] is True
    assert result["database_reachable"] is False
    assert result["error"] == "base_postgres_not_ready"
    assert result["release_ready"] is False


def test_preflight_rejects_source_change_before_mail_lookup(monkeypatch):
    _sources(monkeypatch, source="primary_override")
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"source": "fallback_override",
                                 "reachable": True, "initialized": True})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("must not query Mail")))
    result = mail_preflight.report()
    assert result["error"] == "database_source_changed_during_preflight"
    assert result["mail_schema_ready"] is False
    assert result["release_ready"] is False


def test_preflight_rejects_base_checksum_mismatch_before_mail_lookup(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"source": "primary_override",
                                 "reachable": True, "initialized": True,
                                 "checksum_mismatches": ["0003_product_governance"]})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: (_ for _ in ()).throw(
                            AssertionError("must not query Mail")))
    result = mail_preflight.report()
    assert result["error"] == "base_migration_checksum_mismatch"
    assert result["mail_schema_ready"] is False
    assert result["release_ready"] is False


def test_preflight_rejects_authority_switch_after_mail_inspection(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"source": "primary_override",
                                 "reachable": True, "initialized": True})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: {"schema_ready": True, "error": None})
    calls = iter(("primary", "fallback"))
    monkeypatch.setattr(postgres_db, "database_authority", lambda: next(calls))
    result = mail_preflight.report()
    assert result["error"] == "database_selection_changed_during_preflight"
    assert result["mail_schema_ready"] is False
    assert result["release_ready"] is False


def test_preflight_rejects_source_switch_after_mail_inspection(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(postgres_db, "postgres_status",
                        lambda: {"source": "primary_override",
                                 "reachable": True, "initialized": True})
    monkeypatch.setattr(mail_migration, "schema_status",
                        lambda: {"schema_ready": True, "error": None})
    calls = iter(("primary_override", "fallback_override"))
    monkeypatch.setattr(postgres_db, "database_source", lambda: next(calls))
    result = mail_preflight.report()
    assert result["error"] == "database_selection_changed_during_preflight"
    assert result["mail_schema_ready"] is False
    assert result["target_mapping_proven"] is False
    assert result["recovery_point_verified"] is False



def test_independent_recovery_evidence_is_explicit_and_not_auto_attested(
    monkeypatch,
):
    _sources(monkeypatch)
    monkeypatch.setattr(
        postgres_db, "postgres_status",
        lambda: {"source": "primary_override", "reachable": True,
                 "initialized": True},
    )
    monkeypatch.setattr(
        mail_migration, "schema_status",
        lambda: {"schema_ready": True, "error": None},
    )
    result = mail_preflight.report()
    required = result["independent_release_evidence_required"]
    assert required == [
        "service_to_database_target_mapping",
        "backup_owner_and_source_target_match",
        "independent_backup_integrity_verification",
        "isolated_restore_completion_and_readback",
        "restore_timestamp_and_operator_attestation",
        "founder_release_approval",
    ]
    assert len(required) == len(set(required))
    assert result["mail_schema_ready"] is True
    assert result["error"] == "independent_recovery_evidence_missing"
    assert result["independent_release_evidence_verified"] is False
    assert result["target_mapping_proven"] is False
    assert result["recovery_point_verified"] is False
    assert result["live_migration_authorized"] is False
    assert result["release_ready"] is False
    assert all("://" not in str(value) for value in result.values())


def test_recovery_evidence_never_autoverifies_when_preflight_unavailable(
    monkeypatch,
):
    _sources(monkeypatch, configured=False)
    monkeypatch.setattr(
        postgres_db, "postgres_status",
        lambda: (_ for _ in ()).throw(
            AssertionError("unconfigured must not touch database")
        ),
    )
    result = mail_preflight.report()
    assert len(result["independent_release_evidence_required"]) == 6
    assert result["independent_release_evidence_verified"] is False
    assert result["recovery_point_verified"] is False
    assert result["release_ready"] is False


def test_preflight_preserves_specific_schema_error_over_recovery_hold(
    monkeypatch,
):
    _sources(monkeypatch)
    monkeypatch.setattr(
        postgres_db, "postgres_status",
        lambda: {"source": "primary_override", "reachable": True,
                 "initialized": True},
    )
    monkeypatch.setattr(
        mail_migration, "schema_status",
        lambda: {"schema_ready": False,
                 "error": "mail_migration_checksum_mismatch"},
    )
    result = mail_preflight.report()
    assert result["error"] == "mail_migration_checksum_mismatch"
    assert result["mail_schema_ready"] is False
    assert result["recovery_point_verified"] is False
    assert result["release_ready"] is False


def test_preflight_redacts_unrecognised_mail_schema_error(monkeypatch):
    _sources(monkeypatch)
    monkeypatch.setattr(
        postgres_db, "postgres_status",
        lambda: {"source": "primary_override", "reachable": True,
                 "initialized": True},
    )
    monkeypatch.setattr(
        mail_migration, "schema_status",
        lambda: {"schema_ready": True,
                 "error": "postgres://private:password@host/mail"},
    )
    result = mail_preflight.report()
    assert result["error"] == "mail_preflight_unavailable"
    assert result["mail_schema_ready"] is False
    assert result["recovery_point_verified"] is False
    assert result["release_ready"] is False
    assert "password" not in str(result)
