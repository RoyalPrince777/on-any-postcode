(()=>{"use strict";
const root=document.querySelector("[data-eiot-root]");if(!root)return;
const q=s=>root.querySelector(s);let state=JSON.parse(document.querySelector("#eiot-initial-state").textContent),busy=false;
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const POS={
 "figges-marsh":[220,180],"market-lane":[345,250],"town-centre":[470,315],"eastfields":[720,180],
 "estate-cut":[835,265],"pollards-hill":[835,405],"cricket-green":[610,455],"marsh-path":[380,430],
 "ravensbury":[360,505],"lower-mitcham":[255,615],"junction":[110,665],"mitcham-common":[555,650],
 "common-trail":[455,585]
};
function p(id){return POS[id]||[500,380]}
function lineMarkup(link){
 const a=p(link.from),b=p(link.to),cls=link.kind==="alley"?"eiot-alley":link.kind==="footpath"?"eiot-footpath":"eiot-road";
 return '<line class="'+cls+'" x1="'+a[0]+'" y1="'+a[1]+'" x2="'+b[0]+'" y2="'+b[1]+'"></line>';
}
function routePoints(){
 if(!state.active_route?.nodes?.length)return "";
 return state.active_route.nodes.map(id=>p(id).join(",")).join(" ");
}
function render(){
 q("[data-time]").textContent=" "+state.time_label;q("[data-day]").textContent=" "+state.day;
 q("[data-influence]").textContent=" "+state.player.influence;q("[data-mode-view]").textContent=" "+state.player.travel_mode;
 const here=state.nodes.find(n=>n.id===state.player.node);q("[data-location]").textContent=here.label;
 q("[data-links]").innerHTML=state.navigation_links.map(lineMarkup).join("");
 const routeLine=q("[data-route-line]"),pts=routePoints();routeLine.setAttribute("points",pts);routeLine.hidden=!pts;
 root.querySelectorAll(".eiot-pin").forEach(n=>n.remove());
 const map=q("[data-map]");
 state.nodes.forEach(n=>{const xy=p(n.id),b=document.createElement("button");b.className="eiot-pin";b.type="button";b.dataset.node=n.id;b.style.left=(xy[0]/10)+"%";b.style.top=(xy[1]/7.6)+"%";b.setAttribute("aria-current",String(n.id===state.player.node));b.textContent=(n.id===state.player.node?"● ":"")+n.label;map.appendChild(b)});
 const dest=q("[data-destination]"),prior=dest.value;dest.replaceChildren();
 state.nodes.filter(n=>n.id!==state.player.node).forEach(n=>{const o=document.createElement("option");o.value=n.id;o.textContent=n.label;dest.appendChild(o)});if([...dest.options].some(o=>o.value===prior))dest.value=prior;
 q("[data-mode]").value=state.player.travel_mode;
 const card=q("[data-route-card]");
 if(state.active_route){card.hidden=false;card.innerHTML="<strong>"+esc(state.active_route.mode.toUpperCase())+" route</strong><br>"+esc(state.active_route.labels.join(" → "))+"<br>"+state.active_route.distance_m+" m · "+state.active_route.steps.map(s=>esc(s.kind)).join(" / ")}else{card.hidden=true;card.textContent=""}
 const shops=state.businesses.filter(b=>b.node===here.id);q("[data-businesses]").innerHTML=shops.length?shops.map(b=>'<div class="eiot-business"><strong>'+esc(b.label)+'</strong><br>'+ (b.open?"OPEN":"CLOSED")+' · stock '+b.stock+' · remembers '+b.memory+'</div>').join(""):"<p>No ON ANY POSTCODE business at this point yet.</p>";
 q("[data-memory]").innerHTML=[...state.events].reverse().slice(0,12).map(e=>"<li>"+esc(e.type)+" · "+esc(e.node||e.to||e.minutes||"world")+(e.mode?" · "+esc(e.mode):"")+"</li>").join("")||"<li>No remembered actions yet.</li>";
 root.querySelectorAll("button").forEach(b=>b.disabled=busy);
 const travel=q('[data-action="travel-route"]');if(travel)travel.disabled=busy||!state.active_route;
}
async function act(command,target,mode){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  const token=document.querySelector('meta[name="oap-csrf-token"]').content;
  const r=await fetch("/arena/earth-is-our-turf/action",{method:"POST",headers:{"Content-Type":"application/json","X-OAP-CSRF-Token":token},body:JSON.stringify({command,target,mode})});
  const data=await r.json();if(!r.ok)throw new Error(data.error||"World action failed");state=data;
 }catch(e){q("[data-error]").textContent=e.message||String(e)}finally{busy=false;render()}
}
root.addEventListener("click",e=>{
 const pin=e.target.closest("[data-node]");if(pin&&pin.dataset.node!==state.player.node){q("[data-destination]").value=pin.dataset.node;act("navigate",pin.dataset.node,q("[data-mode]").value);return}
 const a=e.target.closest("[data-action]");if(!a)return;
 if(a.dataset.action==="navigate")act("navigate",q("[data-destination]").value,q("[data-mode]").value);
 else if(a.dataset.action==="travel-route")act("travel-route",null,state.player.travel_mode);
 else act(a.dataset.action,null,q("[data-mode]").value);
});
render();
})();