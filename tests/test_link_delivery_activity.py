from __future__ import annotations

import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mission_control import link_activity, link_message_routes, product_store


class _Result:
    def __init__(self, row=None, rows=None, rowcount=0):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []
        self.committed = False

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        self.calls.append((normalized, params))
        return self.handler(normalized, params)

    def commit(self):
        self.committed = True


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def _allow_message_link(monkeypatch):
    monkeypatch.setattr(
        product_store.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        product_store.link_relationships, "accepted_between", lambda _first, _second: True
    )


def _allow_activity_link(monkeypatch):
    monkeypatch.setattr(
        link_activity.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_activity.link_relationships, "accepted_between", lambda _first, _second: True
    )


def test_activity_schema_is_explicit_short_lived_and_content_free():
    dry_run = link_activity.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_activity_v1"
    assert dry_run["applied"] is False
    assert "link_typing_activity" in joined
    assert "expires_at TIMESTAMPTZ NOT NULL" in joined
    assert "body" not in joined.casefold()
    assert "draft" not in joined.casefold()
    assert "keystroke" not in joined.casefold()
    assert link_activity.TYPING_TTL_SECONDS == 8


def test_typing_start_requires_current_safe_link(monkeypatch):
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    monkeypatch.setattr(
        link_activity.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_activity.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("typing must not write through Block"),
    )
    with pytest.raises(ValueError, match="link_blocked"):
        link_activity.set_typing(identity, peer, active=True)

    monkeypatch.setattr(
        link_activity.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_activity.link_relationships, "accepted_between", lambda _first, _second: False
    )
    with pytest.raises(ValueError, match="accepted_link_required"):
        link_activity.set_typing(identity, peer, active=True)


def test_typing_stop_remains_available_after_block(monkeypatch):
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    connection = _Connection(lambda _query, _params: _Result())
    monkeypatch.setattr(
        link_activity.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )
    monkeypatch.setattr(
        link_activity.linkup_safety,
        "blocked_between",
        lambda *_args: pytest.fail("stop must not require Block lookup"),
    )

    assert link_activity.set_typing(identity, peer, active=False) is False
    query, params = connection.calls[0]
    assert query.startswith("DELETE FROM link_typing_activity")
    assert params == (identity, peer)
    assert connection.committed is True


def test_typing_read_is_exact_reverse_pair(monkeypatch):
    _allow_activity_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    connection = _Connection(lambda _query, _params: _Result(row=(1,)))
    monkeypatch.setattr(
        link_activity.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    assert link_activity.peer_typing(identity, peer) is True
    query, params = connection.calls[0]
    assert "identity_id=%s AND peer_id=%s" in query
    assert "expires_at>CURRENT_TIMESTAMP" in query
    assert params == (peer, identity)


def test_text_link_block_and_relationship_guard_run_before_message_storage(monkeypatch):
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    monkeypatch.setattr(
        product_store.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        product_store.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("message DB must not be reached through Block"),
    )
    with pytest.raises(ValueError, match="link_blocked"):
        product_store.send_message(sender, recipient, "hello")

    monkeypatch.setattr(
        product_store.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        product_store.link_relationships, "accepted_between", lambda _first, _second: False
    )
    with pytest.raises(ValueError, match="accepted_link_required"):
        product_store.send_message(sender, recipient, "hello")


def test_successful_text_link_is_landed_only_after_insert_commit(monkeypatch):
    _allow_message_link(monkeypatch)
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    message_id = str(uuid.uuid4())

    def handler(query, params):
        if query.startswith("SELECT id FROM users"):
            return _Result(rows=[(sender,), (recipient,)])
        if query.startswith("SELECT COUNT(*) FROM messages"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO messages"):
            return _Result(row=(message_id,))
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        product_store.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    assert product_store.send_message(sender, recipient, "Born Local") == message_id
    assert connection.committed is True
    assert any(call[0].startswith("INSERT INTO messages") for call in connection.calls)


def test_message_states_are_exact_outgoing_pair_without_body(monkeypatch):
    _allow_message_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    first_id = str(uuid.uuid4())
    second_id = str(uuid.uuid4())
    landed_at = datetime.now(timezone.utc)
    seen_at = datetime.now(timezone.utc)
    connection = _Connection(
        lambda _query, _params: _Result(
            rows=[
                (first_id, seen_at, landed_at),
                (second_id, None, landed_at),
            ]
        )
    )
    monkeypatch.setattr(
        product_store.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(connection),
    )

    states = product_store.message_states(identity, peer)
    query, params = connection.calls[0]
    assert "sender_id=%s AND recipient_id=%s" in query
    assert params[:2] == (identity, peer)
    assert states[0]["state"] == "seen"
    assert states[1]["state"] == "landed"
    assert "body" not in states[0]


def test_delivery_status_requires_authentication(anonymous_client):
    response = anonymous_client.get("/linkup/messages/status")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_delivery_status_is_coarse_first_party_and_no_store(client, monkeypatch):
    monkeypatch.setattr(
        link_message_routes.product_store,
        "status",
        lambda: {"tables": {"messages": True}, "ready": True},
    )
    monkeypatch.setattr(
        link_message_routes.link_activity,
        "status",
        lambda: {
            "ready": True,
            "typing_ttl_seconds": 8,
        },
    )
    response = client.get("/linkup/messages/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ready"] is True
    assert payload["first_party"] is True
    assert payload["landed_semantics"] == "persisted_oap_data"
    assert payload["seen_semantics"] == "recipient_read_receipt"
    assert payload["typing_stores_content"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_message_api_requires_csrf(client):
    response = client.post(
        "/linkup/messages",
        json={"recipient_id": str(uuid.uuid4()), "body": "hello"},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_typing_api_requires_csrf(client):
    response = client.post(
        "/linkup/activity/typing",
        json={"peer_id": str(uuid.uuid4()), "active": True},
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_browser_controller_is_same_origin_retryable_and_syntax_valid():
    messages_js = Path("static/linkup_messages.js").read_text(encoding="utf-8")
    voice_js = Path("static/linkup_voice.js").read_text(encoding="utf-8")

    assert 'apiJson("/linkup/messages/status")' in messages_js
    assert 'apiJson("/linkup/messages"' in messages_js
    assert 'apiJson("/linkup/activity/typing"' in messages_js
    assert 'retry.textContent = "Retry"' in messages_js
    assert 'receipt.textContent = "Landed"' in messages_js
    assert '"Seen" : "Landed"' in messages_js
    assert 'credentials: "same-origin"' in messages_js
    assert "https://" not in messages_js
    assert "http://" not in messages_js
    assert "keystroke" not in messages_js.casefold()
    assert 'script.src = "/static/linkup_messages.js"' in voice_js

    node = shutil.which("node")
    if node:
        subprocess.run([node, "--check", "static/linkup_messages.js"], check=True)
        subprocess.run([node, "--check", "static/linkup_voice.js"], check=True)
