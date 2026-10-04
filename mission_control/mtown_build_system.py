"""MBS — M Town Build System v1.

First-party world build/stream planner for EARTH IS OUR TURF.
Converts current player + route state into deterministic LIVE/BACKGROUND/MEMORY
simulation tiers and preload requirements. It does not claim real-world geometry.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA = "oap.eiot.mbs.mtown.v1"

TIER_LIVE = "LIVE"
TIER_BACKGROUND = "BACKGROUND"
TIER_MEMORY = "MEMORY"

def _canonical(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def _id(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()[:20]

def build_manifest(
    *,
    chunks: dict[str, dict[str, Any]],
    active_chunk: str,
    route_nodes: list[str] | None,
    node_to_chunk: dict[str, str],
) -> dict[str, Any]:
    if active_chunk not in chunks:
        raise ValueError("mbs_active_chunk_invalid")

    route_chunks: list[str] = []
    for node_id in route_nodes or []:
        chunk = node_to_chunk.get(node_id)
        if chunk and chunk not in route_chunks:
            route_chunks.append(chunk)

    live=[active_chunk]
    preload=[c for c in route_chunks if c != active_chunk][:2]

    background=[]
    for key in chunks:
        if key in live or key in preload:
            continue
        if key == "central" or len(background) < 2:
            background.append(key)

    tiers={}
    for key in chunks:
        if key in live:
            tiers[key]=TIER_LIVE
        elif key in preload or key in background:
            tiers[key]=TIER_BACKGROUND
        else:
            tiers[key]=TIER_MEMORY

    manifest={
        "schema":SCHEMA,
        "active_chunk":active_chunk,
        "tiers":tiers,
        "preload_next":preload,
        "budgets":{
            TIER_LIVE:{"npc_detail":"full","vehicle_detail":"full","physics":True,"audio":True,"interiors":"nearby"},
            TIER_BACKGROUND:{"npc_detail":"reduced","vehicle_detail":"reduced","physics":False,"audio":False,"interiors":"off"},
            TIER_MEMORY:{"npc_detail":"statistical","vehicle_detail":"state_only","physics":False,"audio":False,"interiors":"off"},
        },
        "unreal_handoff":{
            "world_partition":True,
            "data_layers":True,
            "hlod":True,
            "streaming_sources":["player","active_route"],
            "authoritative_truth":"oap_world_state",
        },
        "truth":{
            "real_world_geometry_claimed":False,
            "private_access_claimed":False,
            "surveillance_claimed":False,
        },
    }
    manifest["manifest_id"]=_id(manifest)
    return manifest

def status() -> dict[str, Any]:
    return {
        "schema":SCHEMA,
        "name":"M Town Build System",
        "version":1,
        "purpose":"deterministic streamed-world build planning",
        "tiers":[TIER_LIVE,TIER_BACKGROUND,TIER_MEMORY],
    }
