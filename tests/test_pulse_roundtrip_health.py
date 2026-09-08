from pathlib import Path

from mission_control import pulse_routes

ROOT = Path(__file__).resolve().parents[1]


def test_pulse_roundtrip_probe_is_residue_free():
    text = (ROOT / "mission_control" / "pulse_routes.py").read_text()

    assert "connection.rollback()" in text
    assert "oap-pulse-probe-" in text
    assert "EXISTS(SELECT 1 FROM users WHERE id=%s)" in text
    assert "EXISTS(SELECT 1 FROM posts WHERE id=%s)" in text
    assert "@app.get(\"/pulse/health\")" in text


def test_pulse_health_exposes_only_coarse_success(client, monkeypatch):
    monkeypatch.setattr(pulse_routes, "_roundtrip_probe", lambda: True)

    response = client.get("/pulse/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}
    assert response.headers["Cache-Control"] == "no-store"


def test_pulse_health_fails_closed(client, monkeypatch):
    monkeypatch.setattr(pulse_routes, "_roundtrip_probe", lambda: False)

    response = client.get("/pulse/health")

    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
