import pytest

from mission_control import smi_oauth_resource_contract as oauth


def test_metadata_has_exact_read_only_resource_and_scope():
    result = oauth.protected_resource_metadata(
        resource_origin="https://onanypostcode.global",
        authorization_server_origin="https://auth.onanypostcode.global",
    )
    assert result == {
        "resource": "https://onanypostcode.global/mission/smi/mcp",
        "authorization_servers": ["https://auth.onanypostcode.global"],
        "scopes_supported": ["oap.smi.status.read"],
        "bearer_methods_supported": ["header"],
    }


@pytest.mark.parametrize("origin", [
    "http://onanypostcode.global",
    "http://localhost",
    "https://localhost",
    "https://127.0.0.1",
    "https://user:pass@onanypostcode.global",
    "https://onanypostcode.global/path",
    "https://onanypostcode.global/?key=secret",
    "https://onanypostcode.global/#fragment",
    "",
    None,
])
def test_unsafe_resource_origin_rejected(origin):
    with pytest.raises(ValueError):
        oauth.protected_resource_metadata(
            resource_origin=origin,
            authorization_server_origin="https://auth.onanypostcode.global",
        )


def test_no_fake_oauth_or_chatgpt_availability():
    state = oauth.requirements()
    assert state["oauth_ready"] is False
    assert state["mcp_transport_ready"] is False
    assert state["chatgpt_connected"] is False
    assert state["write_access_enabled"] is False
    assert "founder_subject" in state["token_validation_required"]
    assert "audience" in state["token_validation_required"]
