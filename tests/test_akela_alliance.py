"""Akela relationship boundary contract tests."""
from mission_control.akela_alliance import akela_alliance_view, validate_akela_view


def test_akela_dual_pack_relationships_are_distinct():
    view = akela_alliance_view()
    assert validate_akela_view()["passed"]
    assert view["agent"] == "Akela"
    assert len(view["wolf_pack"]) == 6
    assert all(m["relationship"] == "family" for m in view["wolf_pack"])
    assert all(m["relationship"] == "mission"
               for m in view["mission_packs"][0]["members"])


def test_no_runtime_claims_or_new_authority():
    view = akela_alliance_view()
    assert view["runtime_verified"] is False
    assert view["authority_granted"] is False
    assert all(m["activity"] == "ASSIGNED_UNVERIFIED"
               for m in view["mission_packs"][0]["members"])


def test_projection_is_detached():
    view = akela_alliance_view()
    view["wolf_pack"][0]["name"] = "changed"
    assert akela_alliance_view()["wolf_pack"][0]["name"] == "Akela"
