from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from mission_control import smi_authenticated_dispatch
from mission_control.smi_connector_dispatch import ConnectorAccessDenied
from mission_control.smi_mcp_token_gate import TokenRejected, TrustedTokenPolicy


@pytest.fixture
def identity():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    policy = TrustedTokenPolicy(
        issuer="https://auth.example.test",
        audience="https://oap.example.test/mission/smi/mcp",
        founder_subject="founder-test-id",
        public_key_pem=pub,
    )
    now = datetime.now(UTC)
    claims = {
        "iss": policy.issuer, "aud": policy.audience,
        "sub": policy.founder_subject, "iat": now,
        "exp": now + timedelta(minutes=5), "scope": "oap.smi.status.read",
    }
    return key, policy, claims


def test_valid_token_routes_to_existing_readonly_dispatcher(identity):
    key, policy, claims = identity
    token = jwt.encode(claims, key, algorithm="RS256")
    result = smi_authenticated_dispatch.verified_readonly_dispatch(
        bearer_token=token,
        policy=policy,
        tool_name="smi_status",
        arguments={},
        studio_status={"id": "oap-studio-intelligence", "secret": "never-expose"},
    )
    assert result["studio_declared"] is True
    assert result["execution_granted"] is False
    assert "never-expose" not in str(result)


def test_invalid_token_never_reaches_dispatcher(identity, monkeypatch):
    _, policy, _ = identity

    def forbidden(*args, **kwargs):
        raise AssertionError("dispatcher must not run on bad token")

    monkeypatch.setattr(smi_authenticated_dispatch.smi_connector_dispatch, "dispatch", forbidden)
    with pytest.raises(TokenRejected):
        smi_authenticated_dispatch.verified_readonly_dispatch(
            bearer_token="not-a-valid-token",
            policy=policy, tool_name="smi_status", arguments={},
        )


def test_valid_token_still_cannot_execute_write_tool(identity):
    key, policy, claims = identity
    token = jwt.encode(claims, key, algorithm="RS256")
    with pytest.raises(ConnectorAccessDenied):
        smi_authenticated_dispatch.verified_readonly_dispatch(
            bearer_token=token,
            policy=policy, tool_name="studio_generate", arguments={},
        )
