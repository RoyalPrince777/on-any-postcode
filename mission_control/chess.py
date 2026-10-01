"""First-party OAP Arena Chess engine (bounded legal-move slice)."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid

SCHEMA="oap.arena.chess.v1";SESSION_KEY="oap_chess_v1";REQ=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")
def _d(v): return hashlib.sha256(json.dumps(v,separators=(",",":"),sort_keys=True).encode()).hexdigest()
def _seal(s): o=copy.deepcopy(s);o.pop("checkpoint",None);o["checkpoint"]=_d(o);return o
def new_game():
    b={"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","d2":"wP","e2":"wP","f2":"wP","g2":"wP","h2":"wP",
       "a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","d7":"bP","e7":"bP","f7":"bP","g7":"bP","h7":"bP"}
    return _seal({"schema":SCHEMA,"game_id":str(uuid.uuid4()),"status":"active","turn":"w","board":b,"winner":None,"result":None,"check":False,"request_receipts":[]})
def validate(s):
    if not isinstance(s,dict):return {"passed":False,"errors":["chess_state_missing"]}
    e=[]; exp=copy.deepcopy(s);exp.pop("checkpoint",None)
    if s.get("schema")!=SCHEMA:e.append("chess_schema_invalid")
    if s.get("status") not in {"active","completed","stopped"}:e.append("chess_status_invalid")
    if s.get("checkpoint")!=_d(exp):e.append("chess_checkpoint_invalid")
    return {"passed":not e,"errors":e}
def _copy(s):
    c=validate(s)
    if not c["passed"]:raise ValueError(c["errors"][0])
    return copy.deepcopy(s)
def _sq(x):
    return isinstance(x,str) and len(x)==2 and x[0] in "abcdefgh" and x[1] in "12345678"
def _req(x):
    r=str(x or "").strip()
    if not REQ.fullmatch(r):raise ValueError("chess_request_id_invalid")
    return r
def _coords(s):return ord(s[0])-97,int(s[1])-1
def _legal(piece,src,dst,board):
    sx,sy=_coords(src);dx,dy=_coords(dst);fx,fy=dx-sx,dy-sy;color=piece[0];kind=piece[1]
    target=board.get(dst)
    if target and target[0]==color:return False
    if kind=="N":return (abs(fx),abs(fy)) in {(1,2),(2,1)}
    if kind=="K":return max(abs(fx),abs(fy))==1
    if kind=="P":
        direction=1 if color=="w" else -1
        start=1 if color=="w" else 6
        if fx==0 and fy==direction and not target:return True
        if fx==0 and sy==start and fy==2*direction and not target:
            mid=f"{src[0]}{sy+direction+1}"
            return mid not in board
        return abs(fx)==1 and fy==direction and target is not None and target[0]!=color
    if kind in {"R","B","Q"}:
        if kind=="R" and not (fx==0 or fy==0):return False
        if kind=="B" and abs(fx)!=abs(fy):return False
        if kind=="Q" and not (fx==0 or fy==0 or abs(fx)==abs(fy)):return False
        stepx=0 if fx==0 else (1 if fx>0 else -1);stepy=0 if fy==0 else (1 if fy>0 else -1)
        x,y=sx+stepx,sy+stepy
        while (x,y)!=(dx,dy):
            if f"{chr(97+x)}{y+1}" in board:return False
            x+=stepx;y+=stepy
        return True
    return False
def _king_square(board,color):
    return next((sq for sq,piece in board.items() if piece==color+"K"),None)
def _attacked(board,square,by_color):
    for src,piece in board.items():
        if piece[0]!=by_color:continue
        if piece[1]=="P":
            sx,sy=_coords(src);dx,dy=_coords(square)
            direction=1 if by_color=="w" else -1
            if abs(dx-sx)==1 and dy-sy==direction:return True
            continue
        if _legal(piece,src,square,board):return True
    return False
def _in_check(board,color):
    king=_king_square(board,color)
    return king is None or _attacked(board,king,"b" if color=="w" else "w")
def _candidate_board(board,src,dst,color):
    piece=board.get(src)
    if not piece or piece[0]!=color or not _legal(piece,src,dst,board):return None
    target=board.get(dst)
    if target and target[1]=="K":return None
    nxt=copy.deepcopy(board);nxt.pop(src);nxt[dst]=piece
    if _in_check(nxt,color):return None
    return nxt
def _has_legal_move(board,color):
    for src,piece in board.items():
        if piece[0]!=color:continue
        for file in "abcdefgh":
            for rank in "12345678":
                dst=file+rank
                if src!=dst and _candidate_board(board,src,dst,color) is not None:return True
    return False
def public_state(s):
    if s is None:return {"started":False,"status":"idle"}
    c=validate(s)
    if not c["passed"]:raise ValueError(c["errors"][0])
    return {"started":True,"status":s["status"],"turn":"White" if s["turn"]=="w" else "Black","board":copy.deepcopy(s["board"]),"winner":s["winner"],"result":s.get("result"),"check":bool(s.get("check")),"payments":False}
def move(s,*,source:object,target:object,request_id:object):
    cur=_copy(s);req=_req(request_id);src=str(source);dst=str(target)
    if any(x["request_id"]==req for x in cur["request_receipts"]):return cur
    if cur["status"]!="active":raise ValueError(f"chess_game_{cur['status']}")
    if not _sq(src) or not _sq(dst):raise ValueError("chess_square_invalid")
    piece=cur["board"].get(src)
    if not piece or piece[0]!=cur["turn"]:raise ValueError("chess_turn_invalid")
    if not _legal(piece,src,dst,cur["board"]):raise ValueError("chess_move_invalid")
    if cur["board"].get(dst, "")[1:]=="K":raise ValueError("chess_king_capture_invalid")
    next_board=_candidate_board(cur["board"],src,dst,cur["turn"])
    if next_board is None:raise ValueError("chess_self_check_invalid")
    mover=cur["turn"];opponent="b" if mover=="w" else "w"
    cur["board"]=next_board
    cur["request_receipts"].append({"request_id":req,"action":"move","source":src,"target":dst})
    opponent_in_check=_in_check(cur["board"],opponent)
    if not _has_legal_move(cur["board"],opponent):
        cur["status"]="completed"
        cur["turn"]=opponent
        cur["check"]=opponent_in_check
        cur["result"]="checkmate" if opponent_in_check else "stalemate"
        cur["winner"]=("White" if mover=="w" else "Black") if opponent_in_check else None
    else:
        cur["turn"]=opponent
        cur["check"]=opponent_in_check
        cur["result"]=None
    return _seal(cur)
def stop(s,*,request_id:object):
    cur=_copy(s);req=_req(request_id)
    if any(x["request_id"]==req for x in cur["request_receipts"]):return cur
    if cur["status"]!="active":raise ValueError("chess_stop_denied")
    cur["status"]="stopped";cur["request_receipts"].append({"request_id":req,"action":"stop"});return _seal(cur)
