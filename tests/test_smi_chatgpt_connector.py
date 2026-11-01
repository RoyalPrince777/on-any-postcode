import pytest

from mission_control import smi_chatgpt_connector as connector


def test_contract_never_claims_live_connection_or_execution():
    contract = connector.public_contract()
    assert contract["connected"] is False
    assert contract["runtime_verified"] is False
    assert contract["write_tools_enabled"] is False
    assert contract["founder_authority_delegated"] is False
    assert contract["human_authority_final"] is True


def test_unauthorized_status_fails_closed():
    with pytest.raises(PermissionError, match="founder_authorization_required"):
        connector.safe_status(authorized=False, studio_status={"id": "oap-studio-intelligence"})


def test_status_uses_explicit_allowlist_and_never_leaks_secrets():
    result = connector.safe_status(
        authorized=True,
        studio_status={
            "id": "oap-studio-intelligence",
            "generation_backend_proven": False,
            "full_live_certificate": False,
            "OPENAI_API_KEY": "hidden-secret",
            "private_prompt": "private-content",
            "internal_url": "http://127.0.0.1:11434",
        },
    )
    assert result["studio_declared"] is True
    assert result["generation_backend_proven"] is False
    assert result["full_live_certificate"] is False
    assert result["execution_granted"] is False
    assert result["publishing_granted"] is False
    assert "hidden-secret" not in str(result)
    assert "private-content" not in str(result)
    assert "127.0.0.1" not in str(result)


def test_missing_proof_cannot_turn_true():
    result = connector.safe_status(authorized=True, studio_status={})
    assert result["generation_backend_proven"] is False
    assert result["full_live_certificate"] is False
    assert result["deployment_proven"] is False


def test_founder_route_requires_existing_session_auth():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "mission_control" / "views.py").read_text()
    assert '@bp.get("/smi/connector/status")' in source
    assert '@web_security.login_required(api=True, founder_only=True)\ndef smi_connector_status():' in source
    assert 'smi_chatgpt_connector.safe_status(' in source
    assert 'studio_status=studio_intelligence.status()' in source
    assert '_no_store(make_response(jsonify(' in source
