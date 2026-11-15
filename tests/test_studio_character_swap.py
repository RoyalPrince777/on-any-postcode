"""Fail-closed contract for SMI's character swap prep (no provider execution)."""
import pytest

from mission_control import studio_character_swap


def test_prepared_swap_is_not_a_render_or_credit_authority():
    result = studio_character_swap.prepare(
        source_video_id="4db19aff-ebd2-441e-ba6c-c0d7cfa94e12",
        character_image_id="fb53cdb9-0776-4aa0-baf8-e433f8940b5e",
        source_duration_seconds=29.7, quoted_credits=210,
    )
    assert result["state"] == "prepared"
    assert result["quote_claimed_credits"] == 210
    assert result["quote_verified_by_smi"] is False
    assert result["render_submitted"] is False
    assert result["media_ownership_verified"] is False
    assert result["execution_granted"] is False
    assert result["payment_authorised"] is False
    assert result["founder_final"] is True


@pytest.mark.parametrize("duration", [0, 3.9, 30.17, -1, "nan", "infinity"])
def test_source_duration_outside_provider_limit_fails_closed(duration):
    with pytest.raises(ValueError, match="studio_swap_duration_out_of_range"):
        studio_character_swap.prepare(
            source_video_id="4db19aff-ebd2-441e-ba6c-c0d7cfa94e12",
            character_image_id="fb53cdb9-0776-4aa0-baf8-e433f8940b5e",
            source_duration_seconds=duration,
        )


def test_unregistered_media_or_changed_target_rejected():
    base = {
        "source_video_id": "4db19aff-ebd2-441e-ba6c-c0d7cfa94e12",
        "character_image_id": "fb53cdb9-0776-4aa0-baf8-e433f8940b5e",
        "source_duration_seconds": 29.7,
    }
    with pytest.raises(ValueError, match="registered_media"):
        studio_character_swap.prepare(**{**base, "source_video_id": "https://example.test/file.mp4"})
    with pytest.raises(ValueError, match="target_unsupported"):
        studio_character_swap.prepare(**{**base, "target": "all_people"})
    with pytest.raises(ValueError, match="quote_invalid"):
        studio_character_swap.prepare(**{**base, "quoted_credits": True})


def test_smi_wrapper_writes_purple_hrm_receipt(monkeypatch):
    from mission_control import studio_intelligence
    receipts = []
    def fake_receipt(kind, payload):
        receipts.append((kind, payload))
        return {"read_back_ok": True, "receipt_id": "studio-preflight"}
    monkeypatch.setattr(studio_intelligence.smi_receipt_backend, "write_receipt", fake_receipt)
    result = studio_intelligence.prepare_character_swap(
        source_video_id="4db19aff-ebd2-441e-ba6c-c0d7cfa94e12",
        character_image_id="fb53cdb9-0776-4aa0-baf8-e433f8940b5e",
        source_duration_seconds=29.7, quoted_credits=210,
    )
    assert result["receipt_proven"] is True
    assert result["render_submitted"] is False
    assert receipts[0][1]["signal"] == "🟣"
    assert receipts[0][1]["safe_payload"]["quote_verified"] is False
    assert "source_video_id" not in receipts[0][1]["safe_payload"]


def test_founder_only_preflight_route_exists():
    from pathlib import Path
    views = (Path(__file__).resolve().parents[1] / "mission_control" / "views.py").read_text()
    assert '@bp.post("/studio/character-swap/prepare")' in views
    assert '@web_security.login_required(api=True, founder_only=True)' in views
    assert "studio_intelligence.prepare_character_swap(" in views
    assert "studio_receipt_unconfirmed" in views
