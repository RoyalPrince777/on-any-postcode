"""M Town Interiors & Persistence v1.

Game-only interiors, door state, vehicle condition/energy, and lightweight
persistence receipts for EARTH IS OUR TURF.
"""
from __future__ import annotations

import copy
from typing import Any

SCHEMA="oap.eiot.mtown-interiors-persistence.v1"

INTERIORS=(
    {"id":"interior-oap-local","entrance_id":"entrance-town-local","label":"ON ANY POSTCODE Local","kind":"shop","node":"town-centre","door":"open","public":True},
    {"id":"interior-oap-market","entrance_id":"entrance-town-market","label":"ON ANY POSTCODE Market","kind":"shop","node":"town-centre","door":"open","public":True},
    {"id":"interior-oap-garage","entrance_id":"entrance-garage","label":"ON ANY POSTCODE Garage","kind":"garage","node":"lower-mitcham","door":"open","public":True},
    {"id":"interior-oap-mobility","entrance_id":"entrance-mobility","label":"ON ANY POSTCODE Mobility","kind":"mobility","node":"eastfields","door":"open","public":True},
    {"id":"interior-lavender-local","entrance_id":"entrance-lavender-local","label":"ON ANY POSTCODE Lavender Local","kind":"shop","node":"lavender-avenue","door":"open","public":True},
    {"id":"interior-phipps-local","entrance_id":"entrance-phipps-local","label":"ON ANY POSTCODE Phipps Local","kind":"shop","node":"phipps-bridge","door":"open","public":True},
    {"id":"interior-laburnum-local","entrance_id":"entrance-laburnum-local","label":"ON ANY POSTCODE Laburnum Local","kind":"shop","node":"laburnum-road","door":"open","public":True},
)

def new_state() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "current_interior_id":None,
        "interiors":[copy.deepcopy(row) for row in INTERIORS],
        "vehicle_state":{},
        "receipts":[],
        "truth":{
            "real_building_interior_claimed":False,
            "exact_private_layout_claimed":False,
            "real_vehicle_telemetry_claimed":False,
        },
    }

def validate(state: object) -> dict[str,Any]:
    if not isinstance(state,dict):
        return {"passed":False,"errors":["mtown_interior_state_missing"]}
    errors=[]
    if state.get("schema")!=SCHEMA:
        errors.append("mtown_interior_schema_invalid")
    if not isinstance(state.get("interiors"),list):
        errors.append("mtown_interiors_invalid")
    return {"passed":not errors,"errors":errors}

def enter(state: object, *, entrance_id: object, node_id: object) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    eid=str(entrance_id or "").strip()
    node=str(node_id or "").strip()
    out=copy.deepcopy(state)
    row=next((x for x in out["interiors"] if x["entrance_id"]==eid),None)
    if row is None:
        raise ValueError("mtown_interior_missing")
    if row["node"]!=node:
        raise ValueError("mtown_interior_not_here")
    if row["door"]!="open":
        raise ValueError("mtown_interior_door_closed")
    out["current_interior_id"]=row["id"]
    out["receipts"].append({"type":"interior_entered","interior_id":row["id"],"node":node})
    out["receipts"]=out["receipts"][-40:]
    return out

def exit(state: object) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    out=copy.deepcopy(state)
    if out.get("current_interior_id") is None:
        raise ValueError("mtown_interior_not_active")
    out["receipts"].append({"type":"interior_exited","interior_id":out["current_interior_id"]})
    out["current_interior_id"]=None
    out["receipts"]=out["receipts"][-40:]
    return out

def set_door(state: object, *, interior_id: object, door: object) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    iid=str(interior_id or "").strip()
    value=str(door or "").strip().lower()
    if value not in {"open","closed","locked"}:
        raise ValueError("mtown_interior_door_state_invalid")
    out=copy.deepcopy(state)
    row=next((x for x in out["interiors"] if x["id"]==iid),None)
    if row is None:
        raise ValueError("mtown_interior_missing")
    row["door"]=value
    return out

def ensure_vehicle(state: object, *, vehicle: dict[str,Any]) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    out=copy.deepcopy(state)
    vid=str(vehicle.get("id") or "").strip()
    if not vid:
        raise ValueError("mtown_vehicle_invalid")
    if vid not in out["vehicle_state"]:
        electric=vehicle.get("class")=="ev"
        out["vehicle_state"][vid]={
            "condition":100,
            "energy_type":"charge" if electric else "fuel",
            "energy":100,
            "odometer_m":0,
        }
    return out

def drive_vehicle(state: object, *, vehicle: dict[str,Any], distance_m: object) -> dict[str,Any]:
    out=ensure_vehicle(state,vehicle=vehicle)
    vid=str(vehicle["id"])
    try:
        distance=max(0.0,float(distance_m))
    except (TypeError,ValueError) as exc:
        raise ValueError("mtown_vehicle_distance_invalid") from exc
    row=out["vehicle_state"][vid]
    row["odometer_m"]+=round(distance)
    row["energy"]=max(0,round(float(row["energy"])-distance/1200,2))
    row["condition"]=max(0,round(float(row["condition"])-distance/25000,2))
    out["receipts"].append({"type":"vehicle_driven","vehicle_id":vid,"distance_m":round(distance)})
    out["receipts"]=out["receipts"][-40:]
    return out

def service_vehicle(state: object, *, vehicle_id: object, restore: object=100) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    vid=str(vehicle_id or "").strip()
    if vid not in state.get("vehicle_state",{}):
        raise ValueError("mtown_vehicle_state_missing")
    out=copy.deepcopy(state)
    amount=max(0,min(100,float(restore)))
    out["vehicle_state"][vid]["condition"]=round(amount,2)
    out["receipts"].append({"type":"vehicle_serviced","vehicle_id":vid})
    return out

def refuel_vehicle(state: object, *, vehicle_id: object, amount: object=100) -> dict[str,Any]:
    checked=validate(state)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    vid=str(vehicle_id or "").strip()
    if vid not in state.get("vehicle_state",{}):
        raise ValueError("mtown_vehicle_state_missing")
    out=copy.deepcopy(state)
    value=max(0,min(100,float(amount)))
    out["vehicle_state"][vid]["energy"]=round(value,2)
    out["receipts"].append({"type":"vehicle_energy_restored","vehicle_id":vid})
    return out

def status() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town Interiors & Persistence",
        "version":1,
        "usable_interiors":True,
        "door_states":True,
        "vehicle_condition":True,
        "fuel_charge_state":True,
        "odometer":True,
        "persistence_receipts":True,
        "real_building_interior_claimed":False,
        "real_vehicle_telemetry_claimed":False,
    }
