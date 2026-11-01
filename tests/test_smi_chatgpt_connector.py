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
