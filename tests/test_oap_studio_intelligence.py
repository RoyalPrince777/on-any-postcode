from pathlib import Path

from mission_control import smi_workbench, studio_intelligence

ROOT = Path(__file__).resolve().parents[1]


def test_studio_contract_is_smi_powered_and_governed():
    status = studio_intelligence.status()

    assert status["id"] == "oap-studio-intelligence"
    assert status["name"] == "OAP Studio Intelligence"
    assert status["powered_by"] == "SMI"
    assert status["tabs"] == [
        "Home",
        "Projects",
        "Bring In",
        "Create",
        "Shape",
        "Intelligence",
        "Rights",
        "Release",
        "Campaign",
        "Analyse",
        "Chronicle",
    ]
    assert status["pipeline"] == [
        "Create",
        "Shape",
        "Package",
        "Rights",
        "Release",
        "Distribute",
        "Campaign",
        "Analyse",
        "Chronicle",
    ]
    assert "Imagine" in status["creation_modes"]
    assert "Director" in status["intelligence_roles"]
    assert status["review_depths"] == [3, 7, 21]
    assert "Pulse Cut" in status["output_packs"]
    assert status["spot_placement"]["public_surface"] == "OAP Studio"
    assert status["spot_placement"]["private_engine"] == "OAP Studio Intelligence"
    governance = status["governance"]
    assert governance["human_authority_final"] is True
    assert governance["rights_proof_required"] is True
    assert governance["external_distribution_locked_until_proof"] is True
    assert governance["payment_authority_granted"] is False
    assert governance["publishing_authority_granted"] is False
    assert governance["execution_authority_granted"] is False


def test_studio_is_canonical_media_engine_for_smi_chat_capture():
    status = studio_intelligence.status()
    alignment = status["alignment"]

    assert "SMI Chat" in status["entry_points"]
    assert "camera" in status["capture_inputs"]
    assert "screen" in status["capture_inputs"]
    assert alignment["smi_chat_is_entry_surface"] is True
    assert alignment["studio_is_canonical_media_engine"] is True
    assert alignment["duplicate_studio_engine_allowed"] is False
    assert alignment["capture_does_not_grant_execution"] is True


def test_founder_workbench_exposes_studio_without_secrets(monkeypatch):
    monkeypatch.setattr(
        smi_workbench.smi_chat_runtime,
        "health",
        lambda: {"status": "yellow", "checks": {"database": False, "schema": False}},
    )

    payload = smi_workbench.get_workbench_status()
    studio = next(
        item for item in payload["capabilities"] if item["id"] == "oap-studio-intelligence"
    )

    assert studio["ready"] is True
    assert studio["powered_by"] == "SMI"
    assert "OAP Studio Intelligence mode" in studio["activation_prompt"]
    assert "OAP Studio Intelligence planning and preparation" in payload["runtime_gate"]["available"]


def test_smi_plus_menu_launches_studio():
    smi = (ROOT / "mission_control" / "templates" / "ollama_chat.html").read_text()

    assert "data-oap-studio" in smi or "dataset.oapStudio" in smi
    assert "OAP Studio Intelligence" in smi
    assert "launchStudio" in smi
    assert "activation_prompt" in smi


def test_studio_v2_lock_preserves_oap_boundaries_and_one_source_many_outputs():
    status = studio_intelligence.status()

    assert status["alignment"]["one_source_many_outputs"] is True
    assert status["alignment"]["studio_creates_destinations_publish"] is True
    assert status["alignment"]["public_studio_private_intelligence_separated"] is True
    assert status["studio_council"] == [
        "Director",
        "Producer",
        "Visual",
        "Sound",
        "Story",
        "Rights",
        "Release",
    ]
    assert "Chronicle Master" in status["output_packs"]
    assert "The Spot" in status["destinations"]
    assert status["governance"]["human_authority_final"] is True
    assert status["governance"]["publishing_authority_granted"] is False
    assert status["governance"]["execution_authority_granted"] is False


def test_studio_generation_system_is_multimodal_scene_built_and_governed():
    status = studio_intelligence.status()
    tools = {item["name"]: item for item in status["generation_tools"]}

    assert tools["Imagine"]["input"] == "text"
    assert tools["Imagine"]["output"] == "image"
    assert tools["Bring Alive"]["input"] == "image"
    assert tools["Bring Alive"]["output"] == "video"
    assert tools["Scene Builder"]["input"] == "text"
    assert tools["Motion Rework"]["input"] == "video"
    assert tools["Music Video Builder"]["input"] == "image_or_images_plus_music"
    assert tools["Music Video Builder"]["output"] == "music_video"

    assert status["video_durations"] == ["10s", "30s", "1m", "2m", "Scene", "Film"]
    assert "approved scenes" in status["long_form_rule"]
    assert "5:4" in status["aspect_ratios"]
    assert "Identity Lock" in status["consistency_locks"]
    assert "Product Lock" in status["consistency_locks"]
    assert "World Lock" in status["consistency_locks"]
    assert status["generation_governance"]["scene_card_required_for_text_to_video"] is True
    assert status["generation_governance"]["voice_clone_requires_consent"] is True
    assert status["generation_governance"]["automatic_publication_allowed"] is False
    assert status["generation_governance"]["human_authority_final"] is True
    assert status["chronicle_generation_fields"] == [
        "input", "settings", "source assets", "generated result", "rights status",
        "creator", "timestamp", "chosen version",
    ]


def test_music_video_builder_supports_picture_to_music_and_full_film_path():
    status = studio_intelligence.status()

    assert "Full Music Video" in status["music_video_types"]
    assert "Cinematic" in status["music_video_motion"]
    assert "Performance" in status["music_video_motion"]
    assert "Film" in status["video_durations"]
    assert status["generation_council"] == [
        "Director", "Visual", "Story", "Continuity", "Rights", "Release", "Guardian",
    ]
