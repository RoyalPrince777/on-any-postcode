"""EARTH IS OUR TURF — Mitcham living-world navigation v2.

Recognisable Mitcham districts anchor the game world. Fine-grained alleys,
shortcuts, businesses, residents and surveillance are fictionalised game data.
No precise real-person tracking or real CCTV/blind-spot database is exposed.
"""
from __future__ import annotations

import copy
import hashlib
import heapq
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from mission_control import earth_is_our_turf_character
from mission_control import earth_is_our_turf_mitcham_world as mitcham_world
from mission_control import mtown_build_system, mtown_language

SCHEMA = "oap.arena.earth-is-our-turf.mitcham.v3"
SESSION_KEY = "oap_eiot_mitcham_v1"

NODES = mitcham_world.NODES
NAV_LINKS = mitcham_world.NAV_LINKS

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",",":"), sort_keys=True, ensure_ascii=False)

def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()

def _seal(state: dict[str, Any]) -> dict[str, Any]:
    out=copy.deepcopy(state); out.pop("checkpoint",None); out["checkpoint"]=_digest(out); return out

def _node_row(node_id: str) -> dict[str, Any]:
    return mitcham_world.node_row(node_id)

def _graph(mode: str) -> dict[str,list[tuple[str,int,str]]]:
    if mode not in {"car","bike","foot"}: raise ValueError("eiot_navigation_mode_invalid")
    graph={row["id"]:[] for row in NODES}
    for a,b,kind,distance,modes in NAV_LINKS:
        if mode in modes:
            graph[a].append((b,distance,kind)); graph[b].append((a,distance,kind))
    return graph

def route(origin: object, destination: object, mode: object) -> dict[str,Any]:
    start=str(origin or ""); end=str(destination or ""); travel=str(mode or "").strip().lower()
    _node_row(start); _node_row(end)
    graph=_graph(travel)
    queue=[(0,start,[])]
    best: dict[str,int]={start:0}
    while queue:
        distance,node,path=heapq.heappop(queue)
        if node==end:
            ids=[start]+[step["to"] for step in path]
            return {
                "mode":travel,
                "from":start,
                "to":end,
                "distance_m":distance,
                "nodes":ids,
                "steps":path,
                "labels":[_node_row(x)["label"] for x in ids],
            }
        if distance!=best.get(node): continue
        for nxt,cost,kind in graph[node]:
            nd=distance+cost
            if nd>=best.get(nxt,10**18): continue
            best[nxt]=nd
            heapq.heappush(queue,(nd,nxt,path+[{"from":node,"to":nxt,"kind":kind,"distance_m":cost}]))
    raise ValueError("eiot_route_unavailable_for_mode")

def new_world() -> dict[str, Any]:
    state={
        "schema":SCHEMA,
        "world_id":str(uuid.uuid4()),
        "title":"EARTH IS OUR TURF",
        "tagline":"Born Local. Built Global.",
        "district":"Mitcham · CR4",
        "board_source":"recognisable_mitcham_streaming_seed_v3",
        "precise_tracking":False,
        "fictionalised_surveillance":True,
        "fine_geometry_claimed":False,
        "time_minutes":8*60,
        "day":1,
        "player":{"node":"town-centre","travel_mode":"foot","influence":0,"cash":250,"reputation":0},
        "character":earth_is_our_turf_character.new_character(),
        "active_chunk":"central",
        "loaded_chunks":["central"],
        "nodes":[dict(n, memory=0, prosperity=50, activity=50) for n in NODES],
        "navigation_links":[
            {"from":a,"to":b,"kind":kind,"distance_m":distance,"modes":list(modes)}
            for a,b,kind,distance,modes in NAV_LINKS
        ],
        "active_route":None,
        "businesses":[
            {"id":"oap-local","label":"ON ANY POSTCODE Local","node":"town-centre","opens":420,"closes":1380,"stock":82,"memory":0},
            {"id":"oap-market","label":"ON ANY POSTCODE Market","node":"town-centre","opens":420,"closes":1320,"stock":90,"memory":0},
            {"id":"oap-garage","label":"ON ANY POSTCODE Garage","node":"lower-mitcham","opens":480,"closes":1080,"stock":65,"memory":0},
            {"id":"oap-mobility","label":"ON ANY POSTCODE Mobility","node":"eastfields","opens":360,"closes":1440,"stock":24,"memory":0},
            {"id":"oap-lavender-local","label":"ON ANY POSTCODE Lavender Local","node":"lavender-avenue","opens":420,"closes":1380,"stock":70,"memory":0},
            {"id":"oap-phipps-local","label":"ON ANY POSTCODE Phipps Local","node":"phipps-bridge","opens":420,"closes":1380,"stock":66,"memory":0},
            {"id":"oap-laburnum-local","label":"ON ANY POSTCODE Laburnum Local","node":"laburnum-road","opens":420,"closes":1320,"stock":74,"memory":0},
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
    if state.get("checkpoint")!=_digest(expected): errors.append("eiot_checkpoint_invalid")
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
    out=copy.deepcopy(state); out["started"]=True
    out["time_label"]=f'{state["time_minutes"]//60:02d}:{state["time_minutes"]%60:02d}'
    for row in out["businesses"]: row["open"]=_business_open(row,state["time_minutes"])
    current_node=state["player"]["node"]
    out["active_chunk"]=mitcham_world.chunk_for(current_node)
    out["loaded_chunks"]=mitcham_world.streamed_chunks(
        out["active_chunk"],
        (state.get("active_route") or {}).get("nodes") if isinstance(state.get("active_route"),dict) else None,
    )
    out["chunks"]={key:value for key,value in mitcham_world.CHUNKS.items() if key in out["loaded_chunks"]}
    out["environment"]=mitcham_world.environment_state(
        node_id=current_node,
        minute=state["time_minutes"],
        day=state["day"],
    )
    node_to_chunk={row["id"]:row["chunk"] for row in NODES}
    out["mbs"]=mtown_build_system.build_manifest(
        chunks=mitcham_world.CHUNKS,
        active_chunk=out["active_chunk"],
        route_nodes=(state.get("active_route") or {}).get("nodes") if isinstance(state.get("active_route"),dict) else None,
        node_to_chunk=node_to_chunk,
    )
    out["character"]=earth_is_our_turf_character.public_character(state["character"])
    out["language"]={
        "status":mtown_language.status(),
        "place_label":mtown_language.place_label(out["district"]),
        "arrival":mtown_language.phrase("arrival",place=_node_row(current_node)["label"]),
        "route":mtown_language.phrase(
            "route",
            place=_node_row(state["active_route"]["to"])["label"],
        ) if isinstance(state.get("active_route"),dict) else None,
    }
    out["payments"]=False; out["real_world_tracking"]=False
    return out

def action(state: object, *, command: object, target: object=None, mode: object=None) -> dict[str, Any]:
    checked=validate(state)
    if not checked["passed"]: raise ValueError(checked["errors"][0])
    current=copy.deepcopy(state); cmd=str(command or "").strip()
    here=_node(current,current["player"]["node"])
    if cmd=="navigate":
        travel=str(mode or current["player"]["travel_mode"]).strip().lower()
        plan=route(here["id"],target,travel)
        current["player"]["travel_mode"]=travel
        current["active_route"]=plan
        current["loaded_chunks"]=mitcham_world.streamed_chunks(mitcham_world.chunk_for(here["id"]),plan["nodes"])
        current["events"].append({"type":"route_planned","from":here["id"],"to":plan["to"],"mode":travel,"distance_m":plan["distance_m"]})
    elif cmd=="travel-route":
        plan=current.get("active_route")
        if not isinstance(plan,dict) or plan.get("from")!=here["id"]: raise ValueError("eiot_active_route_missing")
        current["player"]["node"]=plan["to"]
        current["active_chunk"]=mitcham_world.chunk_for(plan["to"])
        current["loaded_chunks"]=mitcham_world.streamed_chunks(current["active_chunk"])
        _node(current,plan["to"])["memory"]+=1
        current["time_minutes"]=(current["time_minutes"]+max(1,plan["distance_m"]//(450 if plan["mode"]=="foot" else 1800 if plan["mode"]=="bike" else 5000)))%(24*60)
        current["events"].append({"type":"travel","from":here["id"],"to":plan["to"],"mode":plan["mode"],"distance_m":plan["distance_m"]})
        current["active_route"]=None
    elif cmd=="move":
        travel=str(mode or current["player"]["travel_mode"]).strip().lower()
        plan=route(here["id"],target,travel)
        if len(plan["steps"])!=1: raise ValueError("eiot_move_requires_direct_link")
        current["player"]["node"]=plan["to"]; current["player"]["travel_mode"]=travel
        current["active_chunk"]=mitcham_world.chunk_for(plan["to"])
        current["loaded_chunks"]=mitcham_world.streamed_chunks(current["active_chunk"])
        _node(current,plan["to"])["memory"]+=1
        current["events"].append({"type":"movement","from":here["id"],"to":plan["to"],"mode":travel,"kind":plan["steps"][0]["kind"]})
    elif cmd=="help-local":
        here["memory"]+=2; here["prosperity"]=min(100,here["prosperity"]+2)
        current["player"]["influence"]+=2; current["player"]["reputation"]+=1
        current["character"]=earth_is_our_turf_character.adjust_reputation(current["character"],dimension="m_town",amount=1)
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
        for node in current["nodes"]: node["activity"]=75 if 420<=current["time_minutes"]<1320 else 28
        current["events"].append({"type":"time","minutes":current["time_minutes"]})
    else: raise ValueError("eiot_action_invalid")
    current["events"]=current["events"][-60:]
    return _seal(current)
