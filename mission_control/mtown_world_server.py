"""Authoritative M Town world-server facade."""
from __future__ import annotations

from typing import Any

from mission_control import (
    earth_is_our_turf,
    mtown_endless_world,
    mtown_persistence,
)

def new_session()->dict[str,Any]:
    return {"world":earth_is_our_turf.new_world(),"server":{"authoritative":True,"tick":0}}

def act(session:dict[str,Any],*,command:object,target:object=None,mode:object=None,distance:object=None)->dict[str,Any]:
    world=earth_is_our_turf.action(session["world"],command=command,target=target,mode=mode,distance=distance)
    return {"world":world,"server":{"authoritative":True,"tick":int(session.get("server",{}).get("tick",0))+1}}

def cells(*,x:object,y:object,radius:object=2)->list[dict[str,Any]]:
    return mtown_endless_world.ring(center_x=x,center_y=y,radius=radius)

def save(*,session:dict[str,Any],player_ref:object)->dict[str,Any]:
    return mtown_persistence.create_save(player_ref=player_ref,state=session["world"])

def reconnect(*,token:object)->dict[str,Any]:
    loaded=mtown_persistence.load_by_token(token=token)
    earth_is_our_turf.public_state(loaded["world_state"])
    return {"world":loaded["world_state"],"server":{"authoritative":True,"tick":0},
            "save":{"save_id":loaded["save_id"],"revision":loaded["revision"],"player_ref":loaded["player_ref"]}}
