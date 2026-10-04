"""Dedicated EARTH IS OUR TURF world-server process."""
from __future__ import annotations
from flask import Flask, jsonify, request
from mission_control import mtown_endless_world, mtown_persistence
app=Flask(__name__)

@app.get("/healthz")
def healthz():
    return jsonify({"ok":True,"service":"eiot-mtown-world-server","authoritative":True})

@app.get("/v1/world/cells")
def world_cells():
    try:
        x=int(request.args.get("x","0")); y=int(request.args.get("y","0")); radius=int(request.args.get("radius","2"))
        return jsonify({"cells":mtown_endless_world.ring(center_x=x,center_y=y,radius=radius)})
    except (TypeError,ValueError) as exc:
        return jsonify({"error":str(exc)}),400

@app.get("/v1/world/persistence/status")
def persistence_status():
    return jsonify(mtown_persistence.status())
