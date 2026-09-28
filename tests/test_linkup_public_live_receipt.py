import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_linkup_live_receipt_matches_the_immutable_release_contract():
    receipt = json.loads(
        (ROOT / "deploy" / "linkup-public-live-receipt.json").read_text()
    )
    release = json.loads(
        (ROOT / "deploy" / "render-core-release.json").read_text()
    )

    assert receipt["git"]["commit"] == release["release_commit"]
    assert receipt["image"]["resolved_digest"] == release["image"]["digest"]
    assert receipt["render"]["service_id"] == (
        release["service"]["render_service_id"]
    )
    assert receipt["render"]["deploy_status"] == "live"
    assert receipt["render"]["plan"] == "free"
    assert receipt["public_acceptance"]["linkup_has_create_my_card"] is True
    assert receipt["public_acceptance"]["linkup_has_enter_my_world"] is False
    assert receipt["public_acceptance"]["account_creation_post_executed"] is False
    assert receipt["boundaries"]["render_source_build_used"] is False
    assert receipt["boundaries"]["smi_redeployed"] is False
    assert receipt["boundaries"]["smi_green_claimed"] is False
