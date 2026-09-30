(() => {
  const root=document.querySelector("[data-route-empire-root]"); if(!root) return;
  const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
  const q=s=>root.querySelector(s); let state=null;
  const req=()=>crypto.randomUUID().replaceAll("-","").slice(0,16);
  const post=async(url,body)=>{const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(body)});const d=await r.json();if(!r.ok) throw new Error(d?.error?.code||"request_failed");return d};
  const render=()=>{
    if(!state)return; q("[data-setup]").hidden=true;q("[data-game]").hidden=false;
    q("[data-board-title]").textContent="🌍 "+state.location_label+" · Route Empire";
    q("[data-turn]").textContent=state.current_player_name;q("[data-round]").textContent=state.round;
    q("[data-status]").textContent=state.status==="completed"?"Winner: "+state.winner_id:state.status;root.querySelectorAll("[data-end-turn],[data-stop]").forEach(b=>b.disabled=state.status!=="active");
    q("[data-players-view]").innerHTML=state.players.map(p=>`<div class="re-node"><strong>${p.name}</strong><br>Points ${p.points} · Influence ${p.influence}</div>`).join("");
    q("[data-nodes]").innerHTML=state.nodes.map(n=>`<div class="re-node"><strong>${n.label}</strong><br>Owner: ${n.owner_id||"Open"} · Level ${n.level}<div class="re-actions"><button data-act="claim" data-node="${n.id}">Claim</button><button data-act="develop" data-node="${n.id}">Develop</button></div></div>`).join("");
  };
  q("[data-start]").addEventListener("click",async()=>{try{const players=q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean);state=await post("/arena/route-empire/start",{location:q("[data-location]").value,players});render()}catch(e){q("[data-error]").textContent=e.message}});
  q("[data-nodes]").addEventListener("click",async e=>{const b=e.target.closest("button[data-act]");if(!b)return;try{state=await post("/arena/route-empire/action",{action:b.dataset.act,node_id:b.dataset.node,request_id:req()});render()}catch(err){q("[data-status]").textContent=err.message}});
  q("[data-end-turn]").addEventListener("click",async()=>{try{state=await post("/arena/route-empire/action",{action:"end_turn",request_id:req()});render()}catch(e){q("[data-status]").textContent=e.message}});
  q("[data-stop]").addEventListener("click",async()=>{try{state=await post("/arena/route-empire/action",{action:"stop",request_id:req()});render()}catch(e){q("[data-status]").textContent=e.message}});
})();