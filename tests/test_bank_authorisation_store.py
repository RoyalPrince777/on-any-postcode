from mission_control import bank_authorisation_store


def test_bank_evidence_schema_requires_explicit_approval():
    try:
        bank_authorisation_store.init_schema()
    except RuntimeError as exc:
        assert "Explicit human approval required" in str(exc)
    else:
        raise AssertionError("bank evidence schema must fail closed without --yes")


def test_bank_evidence_dry_run_does_not_claim_schema_ready():
    result = bank_authorisation_store.init_schema(assume_yes=True, dry_run=True)

    assert result["dry_run"] is True
    assert result["schema_ready"] is False
    assert result["migration"] == "bank_authorisation_evidence_v1"


def test_bank_evidence_status_requires_known_category_and_reference():
    try:
        bank_authorisation_store.record_evidence(
            category="invented_category",
            status="DRAFT",
            evidence_reference="ref",
        )
    except ValueError as exc:
        assert str(exc) == "unknown_bank_evidence_category"
    else:
        raise AssertionError("unknown evidence category must be rejected")


def test_reviewed_or_accepted_evidence_requires_reviewer_before_database_access():
    try:
        bank_authorisation_store.record_evidence(
            category="legal_entity_and_ownership",
            status="ACCEPTED",
            evidence_reference="company-proof",
        )
    except ValueError as exc:
        assert str(exc) == "bank_evidence_reviewer_required"
    else:
        raise AssertionError("accepted evidence must require reviewer")



def test_bank_evidence_boot_migration_is_explicit_off_by_default_and_fail_closed():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "gunicorn.conf.py"
    ).read_text(encoding="utf-8")

    assert "OAP_BANK_EVIDENCE_MIGRATION_ON_BOOT" in source
    assert '== "true"' in source
    assert "init_bank_evidence_schema(assume_yes=True)" in source
    assert "oap_bank_authorisation_evidence_migration_applied" in source
    assert '"regulated_execution_enabled": False' in source
    assert '"regulator_authorisation_granted": False' in source

    gated = source[
        source.index("OAP_BANK_EVIDENCE_MIGRATION_ON_BOOT"):
        source.index("from mission_control.bank_authorisation_store import schema_status")
    ]
    assert "except Exception" not in gated


def test_bank_evidence_runtime_emits_read_only_schema_readiness_receipt():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "gunicorn.conf.py"
    ).read_text(encoding="utf-8")

    assert "oap_bank_authorisation_evidence_schema_readiness" in source
    assert "bank_evidence_schema_status()" in source
    assert '"regulated_execution_enabled": False' in source
    assert '"regulator_authorisation_granted": False' in source
    assert '"human_authority_final": True' in source
