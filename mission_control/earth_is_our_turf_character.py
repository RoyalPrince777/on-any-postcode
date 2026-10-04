"""EARTH IS OUR TURF playable character v1.

First-party persistent character domain for M Town. Separates player identity,
appearance, movement state, inventory, reputation and relationship hooks from
the wider world state. No biometric identity claims.
"""
from __future__ import annotations

import copy
import hashlib
import json
import uuid
from typing import Any

SCHEMA="oap.eiot.character.v1"

APPEARANCE_SLOTS=("hair","headwear","top","bottom","outerwear","shoes","accessory","jewellery")
REPUTATION_KEYS=("m_town","business","street","creator","sports","global")

def _canonical(value: object) -> str:
    return json.dumps(value,separators=(",",":"),sort_keys=True,ensure_ascii=False)

def _seal(character: dict[str,Any]) -> dict[str,Any]:
    out=copy.deepcopy(character)
    out.pop("checkpoint",None)
    out["checkpoint"]=hashlib.sha256(_canonical(out).encode()).hexdigest()
    return out

def new_character(*, display_name: object="Player", home_node: object="town-centre") -> dict[str,Any]:
    name=str(display_name or "Player").strip()[:40] or "Player"
    node=str(home_node or "town-centre").strip()
    character={
        "schema":SCHEMA,
        "character_id":str(uuid.uuid4()),
        "my_card":{
            "display_name":name,
            "home":"M Town · CR4",
            "title":"Local",
            "tagline":"Born Local. Built Global.",
        },
        "appearance":{
            "body_type":"standard",
            "skin_tone":"custom",
            "height_scale":1.0,
            "slots":{slot:None for slot in APPEARANCE_SLOTS},
        },
        "movement":{
            "mode":"foot",
            "node":node,
            "segment":None,
            "offset":0.0,
            "heading":0.0,
            "speed":0.0,
            "stance":"stand",
        },
        "vitals":{
            "health":100,
            "energy":100,
            "stamina":100,
        },
        "inventory":{
            "capacity":20,
            "items":[],
            "cash":250,
        },
        "reputation":{key:0 for key in REPUTATION_KEYS},
        "relationships":{},
        "owned":{
            "vehicles":[],
            "properties":[],
            "businesses":[],
        },
        "memory":{
            "places_visited":[node],
            "people_met":[],
            "major_events":[],
        },
        "online":{
            "presence":"private",
            "instance":None,
            "party":None,
        },
        "truth":{
            "biometric_identity_claimed":False,
            "real_person_required":False,
        },
    }
    return _seal(character)

def validate(character: object) -> dict[str,Any]:
    errors=[]
    if not isinstance(character,dict):
        return {"passed":False,"errors":["character_missing"]}
    if character.get("schema")!=SCHEMA:
        errors.append("character_schema_invalid")
    expected=copy.deepcopy(character)
    expected.pop("checkpoint",None)
    if character.get("checkpoint")!=hashlib.sha256(_canonical(expected).encode()).hexdigest():
        errors.append("character_checkpoint_invalid")
    return {"passed":not errors,"errors":errors}

def public_character(character: dict[str,Any]) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    return copy.deepcopy(character)

def equip(character: object, *, slot: object, item: object) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    key=str(slot or "").strip()
    if key not in APPEARANCE_SLOTS:
        raise ValueError("character_slot_invalid")
    out=copy.deepcopy(character)
    out["appearance"]["slots"][key]=str(item or "").strip() or None
    return _seal(out)

def set_movement(
    character: object,
    *,
    mode: object|None=None,
    node: object|None=None,
    speed: object|None=None,
    heading: object|None=None,
    segment: object|None=None,
    offset: object|None=None,
) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    out=copy.deepcopy(character)
    if mode is not None:
        travel=str(mode).strip().lower()
        if travel not in {"foot","bike","car"}:
            raise ValueError("character_movement_mode_invalid")
        out["movement"]["mode"]=travel
    if node is not None:
        value=str(node).strip()
        if value:
            out["movement"]["node"]=value
            if value not in out["memory"]["places_visited"]:
                out["memory"]["places_visited"].append(value)
    if speed is not None:
        out["movement"]["speed"]=max(0.0,float(speed))
    if heading is not None:
        out["movement"]["heading"]=float(heading)%360.0
    if segment is not None:
        out["movement"]["segment"]=copy.deepcopy(segment)
    if offset is not None:
        out["movement"]["offset"]=max(0.0,float(offset))
    return _seal(out)

def set_owned_vehicles(character: object, vehicle_ids: object) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    if not isinstance(vehicle_ids,list):
        raise ValueError("character_owned_vehicles_invalid")
    out=copy.deepcopy(character)
    out["owned"]["vehicles"]=list(dict.fromkeys(str(v).strip() for v in vehicle_ids if str(v).strip()))
    return _seal(out)

def adjust_reputation(character: object, *, dimension: object, amount: object) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    key=str(dimension or "").strip().lower()
    if key not in REPUTATION_KEYS:
        raise ValueError("character_reputation_invalid")
    out=copy.deepcopy(character)
    out["reputation"][key]=max(-100,min(100,out["reputation"][key]+int(amount)))
    return _seal(out)

def relationship(
    character: object,
    *,
    person_id: object,
    trust: object=0,
    respect: object=0,
    loyalty: object=0,
) -> dict[str,Any]:
    checked=validate(character)
    if not checked["passed"]:
        raise ValueError(checked["errors"][0])
    pid=str(person_id or "").strip()
    if not pid:
        raise ValueError("character_relationship_person_invalid")
    out=copy.deepcopy(character)
    out["relationships"][pid]={
        "trust":max(-100,min(100,int(trust))),
        "respect":max(-100,min(100,int(respect))),
        "loyalty":max(-100,min(100,int(loyalty))),
    }
    if pid not in out["memory"]["people_met"]:
        out["memory"]["people_met"].append(pid)
    return _seal(out)

def status() -> dict[str,Any]:
    return {
        "schema":SCHEMA,
        "name":"EARTH IS OUR TURF Character",
        "version":1,
        "appearance_slots":list(APPEARANCE_SLOTS),
        "reputation_dimensions":list(REPUTATION_KEYS),
        "movement_modes":["foot","bike","car"],
    }
