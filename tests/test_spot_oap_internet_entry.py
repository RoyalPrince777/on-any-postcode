"""OAP Internet Spot entry: route exists, no invented install state."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_spot_exposes_oap_internet_open_not_fake_install():
    source = (ROOT / "mission_control/templates/spot.html").read_text()
    assert 'href="/world" data-spot-internet-entry' in source
    assert '🌐 OAP Internet · Open' in source
    assert 'href="/store" data-spot-apps-entry' in source


def test_spot_internet_entry_serves_existing_world(client):
    response = client.get("/the-spot")
    assert response.status_code == 200
    assert b'data-spot-internet-entry' in response.data
    assert client.get("/world").status_code == 200
