from mission_control import essential_life_systems, oap_library


def test_essential_life_systems_registry_is_complete_and_truth_bounded():
    validation = essential_life_systems.validate_registry()

    assert validation["passed"] is True
    assert validation["systems"] == 10
    assert validation["bands"] == 7
    assert validation["monitor_types"] == 10
    assert validation["live_telemetry_claimed"] is False


def test_every_system_has_monitoring_and_one_resilience_band():
    system_ids = {item["id"] for item in essential_life_systems.SYSTEMS}
    band_members = [
        system_id
        for band in essential_life_systems.BANDS
        for system_id in band["systems"]
    ]

    assert set(band_members) == system_ids
    assert len(band_members) == len(system_ids)
    assert all(item["monitors"] for item in essential_life_systems.SYSTEMS)


def test_smi_snapshot_keeps_registry_evidence_separate_from_live_status():
    snapshot = essential_life_systems.smi_snapshot()

    assert snapshot["truth_mode"] is True
    assert snapshot["status"] == "registry_ready"
    assert snapshot["views"] == ("Now", "Next", "Recover")
    assert snapshot["live_telemetry"] is False
    assert all(system["status"] == "unverified" for system in snapshot["systems"])
    assert all(system["evidence_state"] == "registry_only" for system in snapshot["systems"])


def test_dependency_graph_captures_cascading_essential_system_risk():
    edges = {
        (edge["source"], edge["target"])
        for edge in essential_life_systems.dependency_edges()
    }

    assert ("energy", "water") in edges
    assert ("energy", "communication") in edges
    assert ("movement", "food") in edges
    assert ("communication", "health") in edges


def test_library_surfaces_essential_life_systems_without_exposing_founder_assets():
    collection = next(
        item
        for item in oap_library.COLLECTIONS
        if item["id"] == "essential-life-systems"
    )

    assert collection["access"] == "public"
    assert collection["route"] == "/library/essential-life-systems"
    assert oap_library.validate_catalog()["founder_assets_exposed"] is False
