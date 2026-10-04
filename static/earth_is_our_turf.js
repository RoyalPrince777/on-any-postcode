(()=>{"use strict";
const root=document.querySelector("[data-eiot-root]");if(!root)return;
const q=s=>root.querySelector(s);let state=JSON.parse(document.querySelector("#eiot-initial-state").textContent),busy=false;
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const POS={
 "phipps-bridge":[90,120],"wandle-path":[65,200],"phipps-bridge-road":[155,195],"phipps-cut":[115,235],
 "lavender-park":[240,130],"lavender-avenue":[300,205],"lavender-cut":[260,245],"mount-road":[210,290],"western-road":[355,285],
 "figges-marsh":[430,135],"market-lane":[450,220],"town-centre":[520,305],"marsh-path":[455,370],"cricket-green":[565,430],
 "armfield-crescent":[680,330],"st-marks-road":[735,285],"laburnum-road":[790,220],"eastfields":[845,150],"estate-cut":[865,255],
 "pollards-hill":[900,415],"ravensbury":[430,500],"lower-mitcham":[300,610],"junction":[145,665],
 "mitcham-common":[610,650],"common-trail":[525,575]
};
function p(id){return POS[id]||[500,380]}
function nodeById(id){return state.nodes.find(n=>n.id===id)}
function streamed(id){const n=nodeById(id);return !!n&&state.loaded_chunks.includes(n.chunk)}
function lineMarkup(link){
 const a=p(link.from),b=p(link.to),base=link.kind==="alley"?"eiot-alley":link.kind==="footpath"?"eiot-footpath":"eiot-road";
 const dim=streamed(link.from)&&streamed(link.to)?"":" eiot-link-dim";
 return '<line class="'+base+dim+'" x1="'+a[0]+'" y1="'+a[1]+'" x2="'+b[0]+'" y2="'+b[1]+'"></line>';
}
function routePoints(){
 if(!state.active_route?.nodes?.length)return "";
 return state.active_route.nodes.map(id=>p(id).join(",")).join(" ");
}
function render(){
 q("[data-time]").textContent=" "+state.time_label;q("[data-day]").textContent=" "+state.day;
 q("[data-influence]").textContent=" "+state.player.influence;q("[data-mode-view]").textContent=" "+state.player.travel_mode;\n const ch=state.character;q("[data-my-card]").innerHTML="<strong>"+esc(ch.my_card.display_name)+" · My Card</strong><br>"+esc(ch.my_card.home)+" · "+esc(ch.my_card.title)+"<br>M Town rep "+ch.reputation.m_town+" · Health "+ch.vitals.health+" · Energy "+ch.vitals.energy;
 q("[data-chunk-view]").textContent=" "+(state.chunks?.[state.active_chunk]?.label||state.active_chunk);
 q("[data-traffic]").textContent=" "+state.environment.traffic;
 const here=state.nodes.find(n=>n.id===state.player.node);q("[data-location]").textContent=here.label;\n q("[data-local-voice]").textContent=state.language?.arrival||"";
 q("[data-environment]").innerHTML="<strong>Environment Intelligence</strong><br>Footfall "+state.environment.footfall+" · Shops "+state.environment.shop_activity+" · Parks "+state.environment.park_activity+"<br>"+esc(state.environment.lighting)+" · "+esc(state.environment.soundscape)+" · "+esc(state.environment.visibility)+"<br><small>Game simulation · not live telemetry</small>";
 q("[data-living]").innerHTML="<strong>Living Streets</strong><br>Traffic "+state.living.counts.moving_traffic+" · Pedestrians "+state.living.counts.pedestrians+" · Persistent vehicles "+state.living.counts.persistent_vehicles+" · Entrances "+state.living.counts.entrances+"<br><small>Game simulation · fictionalised fine detail · not live traffic</small>";
 q("[data-links]").innerHTML=state.navigation_links.map(lineMarkup).join("");
 const routeLine=q("[data-route-line]"),pts=routePoints();routeLine.setAttribute("points",pts);routeLine.hidden=!pts;
 root.querySelectorAll(".eiot-pin").forEach(n=>n.remove());
 const map=q("[data-map]");
 state.nodes.forEach(n=>{const xy=p(n.id),b=document.createElement("button");b.className="eiot-pin";b.type="button";b.dataset.node=n.id;b.dataset.streamed=String(state.loaded_chunks.includes(n.chunk));b.style.left=(xy[0]/10)+"%";b.style.top=(xy[1]/7.6)+"%";b.setAttribute("aria-current",String(n.id===state.player.node));b.textContent=(n.id===state.player.node?"● ":"")+n.label;map.appendChild(b)});
 const dest=q("[data-destination]"),prior=dest.value;dest.replaceChildren();
 state.nodes.filter(n=>n.id!==state.player.node).forEach(n=>{const o=document.createElement("option");o.value=n.id;o.textContent=n.label;dest.appendChild(o)});if([...dest.options].some(o=>o.value===prior))dest.value=prior;
 q("[data-mode]").value=state.player.travel_mode;
 const card=q("[data-route-card]");
 if(state.active_route){const pos=state.world_position;card.hidden=false;card.innerHTML="<strong>"+esc(state.active_route.mode.toUpperCase())+" route</strong><br>"+esc(state.active_route.labels.join(" → "))+"<br>"+state.active_route.distance_m+" m · "+state.active_route.steps.map(s=>esc(s.kind)).join(" / ")+(pos?"<br>Progress "+Math.round(pos.route_progress*100)+"% · "+Math.round(pos.remaining_m)+" m remaining":"")}else{card.hidden=true;card.textContent=""}
 const shops=state.businesses.filter(b=>b.node===here.id);q("[data-businesses]").innerHTML=shops.length?shops.map(b=>'<div class="eiot-business"><strong>'+esc(b.label)+'</strong><br>'+ (b.open?"OPEN":"CLOSED")+' · stock '+b.stock+' · remembers '+b.memory+'</div>').join(""):"<p>No ON ANY POSTCODE business at this point yet.</p>";
 q("[data-memory]").innerHTML=[...state.events].reverse().slice(0,12).map(e=>"<li>"+esc(e.type)+" · "+esc(e.node||e.to||e.minutes||"world")+(e.mode?" · "+esc(e.mode):"")+"</li>").join("")||"<li>No remembered actions yet.</li>";
 root.querySelectorAll("button").forEach(b=>b.disabled=busy);
 const travel=q('[data-action="advance-route"]');if(travel)travel.disabled=busy||!state.active_route;
}
async function act(command,target,mode,distance=null){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  const token=document.querySelector('meta[name="oap-csrf-token"]').content;
  const r=await fetch("/arena/earth-is-our-turf/action",{method:"POST",headers:{"Content-Type":"application/json","X-OAP-CSRF-Token":token},body:JSON.stringify({command,target,mode,distance})});
  const data=await r.json();if(!r.ok)throw new Error(data.error||"World action failed");state=data;
 }catch(e){q("[data-error]").textContent=e.message||String(e)}finally{busy=false;render()}
}
root.addEventListener("click",e=>{
 const pin=e.target.closest("[data-node]");if(pin&&pin.dataset.node!==state.player.node){q("[data-destination]").value=pin.dataset.node;act("navigate",pin.dataset.node,q("[data-mode]").value);return}
 const a=e.target.closest("[data-action]");if(!a)return;
 if(a.dataset.action==="navigate")act("navigate",q("[data-destination]").value,q("[data-mode]").value);
 else if(a.dataset.action==="advance-route")act("advance-route",null,state.player.travel_mode,100);
 else act(a.dataset.action,null,q("[data-mode]").value);
});
render();
})();