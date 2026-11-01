import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask

from mission_control.smi_mcp_token_gate import TrustedTokenPolicy
from mission_control.smi_mcp_transport import create_smi_mcp_blueprint


@pytest.fixture
def transport():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    policy = TrustedTokenPolicy(
        issuer="https://auth.example.test",
        audience="https://oap.example.test/mission/smi/mcp",
        founder_subject="founder-test-id",
        public_key_pem=pub,
    )
    now = datetime.now(UTC)
    claims = {
        "iss": policy.issuer, "aud": policy.audience, "sub": policy.founder_subject,
        "iat": now, "exp": now + timedelta(minutes=5), "scope": "oap.smi.status.read",
    }
    token = jwt.encode(claims, key, algorithm="RS256")
    active = {"value": True}
    app = Flask(__name__)
    app.register_blueprint(create_smi_mcp_blueprint(
        policy=policy, token_active=lambda _: active["value"]
    ))
    return app.test_client(), token, active


def call(client, token, method, params=None):
    return client.post(
        "/mission/smi/mcp",
        headers={"Authorization": f"Bearer {token}"},
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
    )


def test_requires_bearer_token(transport):
    client, _, _ = transport
    assert client.post("/mission/smi/mcp", json={}).status_code == 401


def test_revoked_token_fails_closed(transport):
    client, token, active = transport
    active["value"] = False
    assert call(client, token, "tools/list").status_code == 401


def test_mcp_initialize_and_list_readonly_tools(transport):
    client, token, _ = transport
    init = call(client, token, "initialize")
    assert init.status_code == 200
    assert init.json["result"]["capabilities"]["tools"] == {"listChanged": False}
    listed = call(client, token, "tools/list")
    assert [tool["name"] for tool in listed.json["result"]["tools"]] == [
        "smi_status", "studio_capabilities"
    ]


def test_tool_call_stays_readonly(transport):
    client, token, _ = transport
    result = call(client, token, "tools/call", {"name": "smi_status", "arguments": {}})
    assert result.status_code == 200
    status = json.loads(result.json["result"]["content"][0]["text"])
    assert status["execution_granted"] is False
    assert status["human_authority_final"] is True
    rejected = call(client, token, "tools/call", {"name": "studio_generate", "arguments": {}})
    assert rejected.status_code == 400


def test_invalid_token_and_unknown_method(transport):
    client, token, _ = transport
    assert call(client, "invalid-token", "tools/list").status_code == 401
    assert call(client, token, "tools/delete").status_code == 404
