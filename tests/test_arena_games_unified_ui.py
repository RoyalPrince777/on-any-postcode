"""Route-level regression for the unified first-party Arena gaming interface."""

import pytest


@pytest.mark.parametrize("route,heading", [
    ("/arena/route-empire", "Route Empire"),
    ("/arena/iq", "IQ Arena"),
    ("/arena/ludo", "Ludo"),
    ("/arena/chess", "Chess"),
    ("/arena/dot", "Dot"),
    ("/arena/connect4", "Connect 4"),
    ("/arena/dot/room", "Dot"),
    ("/arena/connect4/room", "Connect 4"),
])
def test_games_share_mobile_shell_navigation_and_first_party_controls(client, route, heading):
    response = client.get(route)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert heading in html
    assert "arena_games.css" in html
    assert "mc-shell arena-game" in html
    assert 'href="/arena"' in html
    assert 'name="viewport"' in html
    assert 'name="oap-csrf-token"' in html


@pytest.mark.parametrize("route", ["/arena/ludo", "/arena/chess", "/arena/dot"])
def test_local_games_label_moves_and_start_with_stop_disabled(client, route):
    html = client.get(route).get_data(as_text=True)
    assert 'data-start' in html
    assert 'data-stop disabled' in html
    assert 'role="alert"' in html
    assert 'aria-live="polite"' in html
    if route == "/arena/chess":
        assert 'class="arena-chess-board"' in html
        assert 'data-source' in html and 'data-target' in html
    if route == "/arena/ludo":
        assert 'data-step="1"' in html and 'data-step="6"' in html
    if route == "/arena/dot":
        assert 'data-edges' in html and 'data-score' in html


def test_arena_shared_css_preserves_small_screen_and_keyboard_access(client):
    response = client.get("/static/arena_games.css")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    assert "grid-template-columns:repeat(7,minmax(0,1fr))" in css
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert ".arena-chess-board" in css
