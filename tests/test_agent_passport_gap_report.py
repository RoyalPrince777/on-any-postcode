from mission_control.agent_passport_gap_report import registry_passport_gap_report


def test_passport_gap_report_preserves_registry_and_authority():
    report = registry_passport_gap_report()
    by_name = {item["name"]: item for item in report["entries"]}
    assert report["registry_count"] == report["registry_target"]
    for name in ("Gorilla", "Fox", "Baloo"):
        assert by_name[name]["registered"] is True
        assert by_name[name]["agent_id"]
    for name in ("Mouse", "Secretary", "Tigress", "Lioness"):
        assert by_name[name]["registered"] is False
        assert by_name[name]["agent_id"] is None
    assert all(not item["runtime_verified"] for item in by_name.values())
    assert all(not item["passport_verified"] for item in by_name.values())
    assert report["founder_final_required"] is True
    assert report["execution_authorised"] is False
