from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "mission_control" / "static" / "smi_chat_final.js"
RUNTIME = ROOT / "mission_control" / "smi_chat_runtime_core.py"


def test_smi_page_renders_server_generated_auto_vote_board():
    text = JS.read_text(encoding="utf-8")
    for marker in (
        "SMI AUTO · Evidence Vote Board",
        "smi-auto-review-card",
        "result.auto_review",
        "result.active_reviewers",
        "Votes advise only; they grant no authority.",
    ):
        assert marker in text


def test_smi_runtime_routes_auto_mode_and_named_reviewers():
    text = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        '"SMI_AUTO"',
        'smi_auto.selected_review_roles',
        'brain["active_reviewers"]',
        'smi_auto.build_evidence_vote_board',
        '"auto_review": auto_review',
    ):
        assert marker in text


def test_founder_protocol_review_requires_verified_authority_and_guardian(monkeypatch):
    from mission_control import smi_chat_runtime_core

    calls = []
    monkeypatch.setattr(
        smi_chat_runtime_core.smi_auto, "capability_review_route",
        lambda message: calls.append(message) or {"status": "PROPOSED_UNVERIFIED"},
    )
    founder = {
        "is_human_authority": True,
        "authority_level": 0,
        "permissions": ("APPROVE_RECOMMENDATION",),
    }
    review = smi_chat_runtime_core._founder_protocol_review
    assert review("protocol: guardian", founder, "PASSED") is not None
    for record in (
        {},
        {**founder, "is_human_authority": False},
        {**founder, "authority_level": False},
        {**founder, "authority_level": 5},
        {**founder, "permissions": ()},
    ):
        assert review("protocol: guardian", record, "PASSED") is None
    assert review("protocol: guardian", founder, "BLOCKED") is None
    assert review("protocol: guardian", founder, "PASSED", has_media=True) is None
    assert review("explain protocol: guardian", founder, "PASSED") is None
    assert calls == ["protocol: guardian"]


def test_founder_protocol_review_response_exposes_unknown_not_fake_green(monkeypatch):
    from mission_control import smi_chat_runtime_core
    from oap.smi import protocol_selection

    monkeypatch.setattr(protocol_selection, "which", lambda name: "/private/bin/opa")
    plan = smi_chat_runtime_core.smi_auto.capability_review_route("protocol: guardian")
    response = smi_chat_runtime_core._protocol_review_response(plan)
    assert "OPA: Executable detected" in response
    assert "functional status Unknown" in response
    assert "/private/bin/opa" not in response
    assert "No candidate executed or benchmarked" in response
    assert "unknown protocol" in smi_chat_runtime_core._protocol_review_response(
        {"status": "UNRECOGNISED"}
    )
