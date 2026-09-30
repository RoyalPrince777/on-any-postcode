(()=>{
"use strict";
const root=document.querySelector("[data-oware-root]");if(!root)return;
const q=s=>root.querySelector(s);const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}
function pitButton(index){const b=document.createElement("button");b.type="button";b.className="arena-choice";b.dataset.pit=String(index);b.textContent=String(state.pits[index]);b.setAttribute("aria-label","House "+(index+1)+": "+state.pits[index]+" seeds");const legal=state.status==="active"&&state.legal_pits.includes(index);b.disabled=busy||!legal;if(legal)b.setAttribute("aria-pressed","false");return b;}
function row(indices,label){const wrap=document.createElement("div");wrap.className="arena-choices";wrap.setAttribute("role","group");wrap.setAttribute("aria-label",label);for(const index of indices)wrap.append(pitButton(index));return wrap;}
function render(){
 if(!state)return;
 q("[data-game]").hidden=false;
 q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-status]").textContent=state.draw?"Draw":state.status;
 q("[data-score]").textContent=state.players.map(p=>p.name+" "+p.captured).join(" · ");
 const board=q("[data-board]");board.replaceChildren();
 board.append(row([11,10,9,8,7,6],"Player Two houses"),row([0,1,2,3,4,5],"Player One houses"));
 const active=state.status==="active";
 q("[data-start]").disabled=busy||active;q("[data-players]").disabled=busy||active;q("[data-stop]").disabled=busy||!active;
 if(state.status==="completed"){const winner=state.players.find(p=>p.id===state.winner_id);q("[data-feedback]").textContent=state.draw?"24–24 draw.":"Winner: "+(winner?.name||"—");}
 else if(state.status==="stopped")q("[data-feedback]").textContent="Match stopped.";
 else q("[data-feedback]").textContent="Choose one of "+state.legal_pits.length+" legal houses. Captures occur only on the opponent side at 2 or 3 seeds.";
}
async function action(path,payload){if(busy)return;busy=true;q("[data-error]").textContent="";try{state=await post(path,payload);render();}catch(e){error(e);}finally{busy=false;render();}}
q("[data-start]").onclick=()=>action("/arena/oware/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-pit]");if(btn&&!btn.disabled)action("/arena/oware/move",{pit:Number(btn.dataset.pit),request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/oware/stop",{request_id:requestId()});
})();