from __future__ import annotations

from pathlib import Path

from mission_control import products, spot_step3_creator_safety_proof

ROOT = Path(__file__).resolve().parents[1]


def test_step3_required_capabilities_and_public_routes_are_present():
    capabilities = {
        str(item["id"]): dict(item)
        for item in products.SPOT_CAPABILITIES
    }

    for capability_id in (
        "creators",
        "music",
        "player",
        "radio",
        "distribution",
        "tv-media",
        "safety",
        "support",
    ):
        assert capability_id in capabilities

    assert products.get_public_spot_slug("creators") == "creators"
    assert products.get_public_spot_slug("music") == "music"
    assert products.get_public_spot_slug("player") == "player"
    assert products.get_public_spot_slug("radio") == "radio"
    assert products.get_public_spot_slug("distribution") == "distribution"
    assert products.get_public_spot_slug("tv-media") == "tv-media"
    assert products.get_public_spot_slug("safety") == "safety"
    assert products.get_public_spot_slug("support") == "support"


def test_step3_canonical_locks_remain_fail_closed():
    capabilities = {
        str(item["id"]): dict(item)
        for item in products.SPOT_CAPABILITIES
    }

    expected = {
        "creators": ("Certified Creator Identity", "publishing"),
        "music": ("rights proof", "Creator Identity", "Human Authority"),
        "player": ("youth-safe moderation", "rights"),
        "radio": ("licensing", "rights proof", "moderation"),
        "distribution": ("external", "legal routes"),
        "tv-media": ("Creator publishing workflow",),
        "safety": ("Authenticated reporting", "escalation"),
        "support": ("Safeguarding", "certification", "case privacy"),
    }
    for capability_id, terms in expected.items():
        blocked_by = capabilities[capability_id]["blocked_by"].casefold()
        for term in terms:
            assert term.casefold() in blocked_by


def test_step3_template_keeps_creator_and_support_truth_locks():
    template = (
        ROOT / "mission_control" / "templates" / "spot_capability.html"
    ).read_text(encoding="utf-8")

    for marker in (
        "does not claim Certified Creator Identity",
        "rights clearance or external publishing",
        "no public support form creates or exposes a safeguarding case",
        "Private case handling remains gated",
    ):
        assert marker in template


def test_step3_proof_never_claims_real_publish_or_case_creation():
    source = Path(
        spot_step3_creator_safety_proof.__file__
    ).read_text(encoding="utf-8")

    assert '"certified_creator_identity_created": False' in source
    assert '"media_published": False' in source
    assert '"external_distribution_performed": False' in source
    assert '"public_safeguarding_case_created": False' in source
    assert '"private_case_created": False' in source
    assert '"execution_authority_expanded": False' in source
    assert "authority.require_human_authority" in source
    assert "hrm_durable_receipt.persist_and_read_back" in source
    assert "approval_service._write_audit" in source


def test_step3_boot_trigger_is_explicit_and_fail_closed():
    source = (
        ROOT / "mission_control" / "__init__.py"
    ).read_text(encoding="utf-8")

    assert "OAP_SPOT_STEP3_PROOF_ON_BOOT" in source
    assert "OAP_SPOT_STEP3_PROOF_OPERATION_ID" in source
    assert "spot_step3_creator_safety_proof.run(" in source
    assert '"event": "oap_spot_step3_creator_safety_proof"' in source
    assert '"quarter": 75' in source
    assert '"media_published": False' in source
    assert '"external_distribution_performed": False' in source
    assert '"public_safeguarding_case_created": False' in source
    assert '"execution_authority_expanded": False' in source
