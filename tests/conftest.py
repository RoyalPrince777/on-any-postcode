from __future__ import annotations

import pytest

import app as app_module
from mission_control import config, status


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_path = tmp_path / "uninitialized-oap.db"
    monkeypatch.setattr(config, "OAP_DATABASE_PATH", str(database_path))
    monkeypatch.setattr(status, "_probe_ollama", lambda: False)

    app_module.app.config.update(TESTING=True)
    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()

    with app_module.app.test_client() as test_client:
        yield test_client

    app_module.signal_posts.clear()
    app_module.team_messages.clear()
    app_module.flag_counts.clear()
    app_module.profiles.clear()
