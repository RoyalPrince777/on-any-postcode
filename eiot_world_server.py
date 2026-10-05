"""Dedicated EARTH IS OUR TURF authoritative M Town world-server process."""
from __future__ import annotations

import threading
import uuid

from flask import Flask, jsonify, request

from mission_control import (
    mtown_endless_world,
    mtown_persistence,
    mtown_persistence_broker,
    mtown_world_server,
)

app=Flask(__name__)
_LOCK=threading.RLock()
_WORLDS:dict[str,dict]={}

def _payload()->dict:
    value=request.get_json(silent=True) or {}
    if not isinstance(value,dict):
        raise TypeError("invalid_request")
    return value

@app.get("/healthz")
def healthz():
    return jsonify({
        "ok":True,
        "service":"eiot-mtown-world-server",
        "authoritative":True,
        "active_worlds":len(_WORLDS),
        "persistence":{
            "local":mtown_persistence.status(),
            "broker":mtown_persistence_broker.status(),
        },
    })

@app.post("/v1/worlds")
def create_world():
    with _LOCK:
        world=mtown_world_server.new_session()
        world_id=str(world["world"]["world_id"])
        _WORLDS[world_id]=world
    return jsonify({"world_id":world_id,"state":world["world"],"server":world["server"]}),201

@app.get("/v1/worlds/<world_id>")
def read_world(world_id:str):
    with _LOCK:
        world=_WORLDS.get(world_id)
        if world is None:return jsonify({"error":"eiot_world_not_found"}),404
        return jsonify({"world_id":world_id,"state":world["world"],"server":world["server"]})

@app.post("/v1/worlds/<world_id>/action")
def world_action(world_id:str):
    try:
        payload=_payload()
        with _LOCK:
            current=_WORLDS.get(world_id)
            if current is None:return jsonify({"error":"eiot_world_not_found"}),404
            updated=mtown_world_server.act(
                current,
                command=payload.get("command"),
                target=payload.get("target"),
                mode=payload.get("mode"),
                distance=payload.get("distance"),
            )
            _WORLDS[world_id]=updated
        return jsonify({"world_id":world_id,"state":updated["world"],"server":updated["server"]})
    except (TypeError,ValueError) as exc:
        return jsonify({"error":str(exc)}),400

@app.post("/v1/worlds/<world_id>/save")
def save_world(world_id:str):
    try:
        payload=_payload()
        player_ref=str(payload.get("player_ref") or "").strip()
        with _LOCK:
            current=_WORLDS.get(world_id)
            if current is None:return jsonify({"error":"eiot_world_not_found"}),404
            if mtown_persistence.status()["durable_ready"]:
                saved=mtown_world_server.save(session=current,player_ref=player_ref)
            else:
                saved=mtown_persistence_broker.save(
                    player_ref=player_ref,
                    state=current["world"],
                )
        return jsonify(saved),201
    except (TypeError,ValueError,RuntimeError) as exc:
        return jsonify({"error":str(exc)}),400

@app.post("/v1/worlds/reconnect")
def reconnect_world():
    try:
        payload=_payload()
        if mtown_persistence.status()["durable_ready"]:
            restored=mtown_world_server.reconnect(token=payload.get("reconnect_token"))
        else:
            loaded=mtown_persistence_broker.reconnect(token=payload.get("reconnect_token"))
            restored={
                "world":loaded["world_state"],
                "server":{"authoritative":True,"tick":0},
                "save":{
                    "save_id":loaded["save_id"],
                    "revision":loaded["revision"],
                    "player_ref":loaded["player_ref"],
                },
            }
        world_id=str(restored["world"]["world_id"])
        with _LOCK:_WORLDS[world_id]={"world":restored["world"],"server":restored["server"]}
        return jsonify({"world_id":world_id,**restored})
    except (TypeError,ValueError,RuntimeError) as exc:
        return jsonify({"error":str(exc)}),400

@app.get("/v1/world/cells")
def world_cells():
    try:
        x=int(request.args.get("x","0"))
        y=int(request.args.get("y","0"))
        radius=int(request.args.get("radius","2"))
        return jsonify({"cells":mtown_endless_world.ring(center_x=x,center_y=y,radius=radius)})
    except (TypeError,ValueError) as exc:
        return jsonify({"error":str(exc)}),400

@app.get("/v1/world/persistence/status")
def persistence_status():
    return jsonify(mtown_persistence.status())
