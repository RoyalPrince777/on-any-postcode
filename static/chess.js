(()=>{
"use strict";const root=document.querySelector("[data-chess-root]");if(!root)return;
const q=s=>root.querySelector(s),csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false,selected=null;
const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const glyph={wK:"♔",wQ:"♕",wR:"♖",wB:"♗",wN:"♘",wP:"♙",bK:"♚",bQ:"♛",bR:"♜",bB:"♝",bN:"♞",bP:"♟"};
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(path,payload){const r=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data?.error?.code||"arena_request_failed");return data;}
function render(){
 if(!state)return;q("[data-game]").hidden=false;
 const active=state.status==="active";
 q("[data-turn]").textContent=active?state.turn:"—";q("[data-status]").textContent=state.status;
 q("[data-stop]").disabled=!active||busy;q("[data-move]").disabled=!active||busy;
 const board=q("[data-board]");board.replaceChildren();
 for(let rank=8;rank>=1;rank--)for(const file of "abcdefgh"){
  const id=file+rank,piece=state.board[id];const square=document.createElement("button");
  square.type="button";square.className="arena-chess-square "+(((file.charCodeAt(0)-97+rank)%2)?"arena-chess-dark":"arena-chess-light");
  square.dataset.square=id;square.disabled=!active||busy;
  square.textContent=glyph[piece]||"";
  square.setAttribute("aria-label",id+" "+(piece?(piece[0]==="w"?"White ":"Black ")+({K:"king",Q:"queen",R:"rook",B:"bishop",N:"knight",P:"pawn"}[piece[1]]):"empty"));
  square.setAttribute("aria-pressed",String(selected===id));board.append(square);
 }
 q("[data-feedback]").textContent=state.status==="completed"?"Winner: "+state.winner:state.status==="stopped"?"Match stopped.":selected?"Selected "+selected+". Choose destination.":"Select your piece or enter source and target squares.";
}
async function act(path,payload){if(busy)return;busy=true;q("[data-error]").textContent="";try{state=await post(path,payload);selected=null;render();}catch(e){error(e);}finally{busy=false;render();}}
function move(){
 const source=q("[data-source]").value.trim().toLowerCase(),target=q("[data-target]").value.trim().toLowerCase();
 if(!/^[a-h][1-8]$/.test(source)||!/^[a-h][1-8]$/.test(target)){error(new Error("Use squares a1–h8 (for example e2 → e4)."));return;}
 act("/arena/chess/move",{source,target,request_id:requestId()});
}
q("[data-start]").onclick=()=>act("/arena/chess/start",{});
q("[data-move]").onclick=move;
q("[data-stop]").onclick=()=>act("/arena/chess/stop",{request_id:requestId()});
q("[data-board]").onclick=e=>{
 const btn=e.target.closest("[data-square]");if(!btn||btn.disabled)return;
 const id=btn.dataset.square;
 if(!selected){selected=id;q("[data-source]").value=id;render();return;}
 if(selected===id){selected=null;q("[data-source]").value="";render();return;}
 q("[data-target]").value=id;move();
};
})();