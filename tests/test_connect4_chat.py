"""Bounded Connect 4 room chat contract checks; DB integration needs migrated test DB."""
import pytest

from mission_control import arena_connect4_chat


def test_room_chat_page_and_client_wiring(client):
    html = client.get("/arena/connect4/room").get_data(as_text=True)
    js = client.get("/static/arena_connect4_room.js").get_data(as_text=True)
    assert 'data-chat-log' in html
    assert 'data-chat-form' in html
    assert 'maxlength="280"' in html
    assert "no chat, payment" not in html
    assert "/arena/rooms/connect4/chat/read" in js
    assert "/arena/rooms/connect4/chat/send" in js
    assert "document.createTextNode(item.text)" in js


def test_chat_requires_csrf(client):
    assert client.post("/arena/rooms/connect4/chat/read", json={}).status_code == 403
    assert client.post("/arena/rooms/connect4/chat/send", json={}).status_code == 403


def test_chat_rejects_invalid_room_or_message_before_db():
    with pytest.raises(ValueError, match="arena_room_id_invalid"):
        arena_connect4_chat.read(room_id="not-a-uuid", reconnect_token="x" * 40)
    with pytest.raises(ValueError, match="arena_chat_message_invalid"):
        arena_connect4_chat.send(
            room_id="00000000-0000-4000-8000-000000000001",
            reconnect_token="x" * 40,
            request_id="msg-invalid-001",
            message=" " * 12,
        )
    with pytest.raises(ValueError, match="arena_chat_message_invalid"):
        arena_connect4_chat.send(
            room_id="00000000-0000-4000-8000-000000000001",
            reconnect_token="x" * 40,
            request_id="msg-invalid-002",
            message="x" * 281,
        )
