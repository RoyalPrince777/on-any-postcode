from pathlib import Path


def test_war_room_exposes_bounded_a3_pilot_without_claiming_runtime():
    page = Path("mission_control/templates/war_room.html").read_text(encoding="utf-8")

    assert "A3 bounded pilot" in page
    assert "RUNTIME_HEARTBEAT" in page
    assert "RUNTIME_HEALTH_PROBE" in page
    assert "24/7 Organism Runtime" in page
    assert "fresh worker heartbeat" in page
    assert "A4 / A5 remain locked" in page
    assert (
        "money, migrations, auth, dispatch, publishing and unreviewed deploys remain outside A3"
        in page
    )
