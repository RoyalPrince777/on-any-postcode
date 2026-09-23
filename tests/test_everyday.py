"""First-party Everyday scope and Command Centre placement regressions."""
from pathlib import Path

import pytest

from oap.everyday import CATEGORIES, catalogue, propose_partner

ROOT = Path(__file__).resolve().parents[1]


def test_seven_everyday_categories_without_fake_ready():
    data = catalogue()
    assert data["name"] == "OAP EVERYDAY"
    assert len(data["categories"]) == len(CATEGORIES) == 7
    assert {x["key"] for x in data["categories"]} == {
        "essentials", "energy", "move", "families", "support", "rewards", "partners"
    }
    assert all(x["status"] == "planned" for x in data["categories"])
    assert not data["entries_open"] and not data["payments_enabled"]
    assert not data["prizes_secured"] and data["partners_confirmed"] == 0
    assert not data["public_launch_authorised"]


def test_direct_support_is_separate_from_free_draw():
    data = catalogue()
    assert data["direct_support_requires_draw_entry"] is False
    assert data["rewards_engine"] == "existing_oap_raffles"
    assert data["external_provider_required"] is False


def test_proposed_partner_does_not_fake_a_deal_or_contact():
    proposal = propose_partner(organisation="Local shop",
                               prize_description="Groceries voucher")
    assert proposal["status"] == "proposed_unverified"
    for key in ("contact_sent", "partner_committed", "prize_secured",
                "public_listing_allowed", "entries_open", "payments_enabled"):
        assert proposal[key] is False


def test_partner_proposal_rejects_invalid_content():
    for organisation, prize in (("", "Voucher"), ("Shop", ""), ("A" * 121, "Voucher"),
                                ("Shop", "x" * 281)):
        with pytest.raises(ValueError):
            propose_partner(organisation=organisation, prize_description=prize)


def test_everyday_is_private_programme_route_not_a_second_raffles_engine():
    routes = (ROOT / "mission_control/raffles_command_views.py").read_text()
    mission = (ROOT / "mission_control/templates/mission.html").read_text()
    page = (ROOT / "mission_control/templates/everyday_command.html").read_text()
    assert '@bp.get("/everyday")' in routes
    assert "def everyday_dashboard()" in routes
    assert "login_required(founder_only=True)" in routes
    assert "url_for('raffles_command.everyday_dashboard')" in mission
    assert "url_for('raffles_command.dashboard')" in page
    assert "No new payment engine" in page
