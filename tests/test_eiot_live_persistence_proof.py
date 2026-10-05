"""Regression coverage for live EIOT persistence proof hardening."""
import eiot_world_server
from mission_control import mtown_persistence


class _Result:
    def __init__(self, one=None):
        self._one=one

    def fetchone(self):
        return self._one


class _Connection:
    def __init__(self):
        self.calls=[]
        self.commits=0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql,params))
        return _Result(("00000000-0000-0000-0000-000000000001","00000000-0000-0000-0000-00000000e107",2))

    def commit(self):
        self.commits+=1


def test_save_upsert_rotates_reconnect_token_hash(monkeypatch):
    connection=_Connection()
    monkeypatch.setattr(mtown_persistence.postgres_db,"connect",lambda **kwargs:connection)
    result=mtown_persistence.create_save(
        player_ref="player-1",
        state={"world_id":"00000000-0000-0000-0000-00000000e107"},
    )
    sql=connection.calls[0][0]
    assert "reconnect_token_hash=EXCLUDED.reconnect_token_hash" in sql
    assert result["revision"]==2
    assert connection.commits==1


def test_world_server_boot_proof_requires_roundtrip_match(monkeypatch):
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence,
        "status",
        lambda:{"durable_ready":False},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "configured",
        lambda:True,
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "initialize",
        lambda:{},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "save",
        lambda **kwargs:{"reconnect_token":"proof-token"},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "reconnect",
        lambda **kwargs:{
            "world_state":{
                "world_id":"00000000-0000-0000-0000-00000000e107",
                "probe":"eiot-persistence-v1",
            }
        },
    )
    eiot_world_server._PERSISTENCE_BOOT.update({
        "attempted":False,
        "ready":False,
        "backend":"none",
        "error":None,
    })
    eiot_world_server._boot_persistence()
    assert eiot_world_server._PERSISTENCE_BOOT["attempted"] is True
    assert eiot_world_server._PERSISTENCE_BOOT["ready"] is True
    assert eiot_world_server._PERSISTENCE_BOOT["backend"]=="oap-core-postgresql-broker"


def test_world_server_boot_proof_stays_red_on_mismatch(monkeypatch):
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence,
        "status",
        lambda:{"durable_ready":False},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "configured",
        lambda:True,
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "initialize",
        lambda:{"durable_ready":True},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "save",
        lambda **kwargs:{"reconnect_token":"proof-token"},
    )
    monkeypatch.setattr(
        eiot_world_server.mtown_persistence_broker,
        "reconnect",
        lambda **kwargs:{"world_state":{"world_id":"wrong"}},
    )
    eiot_world_server._PERSISTENCE_BOOT.update({
        "attempted":False,
        "ready":False,
        "backend":"none",
        "error":None,
    })
    eiot_world_server._boot_persistence()
    assert eiot_world_server._PERSISTENCE_BOOT["attempted"] is True
    assert eiot_world_server._PERSISTENCE_BOOT["ready"] is False
    assert eiot_world_server._PERSISTENCE_BOOT["error"]=="RuntimeError"
