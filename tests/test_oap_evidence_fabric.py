from mission_control import oap_evidence_fabric as fabric


def test_whole_company_fabric_is_exactly_700_unique_checks():
    cells = fabric.catalogue()

    assert len(fabric.OAP_DOMAINS) == 14
    assert len(fabric.INTELLIGENCE_LENSES) == 10
    assert len(fabric.PROOF_CLASSES) == 5
    assert len(cells) == 700
    assert len({cell["check_id"] for cell in cells}) == 700
    assert cells[0]["check_id"] == "OAP-001"
    assert cells[-1]["check_id"] == "OAP-700"


def test_whole_company_fabric_fails_closed_when_empty():
    result = fabric.snapshot()

    assert result["counts"]["UNKNOWN"] == 700
    assert result["proven_count"] == 0
    assert result["green_gate_passed"] is False
    assert result["full_green"] is False
    assert all(
        domain["green"] is False
        for domain in result["domain_status"].values()
    )


def test_receipt_requires_source_system_reference_and_timestamp():
    result = fabric.snapshot(
        (
            {
                "check_id": "OAP-001",
                "state": "PASS",
                "source_system": "infrastructure",
                "evidence_reference": "oap:test:runtime",
                "observed_at": "2026-10-02T18:00:00+00:00",
            },
            {
                "check_id": "OAP-002",
                "state": "PASS",
                "source_system": "",
                "evidence_reference": "oap:test:missing-source",
                "observed_at": "2026-10-02T18:00:00+00:00",
            },
        )
    )

    assert result["counts"]["PASS"] == 1
    assert result["counts"]["UNKNOWN"] == 699
    assert result["valid_receipt_count"] == 1
    assert result["invalid_receipt_count"] == 1


def test_domain_status_prevents_one_system_from_hiding_another():
    receipts = tuple(
        {
            "check_id": f"OAP-{index:03d}",
            "state": "PASS",
            "source_system": "infrastructure",
            "evidence_reference": f"oap:test:{index}",
            "observed_at": "2026-10-02T18:00:00+00:00",
        }
        for index in range(1, 51)
    )
    result = fabric.snapshot(receipts)

    assert result["domain_status"]["infrastructure"]["green"] is True
    assert result["domain_status"]["trust_identity"]["green"] is False
    assert result["green_gate_passed"] is False
    assert result["proven_count"] == 50


def test_full_green_requires_every_cell_and_founder_final():
    receipts = tuple(
        {
            "check_id": f"OAP-{index:03d}",
            "state": "PASS",
            "source_system": "oap-runtime",
            "evidence_reference": f"oap:test:{index}",
            "observed_at": "2026-10-02T18:00:00+00:00",
        }
        for index in range(1, 701)
    )

    gated = fabric.snapshot(receipts)
    final = fabric.snapshot(receipts, founder_final_recorded=True)

    assert gated["green_gate_passed"] is True
    assert gated["full_green"] is False
    assert final["full_green"] is True
