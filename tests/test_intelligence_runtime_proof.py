from mission_control import intelligence_runtime_proof

CANONICAL_WORLD_IDS = (
    "earth",
    "language",
    "life",
    "movement",
    "civic",
    "civilisation",
    "matrix",
)


def test_runtime_proof_keeps_seven_worlds_and_three_claim_levels_separate():
    current = intelligence_runtime_proof.status()
    worlds = {item["id"]: item for item in current["worlds"]}

    assert current["world_count"] == 7
    assert current["world_ids"] == CANONICAL_WORLD_IDS
    assert current["network_calls_made"] is False
    assert current["universal_runtime_green"] is False
    assert current["execution_granted"] is False
    assert current["approval_granted"] is False
    assert current["human_authority_final"] is True

    assert worlds["earth"]["bounded_runtime_ready"] is True
    assert worlds["earth"]["full_runtime_ready"] is False

    assert worlds["language"]["bounded_runtime_ready"] is True
    assert worlds["language"]["full_runtime_ready"] is False

    assert worlds["movement"]["bounded_runtime_ready"] is True
    assert worlds["movement"]["live_external_ready"] is False
    assert worlds["movement"]["full_runtime_ready"] is False


def test_validated_worlds_can_be_bounded_without_inheriting_full_green():
    worlds = {
        item["id"]: item for item in intelligence_runtime_proof.status()["worlds"]
    }

    for world_id in ("life", "civic", "civilisation"):
        assert worlds[world_id]["bounded_runtime_ready"] is True
        assert worlds[world_id]["live_external_ready"] is False
        assert worlds[world_id]["full_runtime_ready"] is False
        assert worlds[world_id]["full_runtime_light"] == "🟣"


def test_owned_runtime_evidence_stays_separate_from_full_runtime():
    current = intelligence_runtime_proof.status()
    worlds = {item["id"]: item for item in current["worlds"]}
    cross = {item["id"]: item for item in current["cross_system"]}

    expected_ecosystem_live = bool(
        current["weather_provider_verified"]
        or current["infrastructure_runtime_verified"]
        or current["people_aggregate_verified"]
        or current["guardian_runtime_verified"]
    )
    assert cross["ecosystem"]["live_external_ready"] is expected_ecosystem_live
    assert cross["ecosystem"]["full_runtime_ready"] is False
    assert worlds["matrix"]["live_external_ready"] is current["infrastructure_runtime_verified"]
    assert current["universal_runtime_green"] is False


def test_cross_system_runtime_proof_keeps_provider_and_hardware_claims_gated():
    current = intelligence_runtime_proof.status()
    cross = {item["id"]: item for item in current["cross_system"]}

    assert tuple(cross) == (
        "ecosystem",
        "technology",
        "international_humanitarian",
        "multimodal",
    )
    assert cross["ecosystem"]["bounded_runtime_ready"] is True
    assert cross["ecosystem"]["full_runtime_ready"] is False
    assert cross["multimodal"]["bounded_runtime_ready"] is True
    assert cross["multimodal"]["live_external_ready"] is False
    assert cross["multimodal"]["full_runtime_ready"] is False
    assert cross["technology"]["full_runtime_ready"] is False
    assert cross["international_humanitarian"]["full_runtime_ready"] is False


def test_runtime_evidence_endpoint_is_founder_read_only(client):
    response = client.get("/mission/intelligence/runtime")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["component"] == "All Intelligence Runtime Proof"
    assert payload["world_count"] == 7
    assert payload["execution_granted"] is False
    assert payload["approval_granted"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_all_intelligence_dashboard_shows_runtime_proof_matrix(client):
    response = client.get("/mission/intelligence")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Runtime Proof Matrix" in page
    assert "bounded runtime" in page
    assert "live external proof" in page
    assert "full runtime" in page
    assert "Human Authority final" in page
