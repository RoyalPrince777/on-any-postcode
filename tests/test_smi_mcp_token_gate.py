from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from mission_control.smi_mcp_token_gate import (
    TokenRejected,
    TrustedTokenPolicy,
    verify_readonly_token,
)


@pytest.fixture
def signing():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    from cryptography.hazmat.primitives import serialization

    public_pem = private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    policy = TrustedTokenPolicy(
        issuer="https://auth.example.test",
        audience="https://oap.example.test/mission/smi/mcp",
        founder_subject="founder-test-id",
        public_key_pem=public_pem,
    )
    now = datetime.now(UTC)
    claims = {
        "iss": policy.issuer,
        "aud": policy.audience,
        "sub": policy.founder_subject,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "scope": "oap.smi.status.read",
    }
    return private, policy, claims


def test_signed_readonly_access_token_is_verified(signing):
    private, policy, claims = signing
    token = jwt.encode(claims, private, algorithm="RS256")
    assert verify_readonly_token(token, policy=policy) == "founder-test-id"


@pytest.mark.parametrize("change", [
    {"iss": "https://attacker.test"},
    {"aud": "https://other.example.test"},
    {"sub": "someone-else"},
    {"scope": "oap.smi.status.readwrite"},
    {"scope": ""},
    {"exp": datetime(2020, 1, 1, tzinfo=UTC)},
])
def test_invalid_claims_fail_closed(signing, change):
    private, policy, claims = signing
    token = jwt.encode({**claims, **change}, private, algorithm="RS256")
    with pytest.raises(TokenRejected, match="invalid_access_token"):
        verify_readonly_token(token, policy=policy)


def test_unsigned_or_wrong_key_tokens_rejected(signing):
    _, policy, claims = signing
    unsigned = jwt.encode(claims, key="", algorithm="none")
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wrong_signature = jwt.encode(claims, other_key, algorithm="RS256")
    for token in (unsigned, wrong_signature, "", None):
        with pytest.raises(TokenRejected):
            verify_readonly_token(token, policy=policy)


def test_missing_required_expiry_rejected(signing):
    private, policy, claims = signing
    claims.pop("exp")
    with pytest.raises(TokenRejected):
        verify_readonly_token(jwt.encode(claims, private, algorithm="RS256"), policy=policy)
