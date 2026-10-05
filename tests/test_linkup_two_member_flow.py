from __future__ import annotations

import uuid
from datetime import datetime, timezone

import app as app_module
from mission_control import link_message_routes, neon_auth, web_security


USER_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
USER_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
COOKIE_A = "oap.a.session"
COOKIE_B = "oap.b.session"
CSRF_A = "csrf-a-12345678901234567890"
CSRF_B = "csrf-b-12345678901234567890"


def _auth(cookie_header: str):
    if f"{COOKIE_A}=a-session" in cookie_header:
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "a-session"},
                "user": {
                    "id": USER_A,
                    "name": "Member A",
                    "email": "a@example.test",
                    "emailVerified": True,
                },
            },
        )
    if f"{COOKIE_B}=b-session" in cookie_header:
        return neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "b-session"},
                "user": {
                    "id": USER_B,
                    "name": "Member B",
                    "email": "b@example.test",
                    "emailVerified": True,
                },
            },
        )
    return neon_auth.AuthResult(status_code=200, payload=None)


def _client(cookie_name: str, cookie_value: str, csrf_value: str):
    client = app_module.app.test_client()
    client.set_cookie(cookie_name, cookie_value)
    with client.session_transaction() as session:
        session[neon_auth.AUTH_COOKIE_NAMES_SESSION_KEY] = [cookie_name]
        session[web_security.CSRF_SESSION_KEY] = csrf_value
    return client


def test_two_member_http_flow_landed_lit_and_cursor_no_duplicate(monkeypatch):
    """Exercise the real Link Up HTTP routes as two authenticated members."""

    app_module.app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    monkeypatch.setattr(neon_auth, "get_session", _auth)
    monkeypatch.setenv(
        "NEON_AUTH_BASE_URL",
        "https://example.neonauth.test/neondb/auth",
    )
    monkeypatch.setenv("OAP_AUTH_REQUIRED", "true")
    web_security.PUBLIC_WRITE_LIMITER.reset()

    messages: list[dict[str, object]] = []

    monkeypatch.setattr(
        link_message_routes.public_store,
        "ensure_authenticated_user",
        lambda *_args, **_kwargs: None,
    )

    def send_message(sender_id, recipient_id, body, *, client_message_id=None):
        assert sender_id in {USER_A, USER_B}
        assert recipient_id in {USER_A, USER_B}
        assert sender_id != recipient_id
        message_id = str(uuid.uuid4())
        messages.append(
            {
                "message_id": message_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "body": str(body),
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "client_message_id": client_message_id,
            }
        )
        return message_id

    def peer_messages_since(
        identity_id,
        peer_id,
        *,
        after=None,
        after_id=None,
        limit=100,
    ):
        pair = [
            item
            for item in messages
            if {item["sender_id"], item["recipient_id"]} == {identity_id, peer_id}
        ]
        if after and after_id:
            pair = [
                item
                for item in pair
                if (str(item["created_at"]), str(item["message_id"]))
                > (str(after), str(after_id))
            ]
        return [
            {
                "message_id": item["message_id"],
                "direction": (
                    "sent" if item["sender_id"] == identity_id else "received"
                ),
                "sender_id": item["sender_id"],
                "recipient_id": item["recipient_id"],
                "body": item["body"],
                "read": item["read"],
                "state": (
                    "seen"
                    if item["sender_id"] == identity_id and item["read"]
                    else "landed"
                    if item["sender_id"] == identity_id
                    else "received"
                ),
                "created_at": item["created_at"],
            }
            for item in pair[:limit]
        ]

    def mark_message_read(identity_id, message_id):
        for item in messages:
            if item["message_id"] == message_id and item["recipient_id"] == identity_id:
                item["read"] = True
                return True
        return False

    def message_states(identity_id, peer_id):
        return [
            {
                "message_id": item["message_id"],
                "state": "seen" if item["read"] else "landed",
                "created_at": item["created_at"],
            }
            for item in messages
            if item["sender_id"] == identity_id and item["recipient_id"] == peer_id
        ]

    monkeypatch.setattr(
        link_message_routes.product_store,
        "send_message",
        send_message,
    )
    monkeypatch.setattr(
        link_message_routes.product_store,
        "peer_messages_since",
        peer_messages_since,
    )
    monkeypatch.setattr(
        link_message_routes.product_store,
        "mark_message_read",
        mark_message_read,
    )
    monkeypatch.setattr(
        link_message_routes.product_store,
        "message_states",
        message_states,
    )

    sender = _client(COOKIE_A, "a-session", CSRF_A)
    receiver = _client(COOKIE_B, "b-session", CSRF_B)

    sent = sender.post(
        "/linkup/messages",
        json={
            "recipient_id": USER_B,
            "body": "OAP two-member proof",
            "client_message_id": str(uuid.uuid4()),
        },
        headers={"X-OAP-CSRF": CSRF_A},
    )
    assert sent.status_code == 201
    sent_payload = sent.get_json()
    assert sent_payload["state"] == "landed"
    message_id = sent_payload["message_id"]

    incoming = receiver.get(f"/linkup/messages/incoming?peer_id={USER_A}")
    assert incoming.status_code == 200
    incoming_messages = incoming.get_json()["messages"]
    assert len(incoming_messages) == 1
    assert incoming_messages[0]["message_id"] == message_id
    assert incoming_messages[0]["direction"] == "received"
    assert incoming_messages[0]["body"] == "OAP two-member proof"

    lit = receiver.post(
        f"/linkup/messages/{message_id}/seen",
        json={},
        headers={"X-OAP-CSRF": CSRF_B},
    )
    assert lit.status_code == 200
    assert lit.get_json()["state"] == "seen"

    sender_state = sender.get(f"/linkup/messages/state?peer_id={USER_B}")
    assert sender_state.status_code == 200
    states = sender_state.get_json()["messages"]
    assert states == [
        {
            "message_id": message_id,
            "state": "seen",
            "created_at": messages[0]["created_at"],
        }
    ]

    reconnect = receiver.get(
        "/linkup/messages/incoming",
        query_string={
            "peer_id": USER_A,
            "after": messages[0]["created_at"],
            "after_id": message_id,
        },
    )
    assert reconnect.status_code == 200
    assert reconnect.get_json()["messages"] == []

    sender.close()
    receiver.close()
