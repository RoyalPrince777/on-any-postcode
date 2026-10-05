"""Live production acceptance proof for EARTH IS OUR TURF M Town."""
from __future__ import annotations

import json
import os
import sys
from urllib import error as urlerror
from urllib import request as urlrequest

BASE=os.environ.get("EIOT_WORLD_URL","https://eiot-mtown-world.onrender.com").rstrip("/")

def _request(path:str, *, payload:dict|None=None) -> tuple[int,dict]:
    data=None
    headers={}
    method="GET"
    if payload is not None:
        data=json.dumps(payload,separators=(",",":")).encode()
        headers["Content-Type"]="application/json"
        method="POST"
    req=urlrequest.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urlrequest.urlopen(req,timeout=30) as response:
            return response.status,json.loads(response.read().decode())
    except urlerror.HTTPError as exc:
        try:
            body=json.loads(exc.read().decode())
        except Exception:
            body={"error":"http_error"}
        return exc.code,body

def _require(condition:bool, message:str)->None:
    if not condition:
        raise AssertionError(message)

def main()->int:
    status,health=_request("/healthz")
    _require(status==200,"healthz_status")
    _require(health.get("authoritative") is True,"healthz_authority")
    persistence=health.get("persistence") or {}
    proof=persistence.get("proof") or {}
    broker=persistence.get("broker") or {}
    _require(broker.get("configured") is True,"broker_not_configured")
    _require(proof.get("attempted") is True,"persistence_proof_not_attempted")
    _require(
        proof.get("ready") is True,
        "persistence_proof_not_ready:"
        + str(proof.get("error") or "none")
        + ":"
        + str(proof.get("backend") or "none"),
    )

    status,cells=_request("/v1/world/cells?x=250000&y=-250000&radius=1")
    _require(status==200,"cells_status")
    rows=cells.get("cells") or []
    _require(len(rows)==9,"cells_count")
    _require(all(row.get("exact_real_geometry_claimed") is False for row in rows),"cells_truth_boundary")

    status,created=_request("/v1/worlds",payload={})
    _require(status==201,"world_create_status")
    world_id=created.get("world_id")
    _require(bool(world_id),"world_id_missing")

    status,acted=_request(
        f"/v1/worlds/{world_id}/action",
        payload={"command":"help-local"},
    )
    _require(status==200,"world_action_status")
    expected_influence=((acted.get("state") or {}).get("player") or {}).get("influence")
    _require(expected_influence==2,"world_action_state")

    player_ref=f"production-proof-{os.environ.get('GITHUB_SHA','manual')[:12]}"
    status,saved1=_request(
        f"/v1/worlds/{world_id}/save",
        payload={"player_ref":player_ref},
    )
    _require(status==201,"world_save_status")
    token1=saved1.get("reconnect_token")
    _require(bool(token1),"reconnect_token_missing")

    status,reconnected1=_request(
        "/v1/worlds/reconnect",
        payload={"reconnect_token":token1},
    )
    _require(status==200,"world_reconnect_status")
    restored1=reconnected1.get("world") or {}
    _require(restored1.get("world_id")==world_id,"reconnect_world_id_mismatch")
    _require((restored1.get("player") or {}).get("influence")==expected_influence,"reconnect_state_mismatch")

    status,saved2=_request(
        f"/v1/worlds/{world_id}/save",
        payload={"player_ref":player_ref},
    )
    _require(status==201,"world_resave_status")
    token2=saved2.get("reconnect_token")
    _require(bool(token2) and token2!=token1,"reconnect_token_not_rotated")

    old_status,_=_request(
        "/v1/worlds/reconnect",
        payload={"reconnect_token":token1},
    )
    _require(old_status==400,"old_reconnect_token_still_valid")

    status,reconnected2=_request(
        "/v1/worlds/reconnect",
        payload={"reconnect_token":token2},
    )
    _require(status==200,"rotated_reconnect_status")
    restored2=reconnected2.get("world") or {}
    _require(restored2.get("world_id")==world_id,"rotated_reconnect_world_id_mismatch")
    _require((restored2.get("player") or {}).get("influence")==expected_influence,"rotated_reconnect_state_mismatch")

    print(json.dumps({
        "eiot_production_live_proof":True,
        "health":True,
        "authoritative_world_server":True,
        "brokered_postgresql_persistence":True,
        "save_reconnect_roundtrip":True,
        "token_rotation":True,
        "endless_cells":True,
        "world_id":world_id,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
