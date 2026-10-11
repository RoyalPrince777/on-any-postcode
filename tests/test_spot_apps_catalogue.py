"""Focused fail-closed catalogue contract tests."""
from mission_control.spot_apps_catalogue import public_catalogue


def test_only_registered_routes_appear():
    assert [x["id"] for x in public_catalogue(registered_routes={"/pulse"}, public_routes={"/pulse"})] == ["pulse"]


def test_missing_routes_never_appear():
    assert public_catalogue(registered_routes=set(), public_routes=set()) == []


def test_search_is_case_insensitive_and_bounded():
    result = public_catalogue(registered_routes={"/pulse", "/arena"}, public_routes={"/pulse", "/arena"}, query="GAMES")
    assert [x["id"] for x in result] == ["arena"]


def test_no_user_supplied_route_is_launched():
    result = public_catalogue(registered_routes={"/evil", "https://example.invalid"}, public_routes={"/evil", "https://example.invalid"})
    assert result == []


def test_no_public_review_fails_closed():
    assert public_catalogue(registered_routes={"/pulse"}) == []


def test_registered_private_route_stays_hidden():
    assert public_catalogue(registered_routes={"/pulse", "/the-link"}, public_routes={"/pulse"}) == [
        {"id": "pulse", "name": "Pulse", "category": "Social", "route": "/pulse"}
    ]
