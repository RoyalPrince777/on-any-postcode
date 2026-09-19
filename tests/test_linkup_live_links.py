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


def test_linkup_client_pulls_new_links_and_supports_seen():
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
    assert "Seen" in page
    assert "data-oap-ping-control" not in page
    assert "data-oap-ping-mute" not in page
    assert "linkup_ping.js" not in page
    assert "data-oap-incoming-pings" not in page


def test_linkup_server_messages_have_live_sync_identity():
    page = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'data-link-message-id="{{ message.message_id }}"' in page
    assert 'data-created-at="{{ message.created_at }}"' in page
