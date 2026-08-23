from __future__ import annotations

import json

from mission_control import brain
from oap.contracts import IdentityRecord


def _human(*permissions: str) -> IdentityRecord:
    return IdentityRecord(
        identity_id="founder-1",
        identity_type="human_authority",
        authority_level=0,
        permissions=frozenset(permissions),
    )


def test_public_smi_has_separate_redacted_routes(client):
    for path in ("/mission/brain", "/mission/smi"):
        response = client.get(path)
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Sovereign Megaverse Intelligence" in page
        assert "Public dashboard" in page
        assert "Verified Human Authority" not in page

    projection = client.get("/mission/smi/status").get_json()
    assert projection["visibility"] == "public"
    assert "identity" not in projection


def test_private_smi_fails_closed_without_identity(client):
    for path in ("/mission/smi/private", "/mission/smi/private/status"):
        response = client.get(path)
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "authentication_required"
    assert client.post("/mission/smi/private").status_code == 405


def test_private_projection_requires_level_zero_permission():
    for identity in (
        _human(),
        IdentityRecord(
            identity_id="agent-1",
            identity_type="agent",
            authority_level=4,
            permissions=frozenset({"VIEW_SOVEREIGN_SMI"}),
        ),
    ):
        try:
            brain.get_private_brain_status(identity)
        except PermissionError:
            pass
        else:
            raise AssertionError("Private SMI projection must fail closed")


def test_private_dashboard_renders_only_through_injected_identity_resolver(client):
    app = client.application
    app.extensions["oap_identity_resolver"] = lambda request: _human(
        "VIEW_SOVEREIGN_SMI"
    )
    try:
        response = client.get("/mission/smi/private")
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Private Sovereign SMI" in page
        assert "Verified Human Authority" in page
        assert "Sovereign controls" in page
        assert 'method="post"' not in page.lower()

        payload = client.get("/mission/smi/private/status").get_json()
        assert payload["visibility"] == "private"
        assert payload["identity"]["authority_level"] == 0
        serialized = json.dumps(payload).lower()
        for secret in ("password", "private_key", "token", "signing_key"):
            assert secret not in serialized
    finally:
        app.extensions.pop("oap_identity_resolver", None)
