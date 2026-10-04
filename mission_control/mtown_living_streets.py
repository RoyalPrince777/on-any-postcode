"""M Town Living Streets v1.

Deterministic first-party simulation for traffic, pedestrians, entrances,
parking and persistent vehicle placement in EARTH IS OUR TURF.

All fine-grained entrances, parking bays and traffic actors are game-world data.
They do not claim precise real-world private access, CCTV coverage or live traffic.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

SCHEMA="oap.eiot.mtown-living-streets.v1"

ENTRANCES=(
    {"id":"entrance-town-local","label":"ON ANY POSTCODE Local","node":"town-centre","kind":"shop","foot":True,"bike":False,"car":False,"public":True},
    {"id":"entrance-town-market","label":"ON ANY POSTCODE Market","node":"town-centre","kind":"shop","foot":True,"bike":False,"car":False,"public":True},
    {"id":"entrance-garage","label":"ON ANY POSTCODE Garage","node":"lower-mitcham","kind":"garage","foot":True,"bike":True,"car":True,"public":True},
    {"id":"entrance-mobility","label":"ON ANY POSTCODE Mobility","node":"eastfields","kind":"mobility","foot":True,"bike":True,"car":False,"public":True},
    {"id":"entrance-lavender-local","label":"ON ANY POSTCODE Lavender Local","node":"lavender-avenue","kind":"shop","foot":True,"bike":False,"car":False,"public":True},
    {"id":"entrance-phipps-local","label":"ON ANY POSTCODE Phipps Local","node":"phipps-bridge","kind":"shop","foot":True,"bike":False,"car":False,"public":True},
    {"id":"entrance-laburnum-local","label":"ON ANY POSTCODE Laburnum Local","node":"laburnum-road","kind":"shop","foot":True,"bike":False,"car":False,"public":True},
    {"id":"entrance-figges","label":"Figge's Marsh public gate","node":"figges-marsh","kind":"park","foot":True,"bike":True,"car":False,"public":True,"fictional_detail":True},
    {"id":"entrance-ravensbury","label":"Ravensbury public gate","node":"ravensbury","kind":"park","foot":True,"bike":True,"car":False,"public":True,"fictional_detail":True},
)

PARKING=(
    {"id":"park-town-01","node":"town-centre","kind":"street","capacity":6,"public":True,"fictional_detail":True},
    {"id":"park-western-01","node":"western-road","kind":"street","capacity":4,"public":True,"fictional_detail":True},
    {"id":"park-lavender-01","node":"lavender-avenue","kind":"street","capacity":4,"public":True,"fictional_detail":True},
    {"id":"park-eastfields-01","node":"eastfields","kind":"mobility","capacity":5,"public":True,"fictional_detail":True},
    {"id":"park-laburnum-01","node":"laburnum-road","kind":"estate","capacity":4,"public":True,"fictional_detail":True},
    {"id":"park-lower-01","node":"lower-mitcham","kind":"garage","capacity":8,"public":True,"fictional_detail":True},
    {"id":"park-common-01","node":"mitcham-common","kind":"edge","capacity":5,"public":True,"fictional_detail":True},
)

VEHICLE_SEEDS=(
    {"id":"vehicle-oap-001","label":"OAP Metro Hatch","class":"hatchback","node":"town-centre","parking_id":"park-town-01","status":"parked","owner":"world"},
    {"id":"vehicle-oap-002","label":"OAP Crown Saloon","class":"saloon","node":"western-road","parking_id":"park-western-01","status":"parked","owner":"world"},
    {"id":"vehicle-oap-003","label":"OAP Atlas Van","class":"van","node":"lower-mitcham","parking_id":"park-lower-01","status":"parked","owner":"oap-garage"},
    {"id":"vehicle-oap-004","label":"OAP Spark EV","class":"ev","node":"eastfields","parking_id":"park-eastfields-01","status":"parked","owner":"oap-mobility"},
)

PEDESTRIAN_ARCHETYPES=(
    "commuter","shopper","walker","worker","student","elder","visitor",
)

def _canonical(value: object) -> str:
    return json.dumps(value,separators=(",",":"),sort_keys=True,ensure_ascii=False)

def _stable_int(*parts: object, modulo: int=100) -> int:
    digest=hashlib.sha256(_canonical(parts).encode()).hexdigest()
    return int(digest[:12],16)%modulo

def new_state() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "tick":0,
        "vehicles":[copy.deepcopy(v) for v in VEHICLE_SEEDS],
        "parking":[dict(p,occupied=0) for p in PARKING],
        "entrances":[copy.deepcopy(e) for e in ENTRANCES],
        "last_snapshot":None,
        "truth":{
            "live_traffic_claimed":False,
            "exact_private_access_claimed":False,
            "precise_parking_geometry_claimed":False,
            "real_person_tracking":False,
        },
    }

def validate(state: object) -> dict[str,Any]:
    errors=[]
    if not isinstance(state,dict):
        return {"passed":False,"errors":["mtown_living_state_missing"]}
    if state.get("schema")!=SCHEMA:
        errors.append("mtown_living_schema_invalid")
    if not isinstance(state.get("vehicles"),list):
        errors.append("mtown_living_vehicles_invalid")
    if not isinstance(state.get("parking"),list):
        errors.append("mtown_living_parking_invalid")
    return {"passed":not errors,"errors":errors}

def _traffic_count(*, node_id: str, minute: int, day: int, traffic_score: int) -> int:
    base=max(0,int(traffic_score)//12)
    variance=_stable_int(node_id,minute//15,day,"traffic",modulo=4)
    return min(12,base+variance)

def _pedestrian_count(*, node_id: str, minute: int, day: int, footfall: int) -> int:
    base=max(0,int(footfall)//10)
    variance=_stable_int(node_id,minute//10,day,"footfall",modulo=5)
    return min(16,base+variance)

def snapshot(
    state: object,
    *,
    node_id: object,
    minute: object,
    day: object,
    environment: dict[str,Any],
    loaded_chunks: list[str],
    node_to_chunk: dict[str,str],
) -> tuple[dict[str,Any],dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    node=str(node_id or "")
    minute_i=int(minute)
    day_i=int(day)
    out=copy.deepcopy(state)
    out["tick"]=int(out.get("tick",0))+1

    live_nodes=[key for key,chunk in node_to_chunk.items() if chunk in set(loaded_chunks)]
    traffic=[]
    pedestrians=[]
    for nid in live_nodes:
        local_traffic=_traffic_count(
            node_id=nid,
            minute=minute_i,
            day=day_i,
            traffic_score=int(environment["traffic"]) if nid==node else max(18,int(environment["traffic"])*2//3),
        )
        for idx in range(local_traffic):
            traffic.append({
                "id":f"traffic-{nid}-{idx}",
                "node":nid,
                "class":("hatchback","saloon","van","ev")[_stable_int(nid,idx,day_i,modulo=4)],
                "state":"moving",
                "game_actor":True,
            })
        local_people=_pedestrian_count(
            node_id=nid,
            minute=minute_i,
            day=day_i,
            footfall=int(environment["footfall"]) if nid==node else max(12,int(environment["footfall"])*2//3),
        )
        for idx in range(local_people):
            pedestrians.append({
                "id":f"ped-{nid}-{idx}",
                "node":nid,
                "archetype":PEDESTRIAN_ARCHETYPES[_stable_int(nid,idx,minute_i//30,modulo=len(PEDESTRIAN_ARCHETYPES))],
                "persistent":False,
                "game_actor":True,
            })

    parking=[]
    for row in out["parking"]:
        occupancy=min(
            int(row["capacity"]),
            _stable_int(row["id"],day_i,minute_i//30,modulo=int(row["capacity"])+1),
        )
        row["occupied"]=occupancy
        row["available"]=max(0,int(row["capacity"])-occupancy)
        parking.append(copy.deepcopy(row))

    snapshot_view={
        "traffic":traffic,
        "pedestrians":pedestrians,
        "parking":parking,
        "entrances":[copy.deepcopy(e) for e in out["entrances"] if e["node"] in live_nodes],
        "persistent_vehicles":[copy.deepcopy(v) for v in out["vehicles"] if node_to_chunk.get(v["node"]) in set(loaded_chunks)],
        "counts":{
            "moving_traffic":len(traffic),
            "pedestrians":len(pedestrians),
            "persistent_vehicles":sum(1 for v in out["vehicles"] if node_to_chunk.get(v["node"]) in set(loaded_chunks)),
            "entrances":sum(1 for e in out["entrances"] if e["node"] in live_nodes),
        },
        "source":"game_living_streets_simulation_v1",
        "live_claim":False,
    }
    out["last_snapshot"]={
        "node":node,
        "minute":minute_i,
        "day":day_i,
        "counts":copy.deepcopy(snapshot_view["counts"]),
    }
    return out,snapshot_view

def park_vehicle(state: object, *, vehicle_id: object, parking_id: object) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    vid=str(vehicle_id or "").strip()
    pid=str(parking_id or "").strip()
    out=copy.deepcopy(state)
    vehicle=next((v for v in out["vehicles"] if v["id"]==vid),None)
    parking=next((p for p in out["parking"] if p["id"]==pid),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    if parking is None:
        raise ValueError("mtown_parking_invalid")
    vehicle["node"]=parking["node"]
    vehicle["parking_id"]=pid
    vehicle["status"]="parked"
    return out

def entrance_for(*, node_id: object, mode: object) -> list[dict[str,Any]]:
    node=str(node_id or "")
    travel=str(mode or "foot").strip().lower()
    if travel not in {"foot","bike","car"}:
        raise ValueError("mtown_entrance_mode_invalid")
    return [
        copy.deepcopy(row)
        for row in ENTRANCES
        if row["node"]==node and bool(row.get(travel))
    ]

def status() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town Living Streets",
        "version":1,
        "traffic_simulation":True,
        "pedestrian_simulation":True,
        "persistent_vehicle_position":True,
        "entrance_intelligence":True,
        "parking_intelligence":True,
        "live_traffic_claimed":False,
        "precise_private_access_claimed":False,
    }
