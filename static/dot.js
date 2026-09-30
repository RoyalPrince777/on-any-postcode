(()=>{
"use strict";const root=document.querySelector("[data-dot-root]");if(!root)return;
const q=s=>root.querySelector(s),csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const res=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok)throw new Error(data?.error?.code||"arena_request_failed");return data;}
const edges=[];
for(let x=0;x<3;x++)for(let y=0;y<3;y++){if(x<2)edges.push([x+","+y,(x+1)+","+y]);if(y<2)edges.push([x+","+y,x+","+(y+1)]);}
function render(){
 if(!state)return;q("[data-game]").hidden=false;
 const active=state.status==="active";
 q("[data-turn]").textContent=active?state.turn_player:"—";
 q("[data-status]").textContent=state.status;q("[data-stop]").disabled=busy||!active;q("[data-draw]").disabled=busy||!active;
 const drawn=state.edges||[],container=q("[data-edges]");container.replaceChildren();
 for(const [a,b] of edges){const taken=drawn.some(e=>e[0]===a&&e[1]===b||e[0]===b&&e[1]===a);
  const btn=document.createElement("button");btn.type="button";btn.dataset.a=a;btn.dataset.b=b;
  btn.textContent=a+" → "+b+(taken?" ✓":"");btn.disabled=busy||!active||taken;
  btn.setAttribute("aria-label","Draw edge "+a+" to "+b+(taken?" (already drawn)":""));container.append(btn);}
 q("[data-score]").textContent=state.players.map(p=>p.name+": "+p.score).join(" · ");
 q("[data-state]").textContent="Completed boxes: "+Object.keys(state.boxes||{}).length+"/4"+
  (state.status==="completed"?" · Game finished":state.status==="stopped"?" · Match stopped":"");
}
async function act(url,payload){if(busy)return;busy=true;q("[data-error]").textContent="";try{state=await post(url,payload);render();}catch(e){error(e);}finally{busy=false;render();}}
q("[data-start]").onclick=()=>act("/arena/dot/start",{});
q("[data-draw]").onclick=()=>act("/arena/dot/draw",{a:q("[data-a]").value.trim(),b:q("[data-b]").value.trim(),request_id:requestId()});
q("[data-edges]").onclick=e=>{const btn=e.target.closest("[data-a]");if(!btn||btn.disabled)return;
 q("[data-a]").value=btn.dataset.a;q("[data-b]").value=btn.dataset.b;
 act("/arena/dot/draw",{a:btn.dataset.a,b:btn.dataset.b,request_id:requestId()});};
q("[data-stop]").onclick=()=>act("/arena/dot/stop",{request_id:requestId()});
})();