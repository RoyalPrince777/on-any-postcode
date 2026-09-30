(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s);const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}
function render(){
 if(!state)return;
 q("[data-game]").hidden=false;q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-status]").textContent=state.status==="completed"?"Finished":state.status;
 const view=q("[data-players-view]");view.replaceChildren();
 for(const player of state.players){const row=document.createElement("div");row.className="arena-race-row";
  const title=document.createElement("strong");title.textContent=player.name+" · "+player.piece+"/"+state.board_end;
  const track=document.createElement("progress");track.max=state.board_end;track.value=player.piece;track.setAttribute("aria-label",player.name+" distance");
  row.append(title,track);view.append(row);}
 const active=state.status==="active";
 root.querySelectorAll("[data-step]").forEach(btn=>btn.disabled=busy||!active);
 q("[data-stop]").disabled=busy||!active;
 q("[data-feedback]").textContent=state.status==="completed"?
  "Winner: "+(state.players.find(p=>p.id===state.winner_id)?.name||"—"):
  state.status==="stopped"?"Match stopped.":"Choose a move from 1 to 6. This is manual movement, not a random dice roll.";
}
async function action(path,payload){if(busy)return;busy=true;q("[data-error]").textContent="";try{state=await post(path,payload);render();}catch(e){error(e);}finally{busy=false;render();}}
q("[data-start]").onclick=()=>action("/arena/ludo/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-step]");if(btn&&!btn.disabled)action("/arena/ludo/move",{steps:Number(btn.dataset.step),request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
})();