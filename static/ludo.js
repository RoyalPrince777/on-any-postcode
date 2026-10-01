(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s),csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}
function pieceLabel(position,finish){if(position===-1)return"Yard";if(position===finish)return"Home";if(position>=52)return"Home lane "+(position-51);return"Track "+position;}
function render(){
 if(!state)return;
 q("[data-game]").hidden=false;
 const active=state.status==="active",rolled=Number.isInteger(state.die);
 q("[data-turn]").textContent=active?state.current_player_name:"—";
 q("[data-status]").textContent=state.status==="completed"?"Finished":state.status;
 q("[data-die]").textContent=rolled?String(state.die):"—";
 q("[data-start]").disabled=busy||active;q("[data-players]").disabled=busy||active;
 q("[data-roll]").disabled=busy||!active||rolled;q("[data-stop]").disabled=busy||!active;
 const view=q("[data-players-view]");view.replaceChildren();
 state.players.forEach((player,playerIndex)=>{
  const card=document.createElement("section");card.className="ludo-player";
  const title=document.createElement("strong");title.textContent=player.name+(player.id===state.current_player_id?" · TURN":"");
  const pieces=document.createElement("div");pieces.className="ludo-pieces";
  player.pieces.forEach((position,pieceIndex)=>{
   const button=document.createElement("button");button.type="button";button.className="ludo-piece";
   button.dataset.piece=String(pieceIndex);button.dataset.player=player.id;
   button.textContent="Token "+(pieceIndex+1)+" · "+pieceLabel(position,state.finish);
   button.disabled=busy||!active||playerIndex!==state.players.findIndex(p=>p.id===state.current_player_id)||!state.legal_pieces.includes(pieceIndex);
   pieces.append(button);
  });
  card.append(title,pieces);view.append(card);
 });
 const winner=state.players.find(p=>p.id===state.winner_id)?.name||"—";
 q("[data-feedback]").textContent=state.status==="completed"?"Winner: "+winner:
  state.status==="stopped"?"Match stopped.":
  rolled?(state.legal_pieces.length?"Choose one highlighted token to move "+state.die+".":"No legal token; turn passes automatically."):
  "Roll the die. A six can bring a token out of the yard.";
}
async function action(path,payload){if(busy)return;busy=true;q("[data-error]").textContent="";try{state=await post(path,payload);render();}catch(e){error(e);}finally{busy=false;render();}}
q("[data-start]").onclick=()=>action("/arena/ludo/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
q("[data-roll]").onclick=()=>action("/arena/ludo/roll",{request_id:requestId()});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-piece]");if(btn&&!btn.disabled)action("/arena/ludo/move",{piece_index:Number(btn.dataset.piece),request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
})();