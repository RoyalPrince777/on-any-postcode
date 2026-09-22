"""Founder-only real mask editor shell; private browser files, never rig approval."""
from pathlib import Path

from mission_control import neon_auth
from oap.smi.character_rig_assets import APPROVED_SOURCE_SHA256, LAYERS

ROOT = Path(__file__).resolve().parents[1]


def test_founder_mask_workbench_renders_exact_art_and_local_export(client):
    response = client.get("/mission/character-mask-workbench")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    page = response.get_data(as_text=True)
    assert "/static/oap/smi_live_chat_dashboard.jpg" in page
    assert APPROVED_SOURCE_SHA256 in page
    assert "smi_character_mask_workbench.js" in page
    assert "smi_mask_zip.js" in page
    assert "smi_character_source_pixels.js" in page
    assert "Download seven source layers" in page
    assert "Download seven-mask ZIP" in page
    assert "Draft masks" in page
    assert "No SMI provider" in page
    for layer in LAYERS:
        assert layer in (
            ROOT / "mission_control/static/smi_character_mask_workbench.js"
        ).read_text()


def test_character_mask_workbench_anonymous_denied(anonymous_client):
    response = anonymous_client.get("/mission/character-mask-workbench")
    assert response.status_code == 302
    assert "/enter-my-world" in response.headers["Location"]


def test_character_mask_workbench_non_founder_denied(
    anonymous_client, monkeypatch
):
    def member(_cookie_header):
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "ordinary-member"},
                "user": {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "email": "ordinary-member@example.test",
                    "name": "Ordinary Member",
                    "emailVerified": True,
                },
            },
        )
    monkeypatch.setattr(neon_auth, "get_session", member)
    anonymous_client.set_cookie(
        "better-auth.session_token", "ordinary-member"
    )
    with anonymous_client.session_transaction() as session:
        session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [
            "better-auth.session_token"
        ]
    response = anonymous_client.get("/mission/character-mask-workbench")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "human_authority_required"
    assert response.headers["Cache-Control"] == "no-store"


def test_mask_editor_contains_no_remote_upload_or_false_rig_activation():
    source = (
        ROOT / "mission_control/static/smi_character_mask_workbench.js"
    ).read_text()
    page = (
        ROOT / "mission_control/templates/smi_character_masks.html"
    ).read_text()
    assert 'credentials:"same-origin"' in source
    assert 'cache:"no-store"' in source
    assert 'crypto.subtle.digest("SHA-256",bytes)' in source
    assert "new Uint8Array(await blob.arrayBuffer())" in source
    assert "createSourceZip(entries)" in source
    assert "speech_sync_proven:false" in source
    assert "new Blob([bytes],{type:" in source
    assert "active:false" not in source or "animation_active:false" in source
    assert "approval:\"DRAFT_REQUIRES_FOUNDER_REVIEW\"" in source
    assert "No substitute avatar" in page
    assert "No SMI provider" in page
    for forbidden in (
        "getUserMedia(", "sendBeacon(", "localStorage", "sessionStorage",
        "new WebSocket(", "navigator.serviceWorker",
    ):
        assert forbidden not in source



def test_gateway_allows_only_sha_pinned_original_not_arbitrary_static():
    import smi_gateway

    assert smi_gateway._allowed("/mission/character-mask-workbench")
    assert smi_gateway._allowed("/mission/static/smi_character_mask_workbench.js")
    assert smi_gateway._allowed("/mission/static/smi_mask_zip.js")
    assert smi_gateway._allowed("/mission/static/smi_character_source_pixels.js")
    assert smi_gateway._allowed("/static/oap/smi_live_chat_dashboard.jpg")
    assert not smi_gateway._allowed("/static/oap/other-character.jpg")
    assert not smi_gateway._allowed("/static/oap/private-mask.png")
    assert not smi_gateway._allowed("/static")
    assert not smi_gateway._allowed("/static/oap/smi_live_chat_dashboard.jpg/other")
