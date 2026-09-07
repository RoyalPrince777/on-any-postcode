from __future__ import annotations

from mission_control import intelligence_lenses


def test_swot_short_command_routes_single_lens():
    routed = intelligence_lenses.route("SWOT The Link")

    assert routed["active"] is True
    assert routed["mode"] == "single"
    assert routed["lens_ids"] == ("swot",)
    assert routed["subject"] == "The Link"


def test_gap_intelligence_command_extracts_subject():
    routed = intelligence_lenses.route("Run Gap Intelligence on Maps")

    assert routed["active"] is True
    assert routed["lens_ids"] == ("gap",)
    assert routed["subject"] == "Maps"


def test_full_intelligence_uses_all_registered_lenses():
    routed = intelligence_lenses.route("Full Intelligence on SIKA")

    assert routed["active"] is True
    assert routed["mode"] == "full"
    assert routed["subject"] == "SIKA"
    assert tuple(routed["lens_ids"]) == intelligence_lenses.FULL_LENS_IDS
    assert len(routed["lens_ids"]) == 26


def test_core_intelligence_uses_decision_chain_without_every_deep_lens():
    routed = intelligence_lenses.route("Run Core Intelligence on OAP Maps")

    assert routed["active"] is True
    assert routed["mode"] == "core"
    assert tuple(routed["lens_ids"]) == intelligence_lenses.CORE_LENS_IDS
    assert routed["subject"] == "OAP Maps"


def test_generic_risk_question_does_not_force_intelligence_mode():
    routed = intelligence_lenses.route("What is the risk of a slow database query?")

    assert routed["active"] is False
    assert routed["lens_ids"] == ()


def test_provider_directive_preserves_governance_boundary():
    routed = intelligence_lenses.route("Run Risk Intelligence on The Link")
    directive = intelligence_lenses.provider_directive(routed)

    assert "Risk Intelligence" in directive
    assert "no approval" in directive
    assert "production mutation" in directive
    assert "Human Authority remains final" in directive


def test_public_route_never_grants_execution():
    public = intelligence_lenses.public_route("Run Readiness Intelligence on SIKA")

    assert public["active"] is True
    assert public["execution_granted"] is False
    assert public["human_authority_final"] is True
    assert public["lenses"] == ({"id": "readiness", "name": "Readiness Intelligence"},)
