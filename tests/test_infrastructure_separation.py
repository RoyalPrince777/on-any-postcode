from __future__ import annotations

import json

from mission_control import infrastructure
from oap.contracts import IdentityRecord


def _human(*permissions: str) -> IdentityRecord:
    return IdentityRecord(
        identity_id="founder-1",
        identity_type="human_authority",
        authority_level=0,
        permissions=frozenset(permissions),
    )


def test_public_infrastructure_status_is_separate_and_redacted(client):
    payload = client.get("/mission/infrastructure/status").get_json()

    assert payload["visibility"] == "public"
    assert "identity" not in payload
    assert "runtime" not in payload


def test_private_infrastructure_fails_closed_without_identity(client):
    for path in (
        "/mission/infrastructure/private",
        "/mission/infrastructure/private/status",
    ):
        response = client.get(path)
        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "authentication_required"


def test_private_infrastructure_requires_dedicated_permission():
    try:
        infrastructure.get_private_infrastructure(_human())
    except PermissionError:
        pass
    else:
        raise AssertionError("Private Infrastructure must fail closed")


def test_private_infrastructure_renders_via_identity_resolver(client):
    app = client.application
    app.extensions["oap_identity_resolver"] = lambda request: _human(
        "VIEW_SOVEREIGN_INFRASTRUCTURE"
    )
    try:
        response = client.get("/mission/infrastructure/private")
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert "Private Infrastructure" in page
        assert "Verified Human Authority" in page
        assert "Credentials are never displayed" in page
        assert 'method="post"' not in page.lower()

        payload = client.get("/mission/infrastructure/private/status").get_json()
        assert payload["visibility"] == "private"
        assert payload["runtime"]["provider_calls_enabled"] is False
        assert payload["runtime"]["network_mutations_enabled"] is False
        serialized = json.dumps(payload).lower()
        for key in ("password", "private_key", "token", "credential_value"):
            assert key not in serialized
    finally:
        app.extensions.pop("oap_identity_resolver", None)
