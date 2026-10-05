from pathlib import Path


def test_linkup_live_incoming_route_is_present():
    source = Path("mission_control/link_message_routes.py").read_text(encoding="utf-8")

    assert '@bp.get("/linkup/messages/incoming")' in source
    assert "peer_messages_since" in source
    assert "@web_security.login_required(api=True)" in source


def test_linkup_live_delta_store_is_guarded_by_accepted_link():
    source = Path("mission_control/product_store.py").read_text(encoding="utf-8")

    assert "def peer_messages_since(" in source
    assert "identity, peer = _link_guard(identity_id, peer_id)" in source
    assert "created_at>%s::timestamptz" in source
    assert "ORDER BY created_at ASC" in source


def test_linkup_client_pulls_new_links_and_supports_lit_receipts():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert "new URLSearchParams({ peer_id: peerId })" in script
    assert "/linkup/messages/incoming?${query.toString()}" in script
    assert "renderLiveLinks" in script
    assert "data-link-message-id" in script
    assert "/seen" in script
    assert "New Link landed" in script


def test_linkup_surface_focuses_on_link_not_ping():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "Type a Link…" in page
    assert "Landed" in page
    assert "Lit" in page
    assert "Seen" not in page
    assert "data-oap-ping-control" not in page
    assert "data-oap-ping-mute" not in page
    assert "linkup_ping.js" not in page
    assert "data-oap-incoming-pings" not in page


def test_linkup_server_messages_have_live_sync_identity():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'data-link-message-id="{{ message.message_id }}"' in page
    assert 'data-created-at="{{ message.created_at }}"' in page


def test_linkup_sender_delete_is_owner_scoped_and_csrf_guarded():
    store = Path("mission_control/product_store.py").read_text(encoding="utf-8")
    routes = Path("mission_control/link_message_routes.py").read_text(encoding="utf-8")
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert "def delete_message(sender_id: object, message_id: object)" in store
    assert "DELETE FROM messages WHERE id=%s AND sender_id=%s RETURNING id" in store
    assert '@bp.delete("/linkup/messages/<message_id>")' in routes
    assert "if guarded := _mutation_guard(identity):" in routes
    assert "product_store.delete_message(identity, message_id)" in routes
    assert "data-oap-delete-link" in page
    assert "message.direction == 'sent'" in page
    assert 'method: "DELETE"' in script
    assert "/linkup/messages/" in script


def test_linkup_optimistic_send_renders_once_inside_message_thread():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert 'host = panel?.querySelector(".linkup-messages")' in script
    assert "state.renderedMessageIds.add(messageId)" in script
    assert 'item.className = "linkup-message outgoing"' in script
    assert "item.dataset.linkMessageId = messageId" in script
    assert "host.appendChild(item)" in script
    assert "host.scrollTop = host.scrollHeight" in script
    assert 'item.className = "oap-link-local-receipt"' not in script


def test_linkup_live_polling_starts_when_conversation_is_opened():
    script = Path("static/linkup_messages.js").read_text(encoding="utf-8")

    assert 'window.addEventListener("oap:linkup-engaged"' in script
    assert 'form[data-oap-link-composer]' in script
    assert "if (form) startPolling(form)" in script


def test_linkup_chat_surface_does_not_expose_ptt():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert "data-oap-ptt-control" not in page
    assert "data-oap-ptt-stop" not in page
