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


def test_http_route_rejects_anonymous_and_non_founder(monkeypatch):
    from flask import Flask
    from mission_control import views, web_security

    app = Flask(__name__)
    app.secret_key = "test-only-no-production-secret"
    app.register_blueprint(views.bp, url_prefix="/mission")
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    client = app.test_client()
    anonymous = client.get("/mission/smi/connector/status")
    assert anonymous.status_code == 401
    assert anonymous.headers["Cache-Control"] == "no-store"

    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: {"id": "test-user"})
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    denied = client.get("/mission/smi/connector/status")
    assert denied.status_code == 403
    assert denied.headers["Cache-Control"] == "no-store"


def test_http_route_returns_only_allowlisted_data_to_founder(monkeypatch):
    from flask import Flask
    from mission_control import views, web_security

    app = Flask(__name__)
    app.secret_key = "test-only-no-production-secret"
    app.register_blueprint(views.bp, url_prefix="/mission")
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: {"id": "founder-test"})
    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    monkeypatch.setattr(views.studio_intelligence, "status", lambda: {
        "id": "oap-studio-intelligence",
        "generation_backend_proven": False,
        "full_live_certificate": False,
        "secret": "never-send-this",
    })
    response = app.test_client().get("/mission/smi/connector/status")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.json["studio_declared"] is True
    assert response.json["execution_granted"] is False
    assert "never-send-this" not in response.get_data(as_text=True)
