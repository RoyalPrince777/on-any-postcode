from pathlib import Path

from mission_control import brain, link_realtime

ROOT = Path(__file__).resolve().parents[1]


def test_oap_data_and_intelligence_names_are_canonical_for_presentation():
    assert link_realtime.OAP_DATA_NAME == "OAP Data"
    assert link_realtime.OAP_INTELLIGENCE_NAME == "OAP Intelligence"

    call = next(item for item in link_realtime.REALTIME_CAPABILITIES if item["id"] == "call")
    face_up = next(
        item for item in link_realtime.REALTIME_CAPABILITIES if item["id"] == "face_up"
    )
    assert "call_audit_oapdata" in call["requires"]
    assert "call_audit_oapdata" in face_up["requires"]
    assert "call_audit_metadata" not in call["requires"]
    assert "call_audit_metadata" not in face_up["requires"]


def test_realtime_contract_requires_first_party_transport():
    assert link_realtime.RUNTIME_GATES["first_party_realtime_transport"] is True
    assert link_realtime.RUNTIME_GATES["external_realtime_provider_required"] is False
    assert link_realtime.OAP_MOTION_SYSTEM["ownership"] == "first_party"
    assert link_realtime.OAP_MOTION_SYSTEM["external_emoji_provider_required"] is False


def test_public_brain_uses_oap_data_and_oap_intelligence_language(monkeypatch):
    monkeypatch.setattr(
        brain,
        "db_status",
        lambda: {"brain_runtime_initialized": False, "initialized": False},
    )
    monkeypatch.setattr(
        brain,
        "validate_architecture",
        lambda: {"checks": {"registry_ready_for_activation": False}},
    )

    status = brain.get_public_brain_status()
    serialized = repr(status)
    assert "OAP Intelligence biological regions" in serialized
    assert "OAP Intelligence Runtime" in serialized
    assert "private OAP Data" in serialized
    assert "private metadata" not in serialized


def test_naming_law_keeps_metadata_compatibility_only():
    notes = (ROOT / "docs" / "OAP_CORE_RENAME_NOTES.md").read_text(encoding="utf-8")
    assert "OAP Data" in notes
    assert "OAP Intelligence" in notes
    assert "metadata` is legacy/technical compatibility language only" in notes
    assert "No external realtime provider is required" in notes
