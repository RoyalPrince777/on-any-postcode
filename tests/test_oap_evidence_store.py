from mission_control import oap_evidence_store as store


OWNER = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def test_oap_receipts_hash_chain_across_domains():
    first = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="OAP-001",
        state="PASS",
        source_system="infrastructure",
        evidence_reference="oap:test:infra",
    )
    second = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="OAP-051",
        state="PASS",
        source_system="trust_identity",
        evidence_reference="oap:test:trust",
        previous_receipt_hash=first["receipt_hash"],
    )

    result = store.verify_chain([first, second])
    assert result["chain_verified"] is True
    assert result["receipt_count"] == 2


def test_oap_receipt_tampering_fails_chain():
    first = store.build_receipt(
        owner_identity_id=OWNER,
        check_id="OAP-001",
        state="PASS",
        source_system="infrastructure",
        evidence_reference="oap:test:infra",
    )
    tampered = dict(first)
    tampered["source_system"] = "other"

    assert store.verify_chain([tampered])["chain_verified"] is False


def test_oap_store_status_never_grants_execution():
    result = store.status()

    assert result["append_only"] is True
    assert result["hash_chained"] is True
    assert result["whole_company_scope"] is True
    assert result["execution_authority_granted"] is False
    assert result["full_green"] is False
