"""M Town World Position System v1.

Deterministic continuous route progress for EARTH IS OUR TURF.
Uses gameplay route distances only. It does not claim exact real-world geometry,
headings, private access or surveillance coverage.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

SCHEMA="oap.eiot.mtown-world-position.v1"

def _canonical(value: object) -> str:
    return json.dumps(value,separators=(",",":"),sort_keys=True,ensure_ascii=False)

def _route_id(route: dict[str,Any]) -> str:
    payload={
        "mode":route.get("mode"),
        "from":route.get("from"),
        "to":route.get("to"),
        "distance_m":route.get("distance_m"),
        "steps":route.get("steps"),
    }
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()[:20]

def start(route: object) -> dict[str,Any]:
    if not isinstance(route,dict) or not isinstance(route.get("steps"),list) or not route["steps"]:
        raise ValueError("mtown_position_route_invalid")
    first=route["steps"][0]
    total=int(route.get("distance_m") or 0)
    if total <= 0:
        raise ValueError("mtown_position_distance_invalid")
    return {
        "schema":SCHEMA,
        "route_id":_route_id(route),
        "mode":str(route.get("mode") or "foot"),
        "origin":str(route.get("from")),
        "destination":str(route.get("to")),
        "current_node":str(route.get("from")),
        "step_index":0,
        "segment":{
            "from":str(first["from"]),
            "to":str(first["to"]),
            "kind":str(first["kind"]),
            "distance_m":int(first["distance_m"]),
            "offset_m":0.0,
            "progress":0.0,
        },
        "travelled_m":0.0,
        "remaining_m":float(total),
        "route_progress":0.0,
        "completed":False,
        "heading_claimed":False,
        "exact_geometry_claimed":False,
    }

def advance(position: object, route: object, *, distance_m: object) -> dict[str,Any]:
    if not isinstance(position,dict) or position.get("schema")!=SCHEMA:
        raise ValueError("mtown_position_invalid")
    if not isinstance(route,dict) or _route_id(route)!=position.get("route_id"):
        raise ValueError("mtown_position_route_mismatch")
    try:
        move=float(distance_m)
    except (TypeError,ValueError) as exc:
        raise ValueError("mtown_position_distance_invalid") from exc
    if move < 0:
        raise ValueError("mtown_position_distance_invalid")
    if position.get("completed"):
        return copy.deepcopy(position)

    out=copy.deepcopy(position)
    steps=route["steps"]
    total=float(route["distance_m"])
    remaining_move=move

    while remaining_move > 0 and not out["completed"]:
        idx=int(out["step_index"])
        step=steps[idx]
        step_distance=float(step["distance_m"])
        offset=float(out["segment"]["offset_m"])
        available=max(0.0,step_distance-offset)
        consumed=min(remaining_move,available)
        offset+=consumed
        out["travelled_m"]=min(total,float(out["travelled_m"])+consumed)
        remaining_move-=consumed

        if offset >= step_distance-1e-9:
            out["current_node"]=str(step["to"])
            idx+=1
            if idx >= len(steps):
                out["completed"]=True
                out["step_index"]=len(steps)-1
                out["segment"]["offset_m"]=step_distance
                out["segment"]["progress"]=1.0
                break
            next_step=steps[idx]
            out["step_index"]=idx
            out["segment"]={
                "from":str(next_step["from"]),
                "to":str(next_step["to"]),
                "kind":str(next_step["kind"]),
                "distance_m":int(next_step["distance_m"]),
                "offset_m":0.0,
                "progress":0.0,
            }
        else:
            out["segment"]["offset_m"]=round(offset,3)
            out["segment"]["progress"]=round(offset/step_distance,6) if step_distance else 1.0

    out["remaining_m"]=round(max(0.0,total-float(out["travelled_m"])),3)
    out["route_progress"]=round(min(1.0,float(out["travelled_m"])/total),6)
    return out

def lookahead_nodes(position: object, route: object, *, distance_m: object=1200) -> list[str]:
    if not isinstance(position,dict) or position.get("schema")!=SCHEMA:
        raise ValueError("mtown_position_invalid")
    if not isinstance(route,dict) or _route_id(route)!=position.get("route_id"):
        raise ValueError("mtown_position_route_mismatch")
    try:
        budget=max(0.0,float(distance_m))
    except (TypeError,ValueError) as exc:
        raise ValueError("mtown_position_distance_invalid") from exc

    nodes=[str(position["current_node"])]
    idx=int(position["step_index"])
    first_offset=float(position["segment"]["offset_m"])
    for step_index in range(idx,len(route["steps"])):
        step=route["steps"][step_index]
        step_remaining=float(step["distance_m"])
        if step_index==idx:
            step_remaining=max(0.0,step_remaining-first_offset)
        nodes.append(str(step["to"]))
        budget-=step_remaining
        if budget <= 0:
            break
    return list(dict.fromkeys(nodes))

def status() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town World Position System",
        "version":1,
        "continuous_route_progress":True,
        "lookahead_streaming":True,
        "exact_geometry_claimed":False,
        "heading_claimed":False,
    }
