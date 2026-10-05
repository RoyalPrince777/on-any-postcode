"""Regression coverage for EIOT first-party persistence broker."""
import os

import app as core_app
import eiot_world_server
from mission_control import mtown_persistence_broker


def test_core_broker_rejects_missing_service_key(client, monkeypatch):
    monkeypatch.setenv("OAP_EIOT_SERVICE_KEY","test-secret")
    response=client.post("/internal/eiot/persistence/init",json={})
    assert response.status_code==403
    assert response.get_json()["error"]=="eiot_service_forbidden"


def test_core_broker_init_accepts_matching_key(client, monkeypatch):
    monkeypatch.setenv("OAP_EIOT_SERVICE_KEY","test-secret")
    monkeypatch.setattr(core_app.mtown_persistence,"ensure_schema",lambda:None)
    monkeypatch.setattr(
        core_app.mtown_persistence,
        "status",
        lambda:{"configured":True,"durable_ready":True},
    )
    response=client.post(
        "/internal/eiot/persistence/init",
        json={},
        headers={"X-EIOT-Service-Key":"test-secret"},
    )
    assert response.status_code==200
    assert response.get_json()["durable_ready"] is True


def test_world_server_uses_broker_when_local_db_is_unconfigured(monkeypatch):
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence,
        "status",
        lambda:{"configured":False,"durable_ready":False},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "save",
        lambda **kwargs:{
            "save_id":"save-1",
            "world_id":kwargs["state"]["world_id"],
            "revision":1,
            "reconnect_token":"token-1",
        },
    )
    client=eiot_world_server.app.test_client()
    created=client.post("/v1/worlds").get_json()
    saved=client.post(
        f'/v1/worlds/{created["world_id"]}/save',
        json={"player_ref":"player-1"},
    )
    assert saved.status_code==201
    assert saved.get_json()["reconnect_token"]=="token-1"


def test_broker_config_requires_url_and_key(monkeypatch):
    monkeypatch.delenv("OAP_EIOT_PERSISTENCE_URL",raising=False)
    monkeypatch.delenv("OAP_EIOT_SERVICE_KEY",raising=False)
    assert mtown_persistence_broker.configured() is False
    monkeypatch.setenv("OAP_EIOT_PERSISTENCE_URL","https://example.invalid")
    monkeypatch.setenv("OAP_EIOT_SERVICE_KEY","key")
    assert mtown_persistence_broker.configured() is True
