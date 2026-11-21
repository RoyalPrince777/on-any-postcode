"""SMI local offline entry must never bypass private SMI authentication."""
from pathlib import Path

from app import app


def test_offline_expose_requires_local_mode(monkeypatch):
    monkeypatch.delenv("OAP_LOCAL_MODE", raising=False)
    with app.test_client() as client:
        response = client.get("/offline/smi")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"


def test_offline_expose_rejects_remote_clients(monkeypatch):
    monkeypatch.setenv("OAP_LOCAL_MODE", "true")
    with app.test_client() as client:
        response = client.get(
            "/offline/smi",
            environ_overrides={"REMOTE_ADDR": "192.0.2.10"},
        )
    assert response.status_code == 404


def test_offline_expose_rejects_non_local_host(monkeypatch):
    monkeypatch.setenv("OAP_LOCAL_MODE", "true")
    with app.test_client() as client:
        response = client.get(
            "/offline/smi",
            base_url="https://onanypostcode.global",
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        )
    assert response.status_code == 404


def test_offline_expose_is_static_and_has_no_private_data(monkeypatch):
    monkeypatch.setenv("OAP_LOCAL_MODE", "true")
    with app.test_client() as client:
        response = client.get(
            "/offline/smi",
            base_url="http://127.0.0.1:5050",
            environ_overrides={"REMOTE_ADDR": "127.0.0.1"},
        )
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "LOCAL · OFFLINE" in text
    assert "Green held" in text
    assert "No live evidence has been checked" in text
    assert response.headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert "<script" not in text.lower()
    assert 'href="https://' not in text.lower()


def test_offline_expose_does_not_replace_private_smi():
    root = Path(__file__).resolve().parents[1]
    src = (root / "app.py").read_text(encoding="utf-8")
    assert '@app.get("/offline/smi")' in src
    assert 'os.environ.get("OAP_LOCAL_MODE"' in src
    assert '"smi-offline-expose.html"' in src
    assert '@web_security.login_required()' in (
        root / "mission_control" / "views.py"
    ).read_text(encoding="utf-8")
