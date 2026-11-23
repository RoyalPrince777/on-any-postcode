"""Bounded regression tests for the additive Founder Studio provider panel.

No provider credentials, network requests, downloads or paid renders required.
"""
from pathlib import Path

import pytest

from mission_control import studio_provider_capabilities as catalogue

ROOT = Path(__file__).resolve().parents[1]


def test_catalogue_is_one_private_studio_without_fake_provider_green():
    snapshot = catalogue.status({"configured": True, "api_key": "NEVER_EXPOSE_ME"})
    assert snapshot["studio"] == "oap-studio-intelligence"
    assert snapshot["one_canonical_studio"] is True
    assert snapshot["external_calls_enabled_by_catalogue"] is False
    models = {model["id"]: model for model in snapshot["provider_catalogue"]}
    for model_id in ("nano-banana", "seedance", "higgsfield", "elevenlabs",
                     "voicestudio", "oap-image", "oap-video", "oap-local"):
        assert model_id in models
    assert all(model["execution_granted"] is False for model in models.values())
    assert all(model["runtime_verified"] is False for model in models.values())
    assert models["oap-image"]["adapter_configured"] is True
    assert models["seedance"]["adapter_configured"] is False
    assert "NEVER_EXPOSE_ME" not in str(snapshot)


@pytest.mark.parametrize("model_id,task", [
    ("nano-banana", "image"), ("nano-banana", "edit"),
    ("seedance", "video"), ("higgsfield", "animate"),
    ("elevenlabs", "voice"), ("voicestudio", "dub"),
    ("oap-image", "edit"), ("oap-video", "video"),
    ("oap-local", "composite"),
])
def test_preflight_does_not_execute_even_if_every_box_is_checked(model_id, task):
    result = catalogue.preflight({
        "model_id": model_id,
        "task": task,
        "aspect_ratio": "16:9",
        "duration_seconds": 5,
        "owner_rights_confirmed": True,
        "subject_consent_confirmed": True,
        "remote_approved": True,
    }, {"configured": True})
    assert result["state"] == "blocked_pending_evidence"
    assert result["execution_granted"] is False
    assert result["payment_authorised"] is False
    assert result["upload_performed"] is False
    assert result["provider_called"] is False
    assert result["output_generated"] is False
    assert "guardian_hrm_independent_proof" in result["missing_evidence"]


@pytest.mark.parametrize("payload", [
    None, [], "", {"model_id": "unknown", "task": "image"},
    {"model_id": "nano-banana", "task": "voice"},
    {"model_id": "nano-banana", "task": "image", "aspect_ratio": "2:1"},
    {"model_id": "seedance", "task": "video", "duration_seconds": 0},
    {"model_id": "seedance", "task": "video", "duration_seconds": 31},
    {"model_id": "seedance", "task": "video", "duration_seconds": True},
    {"model_id": "seedance", "task": "video", "remote_approved": "true"},
    {"model_id": "seedance", "task": "video", "prompt": "do not store raw prompts"},
    {"model_id": "seedance", "task": "video", "api_key": "do not accept secrets"},
])
def test_preflight_rejects_invalid_or_sensitive_fields(payload):
    with pytest.raises(ValueError):
        catalogue.preflight(payload)


def test_unapproved_remote_transfer_and_unowned_reference_are_blockers():
    p = catalogue.preflight({"model_id": "seedance", "task": "animate"})
    assert "external_transfer_not_approved" in p["missing_evidence"]
    assert "reference_ownership_not_confirmed" in p["missing_evidence"]
    assert "subject_consent_not_confirmed" in p["missing_evidence"]


def test_studio_routes_remain_founder_only_and_csrf_gated():
    views = (ROOT / "mission_control" / "views.py").read_text()
    assert '@bp.get("/studio/providers")\n@web_security.login_required(api=True, founder_only=True)' in views
    assert '@bp.post("/studio/providers/preflight")\n@web_security.login_required(api=True, founder_only=True)' in views
    section = views.split('def smi_studio_provider_preflight():', 1)[1].split('@bp.post(', 1)[0]
    assert "web_security.csrf_valid(request)" in section


def test_dashboard_is_additive_and_uses_real_routes():
    html = (ROOT / "mission_control/templates/smi_command_dashboard.html").read_text()
    js = (ROOT / "mission_control/static/smi_studio_provider_panel.js").read_text()
    assert 'id="studio-providers"' in html
    assert 'id="oap-studio-model-grid"' in html
    assert 'meta name="oap-csrf-token"' in html
    assert 'href="/mission/war-room"' in html
    assert 'OAP World → The Spot → The Link → Link Up' in html
    assert 'X-OAP-CSRF' in js
    assert '"/mission/studio/providers/preflight"' in js
    assert 'executionAuthority: false' in js
    assert "navigator.clipboard.writeText" in js
