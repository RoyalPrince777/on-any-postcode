from mission_control import company_intelligence_evidence_store as store


OWNER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_build_receipt_is_owner_scoped_and_hash_chained():
    first = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="CI-001",
        state="PASS",
        evidence_reference="oap:test:first",
    )
    second = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="CI-002",
        state="FAIL",
        evidence_reference="oap:test:second",
        failure_reason="Runtime mismatch.",
        recovery_requirement="Restore last known-good state.",
        previous_receipt_hash=first["receipt_hash"],
    )

    assert first["previous_receipt_hash"] == store.GENESIS_HASH
    assert second["previous_receipt_hash"] == first["receipt_hash"]
    assert len(first["receipt_hash"]) == 64
    assert len(second["receipt_hash"]) == 64


def test_receipt_chain_verifies_and_tampering_fails():
    first = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="CI-001",
        state="PASS",
        evidence_reference="oap:test:first",
    )
    second = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="CI-002",
        state="PASS",
        evidence_reference="oap:test:second",
        previous_receipt_hash=first["receipt_hash"],
    )

    good = store.verify_receipt_chain([first, second])
    tampered = dict(second)
    tampered["state"] = "FAIL"
    bad = store.verify_receipt_chain([first, tampered])

    assert good["chain_verified"] is True
    assert good["receipt_count"] == 2
    assert bad["chain_verified"] is False


def test_unknown_or_unreferenced_receipts_are_rejected():
    try:
        store.build_receipt(
            owner_identity_id=OWNER,
            check_id="CI-999",
            state="PASS",
            evidence_reference="oap:test",
        )
    except ValueError as exc:
        assert str(exc) == "invalid_check_id"
    else:
        raise AssertionError("unknown check must fail")

    try:
        store.build_receipt(
            owner_identity_id=OWNER,
            check_id="CI-001",
            state="PASS",
            evidence_reference="",
        )
    except ValueError as exc:
        assert str(exc) == "invalid_evidence_reference"
    else:
        raise AssertionError("missing evidence reference must fail")


def test_status_never_claims_full_green_from_store_existence(monkeypatch):
    monkeypatch.setattr(
        store,
        "schema_status",
        lambda: {
            "database_reachable": True,
            "evidence_table_ready": True,
            "schema_ready": True,
            "error": None,
        },
    )
    result = store.status()

    assert result["append_only"] is True
    assert result["hash_chained"] is True
    assert result["owner_scoped"] is True
    assert result["execution_authority_granted"] is False
    assert result["full_green"] is False
