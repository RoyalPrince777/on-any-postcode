"""EARTH IS OUR TURF — Mitcham living-world v1.

First-party, session-scoped gameplay seed. Recognisable place names are used as
world anchors, while businesses, residents and surveillance are fictionalised.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA = "oap.arena.earth-is-our-turf.mitcham.v1"
SESSION_KEY = "oap_eiot_mitcham_v1"

NODES = (
    {"id":"town-centre","label":"Mitcham Town Centre","kind":"centre","links":["eastfields","figges-marsh","cricket-green"]},
    {"id":"eastfields","label":"Mitcham Eastfields","kind":"transport","links":["town-centre","pollards-hill"]},
    {"id":"figges-marsh","label":"Figge's Marsh","kind":"park","links":["town-centre","eastfields"]},
    {"id":"cricket-green","label":"Cricket Green","kind":"neighbourhood","links":["town-centre","ravensbury"]},
    {"id":"ravensbury","label":"Ravensbury Park","kind":"park","links":["cricket-green","lower-mitcham"]},
    {"id":"lower-mitcham","label":"Lower Mitcham","kind":"neighbourhood","links":["ravensbury","mitcham-common"]},
    {"id":"mitcham-common","label":"Mitcham Common","kind":"park","links":["lower-mitcham","pollards-hill"]},
    {"id":"pollards-hill","label":"Pollards Hill","kind":"estate","links":["mitcham-common","eastfields"]},
)

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",",":"), sort_keys=True, ensure_ascii=False)

def _seal(state: dict[str, Any]) -> dict[str, Any]:
    out=copy.deepcopy(state)
    out.pop("checkpoint",None)
    out["checkpoint"]=hashlib.sha256(_canonical(out).encode()).hexdigest()
    return out

def new_world() -> dict[str, Any]:
    state={
        "schema":SCHEMA,
        "world_id":str(uuid.uuid4()),
        "title":"EARTH IS OUR TURF",
        "tagline":"Born Local. Built Global.",
        "district":"Mitcham · CR4",
        "board_source":"recognisable_mitcham_game_seed_v1",
        "precise_tracking":False,
        "fictionalised_surveillance":True,
        "time_minutes":8*60,
        "day":1,
        "player":{"node":"town-centre","influence":0,"cash":250,"reputation":0},
        "nodes":[dict(n, memory=0, prosperity=50, activity=50) for n in NODES],
        "businesses":[
            {"id":"oap-local","label":"ON ANY POSTCODE Local","node":"town-centre","opens":420,"closes":1380,"stock":82,"memory":0},
            {"id":"oap-market","label":"ON ANY POSTCODE Market","node":"town-centre","opens":420,"closes":1320,"stock":90,"memory":0},
            {"id":"oap-garage","label":"ON ANY POSTCODE Garage","node":"lower-mitcham","opens":480,"closes":1080,"stock":65,"memory":0},
        ],
        "events":[],
        "created_at":datetime.now(timezone.utc).isoformat(),
    }
    return _seal(state)

def validate(state: object) -> dict[str, Any]:
    errors=[]
    if not isinstance(state,dict): return {"passed":False,"errors":["eiot_state_missing"]}
    if state.get("schema")!=SCHEMA: errors.append("eiot_schema_invalid")
    if not isinstance(state.get("nodes"),list) or len(state["nodes"])!=len(NODES): errors.append("eiot_nodes_invalid")
    expected=copy.deepcopy(state); expected.pop("checkpoint",None)
    if state.get("checkpoint")!=hashlib.sha256(_canonical(expected).encode()).hexdigest(): errors.append("eiot_checkpoint_invalid")
    return {"passed":not errors,"errors":errors}

def _node(state: dict[str, Any], node_id: str) -> dict[str, Any]:
    for node in state["nodes"]:
        if node["id"]==node_id: return node
    raise ValueError("eiot_node_invalid")

def _business_open(row: dict[str, Any], minute: int) -> bool:
    return row["opens"] <= minute < row["closes"]

def public_state(state: dict[str, Any] | None) -> dict[str, Any]:
    if state is None: return {"started":False,"status":"idle"}
    checked=validate(state)
    if not checked["passed"]: raise ValueError(checked["errors"][0])
    out=copy.deepcopy(state)
    out["started"]=True
    out["time_label"]=f'{state["time_minutes"]//60:02d}:{state["time_minutes"]%60:02d}'
    for row in out["businesses"]:
        row["open"]=_business_open(row,state["time_minutes"])
    out["payments"]=False
    out["real_world_tracking"]=False
    return out

def action(state: object, *, command: object, target: object=None) -> dict[str, Any]:
    checked=validate(state)
    if not checked["passed"]: raise ValueError(checked["errors"][0])
    current=copy.deepcopy(state)
    cmd=str(command or "").strip()
    here=_node(current,current["player"]["node"])
    if cmd=="move":
        dest=str(target or "")
        if dest not in here["links"]: raise ValueError("eiot_route_not_adjacent")
        current["player"]["node"]=dest
        _node(current,dest)["memory"]+=1
        current["events"].append({"type":"movement","from":here["id"],"to":dest})
    elif cmd=="help-local":
        here["memory"]+=2; here["prosperity"]=min(100,here["prosperity"]+2)
        current["player"]["influence"]+=2; current["player"]["reputation"]+=1
        current["events"].append({"type":"postcode_memory","node":here["id"],"effect":"community_help"})
    elif cmd=="shop":
        shops=[b for b in current["businesses"] if b["node"]==here["id"] and _business_open(b,current["time_minutes"]) and b["stock"]>0]
        if not shops: raise ValueError("eiot_no_open_shop_here")
        row=shops[0]; row["stock"]-=1; row["memory"]+=1; here["prosperity"]=min(100,here["prosperity"]+1)
        current["player"]["cash"]=max(0,current["player"]["cash"]-5)
        current["events"].append({"type":"commerce","node":here["id"],"business":row["id"]})
    elif cmd=="advance-time":
        current["time_minutes"]=(current["time_minutes"]+120)%(24*60)
        if current["time_minutes"]<120: current["day"]+=1
        for node in current["nodes"]:
            node["activity"]=max(10,min(95,75 if 420<=current["time_minutes"]<1320 else 28))
        current["events"].append({"type":"time","minutes":current["time_minutes"]})
    else:
        raise ValueError("eiot_action_invalid")
    current["events"]=current["events"][-40:]
    return _seal(current)
