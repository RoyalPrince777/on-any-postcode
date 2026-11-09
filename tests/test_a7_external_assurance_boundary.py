"""A7 external references must not be mistaken for independently proven assurances."""

from unittest.mock import MagicMock

from mission_control import a7_certification


def test_a7_external_aggregates_require_independent_verification(monkeypatch):
    from mission_control import postgres_db

    monkeypatch.setattr(postgres_db, "configured", lambda: True)
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (0,) * 10
    ctx = MagicMock()
    ctx.__enter__.return_value = connection
    monkeypatch.setattr(postgres_db, "connect", lambda *, readonly=False: ctx)

    result = a7_certification._production_counts()

    assert result["store_reachable"] is True
    sql = connection.execute.call_args.args[0]
    assert sql.count("independent_verification_passed") == 3
    assert result["a6_independent_proof"] == 0
    assert result["a7_external_audit"] == 0
    assert result["a7_legal_compliance"] == 0


def test_recorded_reference_cannot_claim_independent_verification():
    sql = a7_certification._count_independently_verified_action_sql(
        a7_certification.A7_EXTERNAL_AUDIT_ACTION
    )
    assert "metadata->>'independent_verification_passed'='true'" in sql
    assert "metadata->>'passed'='true'" in sql


def test_founder_reference_receipt_is_recorded_but_never_passed(monkeypatch):
    from mission_control import approval_service, authority, postgres_db

    conn = MagicMock()
    ctx = MagicMock()
    ctx.__enter__.return_value = conn
    monkeypatch.setattr(postgres_db, "connect", lambda: ctx)
    monkeypatch.setattr(
        authority, "require_human_authority",
        lambda connection, identity: {"authority_level": 0},
    )
    recorded = {}
    monkeypatch.setattr(
        approval_service, "_write_audit",
        lambda connection, **kwargs: recorded.update(kwargs),
    )

    receipt = a7_certification.record_evidence_reference(
        identity_id="00000000-0000-0000-0000-000000000001",
        assurance="a6_operation_approval",
        evidence_ref="founder-submitted-reference",
        evidence_hash="a" * 64,
        issuer="Founder",
        scope="A6 approval evidence review",
        attestor_type="HUMAN_AUTHORITY",
    )
    assert receipt["recorded"] is True
    assert receipt["assurance_passed"] is False
    assert receipt["execution_granted"] is False
    assert recorded["metadata"]["reference_recorded"] is True
    assert recorded["metadata"]["passed"] is False
    assert recorded["metadata"]["independent_verification_passed"] is False
    conn.commit.assert_called_once()
