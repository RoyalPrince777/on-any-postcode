(()=>{"use strict";
const root=document.querySelector("[data-eiot-root]");if(!root)return;
const q=s=>root.querySelector(s);let state=JSON.parse(document.querySelector("#eiot-initial-state").textContent),busy=false;
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
function render(){
 q("[data-time]").textContent=" "+state.time_label;q("[data-day]").textContent=" "+state.day;
 q("[data-influence]").textContent=" "+state.player.influence;q("[data-reputation]").textContent=" "+state.player.reputation;
 const here=state.nodes.find(n=>n.id===state.player.node);q("[data-location]").textContent=here.label;
 q("[data-map]").innerHTML=state.nodes.map(n=>'<button class="eiot-node" type="button" data-move="'+esc(n.id)+'" aria-current="'+(n.id===state.player.node)+'"><strong>'+esc(n.label)+'</strong><small>'+esc(n.kind)+' · memory '+n.memory+' · prosperity '+n.prosperity+' · activity '+n.activity+'</small></button>').join("");
 const shops=state.businesses.filter(b=>b.node===here.id);q("[data-businesses]").innerHTML=shops.length?shops.map(b=>'<div class="eiot-business"><strong>'+esc(b.label)+'</strong><br>'+ (b.open?"OPEN":"CLOSED")+' · stock '+b.stock+' · remembers '+b.memory+'</div>').join(""):"<p>No ON ANY POSTCODE business at this node yet.</p>";
 q("[data-memory]").innerHTML=[...state.events].reverse().slice(0,12).map(e=>"<li>"+esc(e.type)+" · "+esc(e.node||e.to||e.minutes||"world")+"</li>").join("")||"<li>No remembered actions yet.</li>";
 root.querySelectorAll("button").forEach(b=>b.disabled=busy);
}
async function act(command,target){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  const token=document.querySelector('meta[name="oap-csrf-token"]').content;
  const r=await fetch("/arena/earth-is-our-turf/action",{method:"POST",headers:{"Content-Type":"application/json","X-OAP-CSRF-Token":token},body:JSON.stringify({command,target})});
  const data=await r.json();if(!r.ok)throw new Error(data.error||"World action failed");state=data;
 }catch(e){q("[data-error]").textContent=e.message||String(e)}finally{busy=false;render()}
}
root.addEventListener("click",e=>{const m=e.target.closest("[data-move]");if(m){const here=state.nodes.find(n=>n.id===state.player.node);if(here.links.includes(m.dataset.move))act("move",m.dataset.move);return;}const a=e.target.closest("[data-action]");if(a)act(a.dataset.action);});
render();
})();