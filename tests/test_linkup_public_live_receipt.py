import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_linkup_live_receipt_remains_the_last_proven_live_runtime():
    receipt = json.loads(
        (ROOT / "deploy" / "linkup-public-live-receipt.json").read_text()
    )
    release = json.loads(
        (ROOT / "deploy" / "render-core-release.json").read_text()
    )

    assert receipt["git"]["commit"] == (
        "9bf7aba26beda0ea2f1ea6d192a7585d0b7cd6d8"
    )
    assert receipt["image"]["resolved_digest"] == (
        "sha256:706fc5700049b0be2a7d7df2e755e5fe160c61c33dbc2d454d772fd6ddd519b6"
    )
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

    assert release["evidence_state"] == "candidate_not_live_proven"
    assert release["live_proof"]["receipt"] == (
        "deploy/linkup-public-live-receipt.json"
    )
    assert release["release_commit"] != receipt["git"]["commit"]
