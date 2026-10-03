(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s);const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}
function pieceLabel(piece){if(piece.zone==="yard")return "Yard";if(piece.zone==="track")return "Track "+(piece.track_square+1);if(piece.zone==="home")return "Home "+piece.home_step;return "Finished";}
function render(){
 if(!state)return;
 q("[data-game]").hidden=false;q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-roll-value]").textContent=state.pending_roll??"—";
 q("[data-status]").textContent=state.status==="completed"?"Finished":state.status;
 const view=q("[data-players-view]");view.replaceChildren();
 for(const player of state.players){
  const row=document.createElement("section");row.className="arena-race-row";
  const title=document.createElement("strong");title.textContent=player.name+" · "+player.finished+"/4 home";
  const pieces=document.createElement("div");pieces.className="arena-actions";pieces.setAttribute("role","group");pieces.setAttribute("aria-label",player.name+" pieces");
  for(const piece of player.pieces){
   const btn=document.createElement("button");btn.type="button";btn.dataset.piece=piece.id;btn.textContent=piece.id.split("-").at(-1)+" · "+pieceLabel(piece);
   const selectable=state.status==="active"&&player.id===state.current_player_id&&state.movable_piece_ids.includes(piece.id)&&state.pending_roll!==null;
   btn.disabled=busy||!selectable;pieces.append(btn);
  }
  row.append(title,pieces);view.append(row);
 }
 const active=state.status==="active",pending=state.pending_roll!==null;
 q("[data-start]").disabled=busy||active;
 q("[data-players]").disabled=busy||active;
 q("[data-roll]").disabled=busy||!active||pending;
 q("[data-stop]").disabled=busy||!active;
 const feedback=q("[data-feedback]");
 if(state.status==="completed"){feedback.textContent="Winner: "+(state.winner_name||state.players.find(p=>p.id===state.winner_id)?.name||"—")+" · All four pieces home";}
 else if(state.status==="stopped"){feedback.textContent="Match stopped.";}
 else if(pending&&state.movable_piece_ids.length){feedback.textContent="Rolled "+state.pending_roll+". Choose a highlighted piece.";}
 else if(pending){feedback.textContent="Rolled "+state.pending_roll+".";}
 else{feedback.textContent="Roll the die.";}
}
async function action(path,payload){if(busy||(path==="/arena/ludo/start"&&state?.status==="active"))return;busy=true;q("[data-start]").disabled=true;q("[data-error]").textContent="";try{state=await post(path,payload);render();}catch(e){error(e);}finally{busy=false;q("[data-start]").disabled=state?.status==="active";render();}}
q("[data-start]").onclick=()=>action("/arena/ludo/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
q("[data-roll]").onclick=()=>action("/arena/ludo/roll",{request_id:requestId()});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-piece]");if(btn&&!btn.disabled)action("/arena/ludo/move",{piece_id:btn.dataset.piece,request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
})();