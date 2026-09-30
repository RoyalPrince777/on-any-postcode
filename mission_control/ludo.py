"""First-party OAP Arena Ludo engine."""
from __future__ import annotations
import copy
import hashlib
import json
import re
import uuid
SCHEMA="oap.arena.ludo.v1"; SESSION_KEY="oap_ludo_v1"; REQUEST_ID_PATTERN=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
BOARD_END=24
def _canon(v): return json.dumps(v,separators=(",",":"),sort_keys=True)
def _digest(v): return hashlib.sha256(_canon(v).encode()).hexdigest()
def _seal(s): o=copy.deepcopy(s);o.pop("checkpoint",None);o["checkpoint"]=_digest(o);return o
def _req(v):
    x=str(v or "").strip()
    if not REQUEST_ID_PATTERN.fullmatch(x): raise ValueError("ludo_request_id_invalid")
    return x
def new_game(players: object):
    if not isinstance(players,list) or not 2<=len(players)<=4: raise ValueError("ludo_player_count_invalid")
    names=[" ".join(str(x).split()) for x in players]
    if any(not x or len(x)>40 for x in names) or len({x.casefold() for x in names})!=len(names): raise ValueError("ludo_players_invalid")
    return _seal({"schema":SCHEMA,"game_id":str(uuid.uuid4()),"status":"active","players":[{"id":f"p{i+1}","name":n,"piece":0} for i,n in enumerate(names)],"turn_index":0,"winner_id":None,"request_receipts":[]})
def validate(s):
    if not isinstance(s,dict): return {"passed":False,"errors":["ludo_state_missing"]}
    e=[]
    if s.get("schema")!=SCHEMA:e.append("ludo_schema_invalid")
    if s.get("status") not in {"active","completed","stopped"}:e.append("ludo_status_invalid")
    exp=copy.deepcopy(s);exp.pop("checkpoint",None)
    if s.get("checkpoint")!=_digest(exp):e.append("ludo_checkpoint_invalid")
    return {"passed":not e,"errors":e}
def _copy(s):
    c=validate(s)
    if not c["passed"]: raise ValueError(c["errors"][0])
    return copy.deepcopy(s)
def public_state(s):
    if s is None:return {"started":False,"status":"idle"}
    c=validate(s)
    if not c["passed"]:raise ValueError(c["errors"][0])
    p=s["players"][s["turn_index"]]
    return {"started":True,"status":s["status"],"players":copy.deepcopy(s["players"]),"current_player_id":p["id"],"current_player_name":p["name"],"winner_id":s["winner_id"],"board_end":BOARD_END,"payments":False}
def move(s,*,steps:object,request_id:object):
    cur=_copy(s); req=_req(request_id)
    if any(x["request_id"]==req for x in cur["request_receipts"]): return cur
    if cur["status"]!="active": raise ValueError(f"ludo_game_{cur['status']}")
    if not isinstance(steps,int) or not 1<=steps<=6: raise ValueError("ludo_steps_invalid")
    p=cur["players"][cur["turn_index"]]; p["piece"]=min(BOARD_END,p["piece"]+steps)
    cur["request_receipts"].append({"request_id":req,"action":"move","steps":steps})
    if p["piece"]>=BOARD_END: cur["status"]="completed";cur["winner_id"]=p["id"]
    else: cur["turn_index"]=(cur["turn_index"]+1)%len(cur["players"])
    return _seal(cur)
def stop(s,*,request_id:object):
    cur=_copy(s); req=_req(request_id)
    if cur["status"]!="active": raise ValueError("ludo_stop_denied")
    if any(x["request_id"]==req for x in cur["request_receipts"]): return cur
    cur["status"]="stopped";cur["request_receipts"].append({"request_id":req,"action":"stop"});return _seal(cur)
