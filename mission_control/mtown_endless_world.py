"""Deterministic endless-cell generator for EARTH IS OUR TURF."""
from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA="oap.eiot.endless-cells.v1"
CELL_METRES=512
BIOMES=("urban_high_street","urban_residential","estate","park","industrial","suburban")
BLOCKS=("terrace","estate_block","shops","park","workshop","car_park")

def _seed(x:int,y:int,world_seed:str)->int:
    raw=json.dumps([world_seed,x,y],separators=(",",":")).encode()
    return int(hashlib.sha256(raw).hexdigest()[:16],16)

def cell(*,x:object,y:object,world_seed:object="mtown-v1")->dict[str,Any]:
    xi,yi=int(x),int(y); seed=_seed(xi,yi,str(world_seed))
    biome=BIOMES[seed%len(BIOMES)]
    roads=2+(seed>>8)%4
    blocks=[BLOCKS[(seed>>(12+i*4))%len(BLOCKS)] for i in range(4+(seed>>5)%5)]
    exits={"north":bool(seed&1),"east":bool(seed&2),"south":bool(seed&4),"west":bool(seed&8)}
    if not any(exits.values()):exits["east"]=True
    return {"schema":SCHEMA,"x":xi,"y":yi,"cell_metres":CELL_METRES,"seed":seed,
            "biome":biome,"road_count":roads,"blocks":blocks,"exits":exits,
            "deterministic":True,"authored_override":False,"exact_real_geometry_claimed":False}

def ring(*,center_x:object,center_y:object,radius:object=2,world_seed:object="mtown-v1")->list[dict[str,Any]]:
    cx,cy,r=int(center_x),int(center_y),max(0,min(8,int(radius)))
    return [cell(x=x,y=y,world_seed=world_seed) for y in range(cy-r,cy+r+1) for x in range(cx-r,cx+r+1)]

def status()->dict[str,Any]:
    return {"schema":SCHEMA,"deterministic":True,"unbounded_coordinates":True,"cell_metres":CELL_METRES}
