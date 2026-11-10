"""M Town Vehicle Life v1.

First-party gameplay state machine for vehicle ownership, enter/exit, route-linked
driving, parking, NPC routine seeds and entrance-use receipts.
"""
from __future__ import annotations

import copy
from typing import Any

SCHEMA="oap.eiot.mtown-vehicle-life.v1"

def new_state() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "active_vehicle_id":None,
        "inside_vehicle":False,
        "last_entrance_id":None,
        "npc_routines":{
            "npc-shopper-001":{"role":"shopper","home":"lavender-avenue","routine":["town-centre","lavender-avenue"],"persistent":True},
            "npc-worker-001":{"role":"worker","home":"eastfields","routine":["eastfields","town-centre"],"persistent":True},
            "npc-driver-001":{"role":"driver","home":"lower-mitcham","routine":["lower-mitcham","town-centre","eastfields"],"persistent":True},
        },
        "truth":{
            "real_vehicle_claimed":False,
            "real_person_schedule_claimed":False,
            "exact_private_entrance_claimed":False,
        },
    }

def validate(state: object) -> dict[str,Any]:
    errors=[]
    if not isinstance(state,dict):
        return {"passed":False,"errors":["mtown_vehicle_life_state_missing"]}
    if state.get("schema")!=SCHEMA:
        errors.append("mtown_vehicle_life_schema_invalid")
    return {"passed":not errors,"errors":errors}

def claim_vehicle(
    state: object,
    *,
    character: dict[str,Any],
    living_streets: dict[str,Any],
    vehicle_id: object,
) -> tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    vid=str(vehicle_id or "").strip()
    if not vid:
        raise ValueError("mtown_vehicle_life_vehicle_invalid")
    life=copy.deepcopy(state)
    char=copy.deepcopy(character)
    streets=copy.deepcopy(living_streets)
    vehicle=next((v for v in streets.get("vehicles",[]) if v.get("id")==vid),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    if vehicle.get("node")!=char.get("movement",{}).get("node"):
        raise ValueError("mtown_vehicle_not_here")
    if vehicle.get("owner") not in {"world",char.get("character_id")}:
        raise ValueError("mtown_vehicle_claim_forbidden")
    owned=char.setdefault("owned",{}).setdefault("vehicles",[])
    if vid not in owned:
        owned.append(vid)
    vehicle["owner"]=char.get("character_id")
    return life,char,streets

def enter_vehicle(
    state: object,
    *,
    character: dict[str,Any],
    living_streets: dict[str,Any],
    vehicle_id: object,
) -> tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    vid=str(vehicle_id or "").strip()
    char=copy.deepcopy(character)
    streets=copy.deepcopy(living_streets)
    vehicle=next((v for v in streets.get("vehicles",[]) if v.get("id")==vid),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    if vehicle.get("node")!=char.get("movement",{}).get("node"):
        raise ValueError("mtown_vehicle_not_here")
    owned=char.setdefault("owned",{}).setdefault("vehicles",[])
    if vid not in owned:
        raise ValueError("mtown_vehicle_not_owned")
    life=copy.deepcopy(state)
    life["active_vehicle_id"]=vid
    life["inside_vehicle"]=True
    vehicle["status"]="occupied"
    vehicle["parking_id"]=None
    char["movement"]["mode"]="car"
    return life,char,streets

def exit_vehicle(
    state: object,
    *,
    character: dict[str,Any],
    living_streets: dict[str,Any],
) -> tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    life=copy.deepcopy(state)
    if not life.get("inside_vehicle") or not life.get("active_vehicle_id"):
        raise ValueError("mtown_vehicle_not_active")
    char=copy.deepcopy(character)
    streets=copy.deepcopy(living_streets)
    vehicle=next((v for v in streets.get("vehicles",[]) if v.get("id")==life["active_vehicle_id"]),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    vehicle["node"]=char["movement"]["node"]
    vehicle["status"]="stopped"
    char["movement"]["mode"]="foot"
    char["movement"]["speed"]=0.0
    life["inside_vehicle"]=False
    life["active_vehicle_id"]=None
    return life,char,streets

def sync_active_vehicle(
    state: object,
    *,
    character: dict[str,Any],
    living_streets: dict[str,Any],
) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    streets=copy.deepcopy(living_streets)
    if not state.get("inside_vehicle") or not state.get("active_vehicle_id"):
        return streets
    vehicle=next((v for v in streets.get("vehicles",[]) if v.get("id")==state["active_vehicle_id"]),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    movement=character.get("movement",{})
    vehicle["node"]=movement.get("node")
    vehicle["segment"]=copy.deepcopy(movement.get("segment"))
    vehicle["offset"]=movement.get("offset",0.0)
    vehicle["status"]="driving" if float(movement.get("speed") or 0)>0 else "occupied"
    vehicle["parking_id"]=None
    return streets

def park_active_vehicle(
    state: object,
    *,
    character: dict[str,Any],
    living_streets: dict[str,Any],
    parking_id: object,
) -> tuple[dict[str,Any],dict[str,Any],dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    if not state.get("inside_vehicle") or not state.get("active_vehicle_id"):
        raise ValueError("mtown_vehicle_not_active")
    pid=str(parking_id or "").strip()
    streets=copy.deepcopy(living_streets)
    parking=next((p for p in streets.get("parking",[]) if p.get("id")==pid),None)
    if parking is None:
        raise ValueError("mtown_parking_invalid")
    if parking.get("node")!=character.get("movement",{}).get("node"):
        raise ValueError("mtown_parking_not_here")
    vehicle=next((v for v in streets.get("vehicles",[]) if v.get("id")==state["active_vehicle_id"]),None)
    if vehicle is None:
        raise ValueError("mtown_vehicle_invalid")
    vehicle["node"]=parking["node"]
    vehicle["parking_id"]=pid
    vehicle["status"]="parked"
    char=copy.deepcopy(character)
    char["movement"]["mode"]="foot"
    char["movement"]["speed"]=0.0
    life=copy.deepcopy(state)
    life["inside_vehicle"]=False
    life["active_vehicle_id"]=None
    return life,char,streets

def use_entrance(state: object, *, entrance_id: object, entrances: list[dict[str,Any]], node_id: object, mode: object) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    eid=str(entrance_id or "").strip()
    travel=str(mode or "foot").strip().lower()
    row=next((e for e in entrances if e.get("id")==eid),None)
    if row is None:
        raise ValueError("mtown_entrance_invalid")
    if row.get("node")!=str(node_id or "") or not bool(row.get(travel)):
        raise ValueError("mtown_entrance_unavailable")
    life=copy.deepcopy(state)
    life["last_entrance_id"]=eid
    return life

def npc_positions(state: object, *, minute: object) -> list[dict[str,Any]]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    minute_i=int(minute)%1440
    phase=(minute_i//360)%4
    out=[]
    for npc_id,row in sorted(state["npc_routines"].items()):
        route=row["routine"]
        node=route[phase%len(route)]
        out.append({
            "id":npc_id,
            "role":row["role"],
            "node":node,
            "persistent":True,
            "source":"game_routine",
        })
    return out

def status() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town Vehicle Life",
        "version":1,
        "ownership":True,
        "enter_exit":True,
        "route_vehicle_sync":True,
        "parking":True,
        "npc_routines":True,
        "usable_entrances":True,
        "real_vehicle_claimed":False,
        "real_person_schedule_claimed":False,
    }
