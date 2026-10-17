from mission_control import company_intelligence_evidence_registry as registry


def test_registry_has_exactly_700_stable_unique_cells():
    cells = registry.cell_catalogue()

    assert len(cells) == 700
    assert len({cell["check_id"] for cell in cells}) == 700
    assert cells[0]["check_id"] == "CI-001"
    assert cells[-1]["check_id"] == "CI-700"


def test_missing_receipts_fail_closed_to_unknown():
    result = registry.snapshot()

    assert result["protocol_check_count"] == 700
    assert result["counts"]["UNKNOWN"] == 700
    assert result["proven_count"] == 0
    assert result["green_gate_passed"] is False
    assert result["full_green"] is False


def test_only_timestamped_evidence_can_advance_a_cell():
    result = registry.snapshot(
        (
            {
                "check_id": "CI-001",
                "state": "PASS",
                "evidence_reference": "oap:test:source",
                "observed_at": "2026-10-02T18:00:00+00:00",
            },
            {
                "check_id": "CI-002",
                "state": "PASS",
                "evidence_reference": "",
                "observed_at": "2026-10-02T18:00:00+00:00",
            },
        )
    )

    assert result["counts"]["PASS"] == 1
    assert result["counts"]["UNKNOWN"] == 699
    assert result["valid_receipt_count"] == 1
    assert result["invalid_receipt_count"] == 1
    assert result["green_gate_passed"] is False


def test_latest_valid_receipt_wins_without_erasing_lineage_input():
    result = registry.snapshot(
        (
            {
                "check_id": "CI-007",
                "state": "PASS",
                "evidence_reference": "oap:test:old",
                "observed_at": "2026-10-02T17:00:00+00:00",
            },
            {
                "check_id": "CI-007",
                "state": "FAIL",
                "evidence_reference": "oap:test:new",
                "observed_at": "2026-10-02T18:00:00+00:00",
                "failure_reason": "Regression detected.",
                "recovery_requirement": "Restore the last known-good state.",
            },
        )
    )

    cell = result["cells"][6]
    assert cell["check_id"] == "CI-007"
    assert cell["state"] == "FAIL"
    assert cell["evidence_reference"] == "oap:test:new"
    assert cell["failure_reason"] == "Regression detected."
    assert result["counts"]["FAIL"] == 1


def test_700_resolved_cells_still_require_founder_final_for_full_green():
    receipts = tuple(
        {
            "check_id": f"CI-{index:03d}",
            "state": "PASS",
            "evidence_reference": f"oap:test:{index}",
            "observed_at": "2026-10-02T18:00:00+00:00",
        }
        for index in range(1, 701)
    )

    gated = registry.snapshot(receipts)
    final = registry.snapshot(receipts, founder_final_recorded=True)

    assert gated["green_gate_passed"] is True
    assert gated["full_green"] is False
    assert final["green_gate_passed"] is True
    assert final["full_green"] is True


def test_na_requires_real_evidence_and_is_not_counted_as_proven():
    result = registry.snapshot(
        (
            {
                "check_id": "CI-010",
                "state": "N/A",
                "evidence_reference": "oap:test:scope-exclusion",
                "observed_at": "2026-10-02T18:00:00+00:00",
            },
        )
    )

    assert result["counts"]["N/A"] == 1
    assert result["resolved_count"] == 1
    assert result["proven_count"] == 0
    assert result["green_gate_passed"] is False
