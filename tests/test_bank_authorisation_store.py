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
