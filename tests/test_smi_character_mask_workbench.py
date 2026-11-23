"""SMI CC original-pixel workbench: Founder-only, source-locked, no rig authority."""
from pathlib import Path

from mission_control import web_security
from oap.smi.character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS

ROOT = Path(__file__).resolve().parents[1]


def test_smi_cc_original_pixels_opens_only_one_founder_workbench(client):
    command = client.get("/mission/smi")
    page = command.get_data(as_text=True)
    assert command.status_code == 200
    assert page.count('href="/mission/character-mask-workbench"') == 1
    assert "Original Pixels" in page

    result = client.get("/mission/character-mask-workbench")
    text = result.get_data(as_text=True)
    assert result.status_code == 200
    assert result.headers["Cache-Control"] == "no-store"
    assert result.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in result.headers["Content-Security-Policy"]
    assert APPROVED_SOURCE_SHA256 in text
    assert "/static/oap/smi_live_chat_dashboard.jpg" in text
    assert "smi_character_mask_workbench.js" in text
    assert "smi_mask_zip.js" in text
    assert 'href="/mission/smi"' in text
    assert "Download seven-mask ZIP" in text
    assert "DRAFT" not in text or "Draft" in text
    assert "No automatic rig activation" in text
    assert client.post("/mission/character-mask-workbench").status_code == 405


def test_smi_cc_original_pixels_requires_sign_in(anonymous_client, monkeypatch):
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    res = anonymous_client.get("/mission/character-mask-workbench", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth" in res.headers["Location"] or "/enter-my-world" in res.headers["Location"]
    assert res.headers["X-Frame-Options"] == "DENY"


def test_smi_cc_original_pixels_rejects_non_founder(anonymous_client, monkeypatch):
    monkeypatch.setattr(
        web_security,
        "current_authenticated_user",
        lambda: {"id": "00000000-0000-4000-8000-000000000123"},
    )
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda _user: False)
    res = anonymous_client.get("/mission/character-mask-workbench")
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "human_authority_required"
    assert res.headers["Cache-Control"] == "no-store"


def test_original_pixel_editor_is_local_and_draft_only():
    source = (ROOT / "mission_control/static/smi_character_mask_workbench.js").read_text()
    page = (ROOT / "mission_control/templates/smi_character_masks.html").read_text()
    writer = (ROOT / "mission_control/static/smi_mask_zip.js").read_text()
    assert 'credentials:"same-origin"' in source
    assert 'cache:"no-store"' in source
    assert 'crypto.subtle.digest("SHA-256",bytes)' in source
    assert 'approval:"DRAFT_REQUIRES_FOUNDER_REVIEW"' in source
    assert "animation_active:false" in source
    assert "includes_hidden_regions:false" in source
    assert "auditDraftRegions()" in source
    assert "new Uint8Array(width*height)" in source
    assert "overlapping_coordinates:overlapping" in source
    assert "draft_region_audit:audit" in source
    assert "source_silhouette_verified:false" in source
    assert "hidden_anatomy_verified:false" in source
    assert "occlusion_approved:false" in source
    assert "anatomical_mask_approval:false" in source
    assert "No automatic rig activation" in page
    assert "Download seven-mask ZIP" in page
    assert 'href="{{ url_for(\'mission_control.smi_command_dashboard_view\') }}"' in page
    for layer in LAYERS:
        assert layer in source
    assert "exact_eight_bundle_entries_required" in writer
    for forbidden in (
        "getUserMedia(", "sendBeacon(", "localStorage", "sessionStorage",
        "new WebSocket(", "navigator.serviceWorker", "requestAnimationFrame(",
    ):
        assert forbidden not in source


def test_gateway_keeps_only_original_art_visible():
    import smi_gateway

    assert smi_gateway._allowed("/mission/character-mask-workbench")
    assert smi_gateway._allowed("/mission/static/smi_character_mask_workbench.js")
    assert smi_gateway._allowed("/mission/static/smi_mask_zip.js")
    assert smi_gateway._allowed("/static/oap/smi_live_chat_dashboard.jpg")
    assert not smi_gateway._allowed("/static/oap/private-mask.png")
    assert not smi_gateway._allowed("/static/oap/some-other-character.jpg")
