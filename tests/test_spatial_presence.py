from mission_control import spatial_presence, technology_intelligence
from oap.smi.agi_core import AGICore


def test_spatial_presence_software_ready_and_future_radio_fail_closed(monkeypatch):
    for name in (
        "OAP_SPATIAL_CAPTURE_EVIDENCE",
        "OAP_SPATIAL_DISPLAY_EVIDENCE",
        "OAP_SPATIAL_RADIO_EVIDENCE",
        "OAP_6G_RADIO_EVIDENCE",
    ):
        monkeypatch.delenv(name, raising=False)
    status = spatial_presence.spatial_presence_status()
    assert status["software_ready"] is True
    assert status["oap_experimental_cmwave_ghz"] == (7.0, 21.0)
    assert status["oap_7_21_is_internal_research_envelope"] is True
    assert status["oap_7_21_claimed_final_6g_standard"] is False
    assert status["capture_hardware_proven"] is False
    assert status["spatial_display_hardware_proven"] is False
    assert status["oap_7_21_radio_hardware_proven"] is False
    assert status["live_6g_network_proven"] is False
    assert status["biometric_identity_profile"] is False
    assert status["autonomous_radio_control"] is False


def test_semantic_compression_degrades_without_fake_terabit_requirement():
    ultra = spatial_presence.semantic_compression_plan(available_mbps=800, latency_ms=20)
    weak = spatial_presence.semantic_compression_plan(available_mbps=8, latency_ms=180)
    assert ultra["profile"] == "spatial_ultra"
    assert ultra["raw_point_cloud_required_end_to_end"] is False
    assert weak["profile"] == "face_up_2d_fallback"
    assert weak["semantic_compression"] is True


def test_spatial_session_requires_consent_and_minimises_matrix():
    try:
        spatial_presence.create_session({"participant_ref": "member-a"})
    except PermissionError as exc:
        assert str(exc) == "spatial_capture_consent_required"
    else:
        raise AssertionError("consent gate did not fail closed")

    result = spatial_presence.create_session(
        {
            "participant_ref": "member-a",
            "consent": True,
            "display": "xr_headset",
            "capture_adapter": "multi_view_rgbd",
            "available_mbps": 150,
            "latency_ms": 50,
            "available_transports": ["5g", "oap_7_21_research"],
            "research_radio_evidence": True,
        }
    )
    assert result["accepted"] is True
    assert result["session"]["transport"] == "5g"
    assert result["matrix_projection"]["raw_media"] is False
    assert result["matrix_projection"]["biometric_identity"] is False
    assert result["matrix_projection"]["precise_location"] is None


def test_smi_routes_holographic_and_7_21_requests_to_technology_and_matrix():
    route = AGICore().route("Build Face Up Spatial holographic telepresence over 7-21 GHz")
    assert "technology" in route["domain_ids"]
    assert "matrix" in route["domain_ids"]


def test_technology_intelligence_exposes_spatial_presence_without_new_world():
    status = technology_intelligence.technology_intelligence_status()
    ids = {item["id"] for item in status["connectivity"]["capabilities"]}
    assert "spatial_presence" in ids
    assert status["face_up_spatial_software_ready"] is True
    assert status["oap_experimental_cmwave_ghz"] == (7.0, 21.0)
    assert status["brain_count"] == 0
    assert status["intelligence_world_count_added"] == 0
    assert status["autonomous_radio_control"] is False
    assert status["human_authority_final"] is True


def test_founder_face_up_spatial_dashboard(client):
    response = client.get("/mission/isac-spatial/presence")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Face Up Spatial" in page
    assert "7–21 GHz" in page
    assert "Guardian Presence" in page
    assert "NOT CLAIMED" in page
