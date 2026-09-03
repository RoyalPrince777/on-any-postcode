from __future__ import annotations

import base64
import hashlib
import hmac
import uuid

import pytest

from mission_control import link_relationships, link_turn


TURN_ENV_KEYS = (
    "OAP_LINK_TURN_URLS",
    "OAP_LINK_TURN_SHARED_SECRET",
    "OAP_LINK_TURN_REALM",
    "OAP_LINK_TURN_OWNED",
    "OAP_LINK_TURN_RELAY_VERIFIED",
    "OAP_LINK_TURN_TTL_SECONDS",
)


def _clear_turn_env(monkeypatch):
    for key in TURN_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _configure_turn(monkeypatch, *, verified: bool = False):
    monkeypatch.setenv(
        "OAP_LINK_TURN_URLS",
        "turn:turn.oap.internal:3478?transport=udp,turns:turn.oap.internal:5349?transport=tcp",
    )
    monkeypatch.setenv("OAP_LINK_TURN_SHARED_SECRET", "s" * 48)
    monkeypatch.setenv("OAP_LINK_TURN_REALM", "turn.oap.internal")
    monkeypatch.setenv("OAP_LINK_TURN_OWNED", "true")
    monkeypatch.setenv("OAP_LINK_TURN_RELAY_VERIFIED", "true" if verified else "false")
    monkeypatch.setenv("OAP_LINK_TURN_TTL_SECONDS", "300")


def test_turn_status_fails_closed_without_oap_owned_configuration(monkeypatch):
    _clear_turn_env(monkeypatch)

    state = link_turn.status()

    assert state == {
        "configured": False,
        "owned": False,
        "credential_ready": False,
        "relay_verified": False,
        "ready": False,
        "url_count": 0,
        "ttl_seconds": 300,
    }


def test_turn_rejects_non_turn_urls_and_requires_oap_ownership(monkeypatch):
    _clear_turn_env(monkeypatch)
    monkeypatch.setenv("OAP_LINK_TURN_URLS", "https://relay.example.com")
    monkeypatch.setenv("OAP_LINK_TURN_SHARED_SECRET", "s" * 48)
    monkeypatch.setenv("OAP_LINK_TURN_REALM", "relay.example.com")

    invalid = link_turn.status()
    assert invalid["configured"] is False
    assert invalid["credential_ready"] is False

    monkeypatch.setenv("OAP_LINK_TURN_URLS", "turn:relay.example.com:3478")
    configured_not_owned = link_turn.status()
    assert configured_not_owned["configured"] is True
    assert configured_not_owned["owned"] is False
    assert configured_not_owned["credential_ready"] is False
    assert configured_not_owned["ready"] is False


def test_turn_configuration_does_not_claim_verified_relay(monkeypatch):
    _clear_turn_env(monkeypatch)
    _configure_turn(monkeypatch, verified=False)

    state = link_turn.status()

    assert state["configured"] is True
    assert state["owned"] is True
    assert state["credential_ready"] is True
    assert state["relay_verified"] is False
    assert state["ready"] is False


def test_turn_credentials_are_short_lived_and_secret_never_returned(monkeypatch):
    _clear_turn_env(monkeypatch)
    _configure_turn(monkeypatch, verified=False)
    identity = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    now = 1_800_000_000
    monkeypatch.setattr(link_turn.time, "time", lambda: now)
    monkeypatch.setattr(
        link_turn.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_turn.link_relationships, "accepted_between", lambda _first, _second: True
    )

    result = link_turn.issue_credentials(identity, recipient)

    expires_at = now + 300
    username = f"{expires_at}:{identity}"
    expected = base64.b64encode(
        hmac.new(("s" * 48).encode(), username.encode(), hashlib.sha1).digest()
    ).decode("ascii")
    server = result["ice_servers"][0]
    assert result["expires_at"] == expires_at
    assert result["ttl_seconds"] == 300
    assert result["relay_verified"] is False
    assert server["username"] == username
    assert server["credential"] == expected
    assert server["credentialType"] == "password"
    assert server["urls"] == [
        "turn:turn.oap.internal:3478?transport=udp",
        "turns:turn.oap.internal:5349?transport=tcp",
    ]
    assert "shared_secret" not in str(result).casefold()
    assert "s" * 48 not in str(result)


def test_turn_block_guard_stops_before_relationship_lookup(monkeypatch):
    _clear_turn_env(monkeypatch)
    _configure_turn(monkeypatch)
    monkeypatch.setattr(
        link_turn.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_turn.link_relationships,
        "accepted_between",
        lambda *_args: pytest.fail("blocked pair must not reach Link relationship lookup"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_turn.issue_credentials(uuid.uuid4(), uuid.uuid4())


def test_turn_requires_accepted_link(monkeypatch):
    _clear_turn_env(monkeypatch)
    _configure_turn(monkeypatch)
    monkeypatch.setattr(
        link_turn.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_turn.link_relationships, "accepted_between", lambda _first, _second: False
    )

    with pytest.raises(ValueError, match="accepted_link_required"):
        link_turn.issue_credentials(uuid.uuid4(), uuid.uuid4())


def test_turn_ttl_is_bounded(monkeypatch):
    _clear_turn_env(monkeypatch)
    _configure_turn(monkeypatch)

    monkeypatch.setenv("OAP_LINK_TURN_TTL_SECONDS", "5")
    assert link_turn.status()["ttl_seconds"] == 60
    monkeypatch.setenv("OAP_LINK_TURN_TTL_SECONDS", "99999")
    assert link_turn.status()["ttl_seconds"] == 900
    monkeypatch.setenv("OAP_LINK_TURN_TTL_SECONDS", "broken")
    assert link_turn.status()["ttl_seconds"] == 300


def test_accepted_link_guard_is_pair_scoped_and_expiry_aware(monkeypatch):
    first = str(uuid.uuid4())
    second = str(uuid.uuid4())
    calls = []

    class Result:
        def fetchone(self):
            return (1,)

    class Connection:
        def execute(self, query, params):
            calls.append((" ".join(str(query).split()), params))
            return Result()

    class Context:
        def __enter__(self):
            return Connection()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        link_relationships.postgres_db,
        "connect",
        lambda *args, **kwargs: Context(),
    )

    assert link_relationships.accepted_between(first, second) is True
    query, params = calls[0]
    assert "status='accepted'" in query
    assert "expires_at>CURRENT_TIMESTAMP" in query
    assert params == (first, second, first, second)


def test_turn_status_route_is_authenticated_and_secret_free(
    client, monkeypatch
):
    monkeypatch.setattr(
        link_turn,
        "status",
        lambda: {
            "configured": True,
            "owned": True,
            "credential_ready": True,
            "relay_verified": False,
            "ready": False,
            "url_count": 2,
            "ttl_seconds": 300,
        },
    )

    response = client.get("/linkup/turn/status")

    assert response.status_code == 200
    assert response.get_json() == {
        "configured": True,
        "credential_ready": True,
        "owned": True,
        "ready": False,
        "relay_verified": False,
    }
    assert response.headers["Cache-Control"] == "no-store"
    assert "secret" not in response.get_data(as_text=True).casefold()


def test_turn_credentials_route_requires_csrf(client):
    response = client.post(
        "/linkup/turn/credentials",
        json={"recipient_id": str(uuid.uuid4())},
    )

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
