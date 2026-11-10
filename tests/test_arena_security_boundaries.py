from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
ROOMS = ROOT / "mission_control" / "arena_rooms.py"
IQ_DUEL = ROOT / "mission_control" / "iq_duel.py"

MUTATION_ROUTES = (
    "arena_room_create",
    "arena_room_join",
    "arena_room_state",
    "arena_room_state_update",
    "arena_room_connect4_action",
    "arena_room_dot_action",
    "arena_room_chess_action",
    "arena_room_ludo_action",
    "arena_room_oware_action",
    "arena_room_iq_action",
    "arena_room_route_empire_action",
)


def _function_source(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"missing function: {name}")


def test_all_arena_room_mutations_enter_csrf_rate_guard_before_adapter_call():
    for name in MUTATION_ROUTES:
        source = _function_source(APP, name)
        guard = source.find("_arena_write_allowed()")
        adapter = source.find("arena_rooms.")
        assert guard >= 0, name
        assert adapter > guard, name


def test_room_state_is_server_owned_hashed_and_revision_locked():
    source = ROOMS.read_text(encoding="utf-8")
    assert "hashlib.sha256(value.encode" in source
    assert "reconnect_token_hash" in source
    assert "FOR UPDATE" in source
    assert "arena_room_revision_conflict" in source
    assert "arena_room_idempotency_conflict" in source
    assert "action_hash" in source
    assert "WHERE room_id=%s AND revision=%s" in source
    assert 'raise ValueError("arena_room_server_game_adapter_required")' in source


def test_new_room_clients_do_not_persist_private_reconnect_tokens_in_browser_storage():
    for filename in (
        "arena_ludo_room.js",
        "arena_oware_room.js",
        "arena_iq_room.js",
        "arena_route_empire_room.js",
    ):
        source = (ROOT / "static" / filename).read_text(encoding="utf-8")
        assert "localStorage" not in source
        assert "sessionStorage" not in source
        assert "document.cookie" not in source
        assert "reconnect_token" in source


def test_iq_duel_public_projection_never_exposes_correct_answer():
    source = _function_source(IQ_DUEL, "public_state")
    assert 'raw["answer"]' not in source
    assert '"answer":' not in source
    assert "clinical_iq_score" in source
    assert "skill_profile_only" in source


def test_room_pages_enforce_no_referrer_boundary():
    for filename in (
        "arena_ludo_room.html",
        "arena_oware_room.html",
        "arena_iq_room.html",
        "arena_route_empire_room.html",
    ):
        source = (ROOT / "mission_control" / "templates" / filename).read_text(encoding="utf-8")
        assert 'name="referrer" content="no-referrer"' in source
