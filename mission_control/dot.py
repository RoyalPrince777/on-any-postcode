"""First-party OAP Arena Dot (Dots and Boxes) engine."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid

SCHEMA="oap.arena.dot.v1";SESSION_KEY="oap_dot_v1";REQ=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$");SIZE=3
def _d(v):return hashlib.sha256(json.dumps(v,separators=(",",":"),sort_keys=True).encode()).hexdigest()
def _seal(s):o=copy.deepcopy(s);o.pop("checkpoint",None);o["checkpoint"]=_d(o);return o
def new_game(player_one: object = "Player One", player_two: object = "Player Two"):
    names = [" ".join(str(v or "").split()) for v in (player_one, player_two)]
    if any(not n or len(n) > 40 for n in names) or names[0].casefold() == names[1].casefold():
        raise ValueError("dot_players_invalid")
    return _seal({"schema":SCHEMA,"game_id":str(uuid.uuid4()),"status":"active","turn":0,"players":[{"id":"p1","name":names[0],"score":0},{"id":"p2","name":names[1],"score":0}],"edges":[],"boxes":{},"winner_id":None,"draw":False,"result":None,"request_receipts":[]})
def validate(s):
    if not isinstance(s,dict):return {"passed":False,"errors":["dot_state_missing"]}
    e=[];exp=copy.deepcopy(s);exp.pop("checkpoint",None)
    if s.get("schema")!=SCHEMA:e.append("dot_schema_invalid")
    if s.get("checkpoint")!=_d(exp):e.append("dot_checkpoint_invalid")
    return {"passed":not e,"errors":e}
def _copy(s):
    c=validate(s)
    if not c["passed"]:raise ValueError(c["errors"][0])
    return copy.deepcopy(s)
def _req(x):
    r=str(x or "").strip()
    if not REQ.fullmatch(r):raise ValueError("dot_request_id_invalid")
    return r
def _edge(a,b):return tuple(sorted((a,b)))
NODE_PATTERN = re.compile(r"^[0-2],[0-2]$")
def _adj(a,b):
    if not isinstance(a, str) or not isinstance(b, str):return False
    if not NODE_PATTERN.fullmatch(a) or not NODE_PATTERN.fullmatch(b):return False
    ax,ay=map(int,a.split(","));bx,by=map(int,b.split(","))
    return abs(ax-bx)+abs(ay-by)==1
def _completed_boxes(edges):
    es={tuple(x) for x in edges};out=[]
    for x in range(SIZE-1):
      for y in range(SIZE-1):
        need={_edge(f"{x},{y}",f"{x+1},{y}"),_edge(f"{x},{y}",f"{x},{y+1}"),_edge(f"{x+1},{y}",f"{x+1},{y+1}"),_edge(f"{x},{y+1}",f"{x+1},{y+1}")}
        if need<=es:out.append(f"{x},{y}")
    return out
def public_state(s):
    if s is None:return {"started":False,"status":"idle"}
    c=validate(s)
    if not c["passed"]:raise ValueError(c["errors"][0])
    return {"started":True,"status":s["status"],"players":copy.deepcopy(s["players"]),"turn_player":s["players"][s["turn"]]["name"],"turn_player_id":s["players"][s["turn"]]["id"],"edges":copy.deepcopy(s["edges"]),"boxes":copy.deepcopy(s["boxes"]),"winner_id":s.get("winner_id"),"draw":bool(s.get("draw")),"result":s.get("result"),"size":SIZE,"payments":False}
def draw(s,*,a:object,b:object,request_id:object):
    cur=_copy(s);req=_req(request_id);a=str(a);b=str(b)
    if any(x["request_id"]==req for x in cur["request_receipts"]):return cur
    if cur["status"]!="active":raise ValueError(f"dot_game_{cur['status']}")
    if not _adj(a,b):raise ValueError("dot_edge_invalid")
    edge=_edge(a,b)
    if list(edge) in cur["edges"]:raise ValueError("dot_edge_exists")
    before=set(cur["boxes"]);cur["edges"].append(list(edge));after=set(_completed_boxes(cur["edges"]));new=after-before
    if new:
        p=cur["players"][cur["turn"]]
        for box in new:cur["boxes"][box]=p["id"]
        p["score"]+=len(new)
    else:cur["turn"]=1-cur["turn"]
    cur["request_receipts"].append({"request_id":req,"action":"draw","edge":list(edge)})
    if len(cur["boxes"])==(SIZE-1)*(SIZE-1):
        cur["status"]="completed"
        first,second=cur["players"]
        cur["draw"]=first["score"]==second["score"]
        cur["winner_id"]=None if cur["draw"] else (first["id"] if first["score"]>second["score"] else second["id"])
        cur["result"]="draw" if cur["draw"] else "boxes_win"
    return _seal(cur)
def stop(s,*,request_id:object):
    cur=_copy(s);req=_req(request_id)
    if any(x["request_id"]==req for x in cur["request_receipts"]):return cur
    if cur["status"]!="active":raise ValueError("dot_stop_denied")
    cur["status"]="stopped";cur["request_receipts"].append({"request_id":req,"action":"stop"});return _seal(cur)
