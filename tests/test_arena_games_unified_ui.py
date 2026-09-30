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


def test_connect4_prevents_overlapping_agent_turns_and_exposes_bounded_recovery(client):
    html = client.get("/arena/connect4").get_data(as_text=True)
    assert "data-retry-agent hidden" in html
    script = client.get("/static/connect4.js").get_data(as_text=True)
    assert "let state=null,agentMode=false,busy=false" in script
    assert "if(busy)return" in script
    assert 'q("[data-mode]").disabled=busy||state?.status==="active"' in script
    assert 'q("[data-agent]").disabled=busy||state?.status==="active"' in script
    assert "q(\"[data-retry-agent]\").hidden=false" in script
    assert "runAgent().catch(error).finally" in script


def test_chess_board_selection_guards_turn_and_restores_keyboard_focus(client):
    script = client.get("/static/chess.js").get_data(as_text=True)
    assert "Select one of your own pieces to begin." in script
    assert 'const ownColour=state.turn==="White"?"w":"b";' in script
    assert 'q(\'[data-square="\'+id+\'"]\')?.focus()' in script
    assert 'q("[data-target]").value="";' in script


@pytest.mark.parametrize("game,path", [
    ("Connect 4", "/static/connect4.js"),
    ("IQ Arena", "/static/iq_arena.js"),
    ("Ludo", "/static/ludo.js"),
    ("Chess", "/static/chess.js"),
    ("Dot", "/static/dot.js"),
    ("Route Empire", "/static/route_empire.js"),
])
def test_active_game_lifecycle_prevents_silent_restart(client, game, path):
    response = client.get(path)
    assert response.status_code == 200, game
    script = response.get_data(as_text=True)
    assert 'state?.status==="active"' in script, game
    assert "busy" in script, game
    assert ('q("[data-start]").disabled' in script or \
            'start.disabled=busy||state?.status==="active"' in script), game


def test_iq_choices_use_dom_nodes_and_single_request_guard(client):
    script = client.get("/static/iq_arena.js").get_data(as_text=True)
    assert "node.replaceChildren()" in script
    assert "button.textContent=choice.label" in script
    assert "if(busy||" in script
    assert 'button.disabled=busy||state.status!=="active"' in script


def test_route_empire_serializes_mutations_and_escapes_both_node_ids(client):
    script = client.get("/static/route_empire.js").get_data(as_text=True)
    assert "let state=null,busy=false" in script
    assert 'data-act="claim" data-node="${escapeText(n.id)}"' in script
    assert 'data-act="develop" data-node="${escapeText(n.id)}"' in script
    assert 'b.disabled=busy||state.status!=="active"' in script
