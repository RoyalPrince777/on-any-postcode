"""Regression tests for conservative SMI contextual intelligence routing."""
from mission_control.intelligence_lenses import route, public_route


def test_contextual_work_request():
    result = route("How can I earn money without capital?")
    assert result["mode"] == "contextual"
    assert result["lens_ids"] == ("opportunity", "priority", "risk")


def test_contextual_security_request():
    result = route("Is this safe?")
    assert result["lens_ids"] == ("risk", "security", "evidence")
    assert public_route("Is this safe?")["execution_granted"] is False


def test_explicit_route_takes_precedence():
    result = route("Run truth intelligence on how to earn money")
    assert result["mode"] == "single"
    assert result["lens_ids"] == ("truth",)


def test_unrelated_chat_remains_inactive():
    assert route("Hello, how are you?")["active"] is False


def test_full_route_unchanged():
    assert route("Run full intelligence on OAP World")["mode"] == "full"
