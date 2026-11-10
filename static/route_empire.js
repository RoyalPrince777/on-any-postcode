(() => {
  const root=document.querySelector("[data-route-empire-root]"); if(!root) return;
  const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
  const q=s=>root.querySelector(s); let state=null,busy=false;
  const escapeText=v=>String(v??"").replace(/[&<>"\x27]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","\x27":"&#39;"}[ch]));
  const req=()=>crypto.randomUUID().replaceAll("-","").slice(0,16);
  const post=async(url,body)=>{const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(body)});const d=await r.json();if(!r.ok) throw new Error(d?.error?.code||"request_failed");return d};
  const render=()=>{
    if(!state)return; q("[data-setup]").hidden=true;q("[data-game]").hidden=false;
    q("[data-board-title]").textContent="🌍 "+state.location_label+" · Route Empire";
    q("[data-turn]").textContent=state.current_player_name;q("[data-round]").textContent=state.round;
    q("[data-status]").textContent=state.status==="completed"?"Winner: "+(state.winner_name||state.winner_id):state.status;
    root.querySelectorAll("[data-end-turn],[data-stop],[data-build-route]").forEach(b=>b.disabled=busy||state.status!=="active");
    q("[data-players-view]").innerHTML=state.players.map(p=>`<div class="re-node"><strong>${escapeText(p.name)}</strong><br>Points ${p.points} · Influence ${p.influence}</div>`).join("");
    q("[data-nodes]").innerHTML=state.nodes.map(n=>`<div class="re-node"><strong>${escapeText(n.label)}</strong><br>Owner: ${escapeText(n.owner_id||"Open")} · Level ${n.level}<div class="re-actions"><button data-act="claim" data-node="${escapeText(n.id)}">Claim</button><button data-act="develop" data-node="${escapeText(n.id)}">Develop</button></div></div>`).join("");
    root.querySelectorAll("[data-nodes] button").forEach(b=>b.disabled=busy||state.status!=="active");
    const owned=state.nodes.filter(n=>n.owner_id===state.current_player_id);
    for(const selector of ["[data-route-from]","[data-route-to]"]){
      const select=q(selector);select.replaceChildren();
      for(const n of owned){const o=document.createElement("option");o.value=n.id;o.textContent=n.label;select.append(o);}
      select.disabled=busy||state.status!=="active"||owned.length<2;
    }
  };
  const error=e=>{const message=e?.message||String(e);q("[data-error]").textContent=message;q("[data-game-error]").textContent=message;};
  async function act(url,payload){
    if(busy||(url==="/arena/route-empire/start"&&state?.status==="active")||
      (url!=="/arena/route-empire/start"&&state?.status!=="active"))return;
    busy=true;q("[data-start]").disabled=true;q("[data-error]").textContent="";q("[data-game-error]").textContent="";
    if(state)render();
    try{state=await post(url,payload);render();}
    catch(e){error(e);}
    finally{busy=false;q("[data-start]").disabled=state?.status==="active";if(state)render();}
  }
  q("[data-start]").onclick=()=>{
    const players=q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean);
    act("/arena/route-empire/start",{location:q("[data-location]").value,players});
  };
  q("[data-nodes]").onclick=e=>{
    const button=e.target.closest("button[data-act]");
    if(!button||button.disabled)return;
    act("/arena/route-empire/action",{action:button.dataset.act,node_id:button.dataset.node,request_id:req()});
  };
  q("[data-build-route]").onclick=()=>act("/arena/route-empire/action",{action:"route",node_id:q("[data-route-from]").value,target_node_id:q("[data-route-to]").value,request_id:req()});
  q("[data-end-turn]").onclick=()=>act("/arena/route-empire/action",{action:"end_turn",request_id:req()});
  q("[data-stop]").onclick=()=>act("/arena/route-empire/action",{action:"stop",request_id:req()});
})();