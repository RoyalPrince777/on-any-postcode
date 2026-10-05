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
 q("[data-influence]").textContent=" "+state.player.influence;q("[data-mode-view]").textContent=" "+state.player.travel_mode;
 const ch=state.character;q("[data-my-card]").innerHTML="<strong>"+esc(ch.my_card.display_name)+" · My Card</strong><br>"+esc(ch.my_card.home)+" · "+esc(ch.my_card.title)+"<br>M Town rep "+ch.reputation.m_town+" · Health "+ch.vitals.health+" · Energy "+ch.vitals.energy;
 q("[data-chunk-view]").textContent=" "+(state.chunks?.[state.active_chunk]?.label||state.active_chunk);
 q("[data-traffic]").textContent=" "+state.environment.traffic;
 const here=state.nodes.find(n=>n.id===state.player.node);q("[data-location]").textContent=here.label;
 q("[data-local-voice]").textContent=state.language?.arrival||"";
 q("[data-environment]").innerHTML="<strong>Environment Intelligence</strong><br>Footfall "+state.environment.footfall+" · Shops "+state.environment.shop_activity+" · Parks "+state.environment.park_activity+"<br>"+esc(state.environment.lighting)+" · "+esc(state.environment.soundscape)+" · "+esc(state.environment.visibility)+"<br><small>Game simulation · not live telemetry</small>";
 q("[data-living]").innerHTML="<strong>Living Streets</strong><br>Traffic "+state.living.counts.moving_traffic+" · Pedestrians "+state.living.counts.pedestrians+" · Persistent vehicles "+state.living.counts.persistent_vehicles+" · Entrances "+state.living.counts.entrances+"<br><small>Game simulation · fictionalised fine detail · not live traffic</small>";
 const hereVehicles=state.living.persistent_vehicles.filter(v=>v.node===state.player.node);
 const hereEntrances=state.living.entrances.filter(v=>v.node===state.player.node);
 const hereParking=state.living.parking.filter(v=>v.node===state.player.node);
 const activeVehicle=state.vehicle_life?.active_vehicle_id;
 const vehicleActions=hereVehicles.map(v=>{
  const owned=state.character.owned.vehicles.includes(v.id);
  if(activeVehicle===v.id)return "<button type=\"button\" data-action=\"exit-vehicle\">Exit "+esc(v.label)+"</button>";
  if(owned)return "<button type=\"button\" data-action=\"enter-vehicle\" data-target=\""+esc(v.id)+"\">Enter "+esc(v.label)+"</button>";
  return "<button type=\"button\" data-action=\"claim-vehicle\" data-target=\""+esc(v.id)+"\">Claim "+esc(v.label)+"</button>";
 }).join(" ");
 const parkingActions=activeVehicle?hereParking.map(p=>"<button type=\"button\" data-action=\"park-vehicle\" data-target=\""+esc(p.id)+"\">Park · "+esc(p.kind)+"</button>").join(" "):"";
 const entranceActions=hereEntrances.map(e=>"<button type=\"button\" data-action=\"use-entrance\" data-target=\""+esc(e.id)+"\">Use "+esc(e.label)+"</button>").join(" ");
 q("[data-vehicle-life]").innerHTML="<strong>Vehicle Life + Entrances</strong><br>"+(vehicleActions||"No persistent vehicle here")+"<br>"+parkingActions+"<br>"+entranceActions;
 const interior=state.interiors?.current_interior_id;
 const activeVid=state.vehicle_life?.active_vehicle_id;
 const vehicleState=activeVid?state.interiors?.vehicle_state?.[activeVid]:null;
 let interiorHtml="<strong>Interior + Vehicle State</strong><br>";
 interiorHtml+=interior?("Inside "+esc(interior)+' <button type="button" data-action="exit-interior">Exit interior</button>'):"Outside";
 if(vehicleState){
   interiorHtml+="<br>Condition "+Math.round(vehicleState.condition)+"% · "+esc(vehicleState.energy_type)+" "+Math.round(vehicleState.energy)+"% · "+vehicleState.odometer_m+" m";
   interiorHtml+='<br><button type="button" data-action="service-vehicle" data-target="'+esc(activeVid)+'">Service</button> <button type="button" data-action="restore-vehicle-energy" data-target="'+esc(activeVid)+'">Restore '+esc(vehicleState.energy_type)+'</button>';
 }
 q("[data-interior-state]").innerHTML=interiorHtml;


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
function showPanel(name,forceOpen=true){
 const side=q("[data-side]");if(!side)return;
 root.querySelectorAll("[data-panel]").forEach(p=>p.hidden=p.dataset.panel!==name);
 root.querySelectorAll("[data-ui-panel]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.uiPanel===name)));
 if(forceOpen)side.dataset.open="true";
}
function closeSheet(){const side=q("[data-side]");if(side)side.dataset.open="false"}
root.addEventListener("click",e=>{
 const ui=e.target.closest("[data-ui-panel]");if(ui){
  const side=q("[data-side]"),same=ui.getAttribute("aria-selected")==="true"&&side?.dataset.open==="true";
  if(same){closeSheet();return}
  showPanel(ui.dataset.uiPanel,true);return;
 }
 const pin=e.target.closest("[data-node]");if(pin&&pin.dataset.node!==state.player.node){showPanel("travel",true);q("[data-destination]").value=pin.dataset.node;act("navigate",pin.dataset.node,q("[data-mode]").value);return}
 const a=e.target.closest("[data-action]");if(!a)return;
 if(a.dataset.action==="navigate")act("navigate",q("[data-destination]").value,q("[data-mode]").value);
 else if(a.dataset.action==="advance-route")act("advance-route",null,state.player.travel_mode,100);
 else act(a.dataset.action,a.dataset.target||null,q("[data-mode]").value);
});
showPanel("travel",window.matchMedia("(min-width:861px)").matches);render();
})();