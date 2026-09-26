from mission_control import organism


def test_major_capabilities_have_canonical_anatomy_owners():
    items = {item["id"]: item for item in organism.CAPABILITY_ANATOMY}
    expected = {
        "continuity_intelligence",
        "workspace_orchestrator",
        "oap_data_builder",
        "live_build_preview",
        "rights_provenance",
        "realtime_presence",
        "generative_music",
    }
    assert set(items) == expected
    for item in items.values():
        assert item["brain_regions"]
        assert item["body_owner"]
        assert item["protection_owner"]
        assert item["memory_owner"]
        assert item["execution_owner"]
        assert item["status"] in {"partial", "missing", "ready"}
        assert item["missing"]

    assert items["continuity_intelligence"]["brain_regions"] == (
        "hippocampus", "occipital_lobe", "cerebellum"
    )
    assert items["workspace_orchestrator"]["brain_regions"] == (
        "thalamus", "frontal_lobe", "corpus_callosum"
    )
    assert items["generative_music"]["body_owner"] == "OAP Music"
    assert items["generative_music"]["status"] == "missing"
    assert items["oap_data_builder"]["consequential_execution"] is True
    assert items["rights_provenance"]["consequential_execution"] is True


def test_public_anatomy_projects_capability_layer_without_new_brain():
    projection = organism.get_public_anatomy()
    assert projection["capability_anatomy"] == organism.CAPABILITY_ANATOMY
    assert projection["validation"]["checks"]["brain_count"] == 1
