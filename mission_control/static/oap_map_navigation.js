(()=>{
const q=s=>document.querySelector(s);
const body=document.body,routeSvg=q('#route-svg'),roadsSvg=q('#roads-svg');
const turnCard=q('#turn-card'),turnIcon=q('#turn-icon'),turnRoad=q('#turn-road'),turnSub=q('#turn-sub'),turnDistance=q('#turn-distance');
const etaClock=q('#eta-clock'),etaRemain=q('#eta-remain'),routeDistance=q('#route-distance-hud');
const tripBar=q('#trip-bar'),driveToggle=q('#drive-toggle');
const details=q('#details-sheet'),detailsToggle=q('#details-toggle'),detailsClose=q('#details-close');
const locate=q('#map-locate'),recenter=q('#recenter'),zoomIn=q('#zoom-in'),zoomOut=q('#zoom-out');
const status=q('#route-state');
let currentRoute=null,currentGeometry=[],watchId=null,lastPoint=null,lastHeading=0,lastProjected=null;
let zoom=1,viewCenter=[500,350],driveMode=false;

function iconFor(step){
 const m=String(step?.modifier||'').toLowerCase(),t=String(step?.type||'').toLowerCase();
 if(t==='arrive')return '●'; if(m.includes('left'))return '↰'; if(m.includes('right'))return '↱'; if(m.includes('uturn'))return '↶'; return '↑';
}
function instruction(step){
 if(!step)return 'Route ready';
 if(step.type==='arrive')return 'Arrive at destination';
 return step.name?('Continue on '+step.name):'Continue';
}
function formatEta(seconds){
 const d=new Date(Date.now()+Math.max(0,+seconds||0)*1000);
 return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});
}
function padBounds(coords){
 const xs=coords.map(c=>+c[0]),ys=coords.map(c=>+c[1]);
 let minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys);
 const dx=Math.max(maxX-minX,.01),dy=Math.max(maxY-minY,.01);
 return{minX:minX-dx*.14,maxX:maxX+dx*.14,minY:minY-dy*.18,maxY:maxY+dy*.18};
}
function project(lon,lat,b){
 const p=50,dx=b.maxX-b.minX||1,dy=b.maxY-b.minY||1;
 return[p+((lon-b.minX)/dx)*(1000-p*2),p+(1-(lat-b.minY)/dy)*(700-p*2)];
}
function routeBounds(){return currentGeometry.length?padBounds(currentGeometry):null}
function applyView(){
 const w=1000/zoom,h=700/zoom;
 const cx=Math.min(1000-w/2,Math.max(w/2,viewCenter[0]));
 const cy=Math.min(700-h/2,Math.max(h/2,viewCenter[1]));
 const box=`${cx-w/2} ${cy-h/2} ${w} ${h}`;
 roadsSvg?.setAttribute('viewBox',box);routeSvg?.setAttribute('viewBox',box);
}
function setZoom(next){
 zoom=Math.max(1,Math.min(3.2,next));applyView();
}
function setDrive(on){
 driveMode=!!on;body.dataset.mapMode=driveMode?'drive':'explore';
 driveToggle.textContent=driveMode?'Overview':'Drive';
 if(driveMode){zoom=Math.max(2.1,zoom);if(lastProjected)viewCenter=lastProjected}
 else{zoom=1;viewCenter=[500,350]}
 applyView();
}
function ensureVehicle(){
 if(!routeSvg)return null;
 let g=q('#vehicle-marker');if(g)return g;
 g=document.createElementNS('http://www.w3.org/2000/svg','g');g.id='vehicle-marker';g.setAttribute('class','vehicle-marker');
 const poly=document.createElementNS('http://www.w3.org/2000/svg','polygon');poly.setAttribute('points','0,-18 13,14 0,9 -13,14');
 const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('r','4');
 g.append(poly,dot);routeSvg.append(g);return g;
}
function placeVehicle(lon,lat,heading){
 const b=routeBounds();if(!b)return;
 const p=project(lon,lat,b),g=ensureVehicle();lastProjected=p;
 g.setAttribute('transform',`translate(${p[0]} ${p[1]}) rotate(${Number.isFinite(heading)?heading:0})`);
 if(driveMode){viewCenter=p;applyView()}
}
function nearestProgress(lon,lat){
 if(!currentGeometry.length)return 0;
 let best=Infinity,index=0;
 currentGeometry.forEach((p,i)=>{
   const dx=(+p[0]-lon)*Math.cos(lat*Math.PI/180),dy=(+p[1]-lat),d=dx*dx+dy*dy;
   if(d<best){best=d;index=i}
 });
 return currentGeometry.length>1?index/(currentGeometry.length-1):0;
}
function activeStep(progress){
 const steps=Array.isArray(currentRoute?.steps)?currentRoute.steps:[];
 if(!steps.length)return null;
 const total=steps.reduce((sum,s)=>sum+Math.max(0,+s.distance_m||0),0)||1;
 const travelled=total*Math.max(0,Math.min(1,progress));
 let acc=0;
 for(const step of steps){const d=Math.max(0,+step.distance_m||0);if(travelled<=acc+d)return{step,remaining:Math.max(0,acc+d-travelled)};acc+=d}
 const last=steps.at(-1);return{step:last,remaining:0};
}
function updateTurn(progress){
 const hit=activeStep(progress);if(!hit)return;
 turnIcon.textContent=iconFor(hit.step);turnRoad.textContent=instruction(hit.step);
 turnSub.textContent=hit.step.type==='arrive'?'Destination':'Next turn';
 turnDistance.textContent=Math.round(hit.remaining)+' m';
}
function updateFromPosition(pos){
 const {longitude,latitude,heading}=pos.coords;
 let h=Number.isFinite(heading)?heading:lastHeading;
 if(!Number.isFinite(heading)&&lastPoint){
   const dx=(longitude-lastPoint[0])*Math.cos(latitude*Math.PI/180),dy=latitude-lastPoint[1];
   h=(Math.atan2(dx,dy)*180/Math.PI+360)%360;
 }
 lastHeading=h;lastPoint=[longitude,latitude];
 placeVehicle(longitude,latitude,h);
 if(driveMode)applyView();
 const progress=nearestProgress(longitude,latitude);updateTurn(progress);
 if(currentRoute){
   const remain=Math.max(0,(+currentRoute.distance_m||0)*(1-progress));
   routeDistance.textContent=(remain/1000).toFixed(remain<10000?1:0)+' km';
   etaRemain.textContent=Math.max(1,Math.round((+currentRoute.duration_s||0)*(1-progress)/60))+' min';
 }
 locate?.classList.add('active');
}
function startLocation(){
 if(!navigator.geolocation){status.textContent='Location unavailable';status.hidden=false;return}
 if(watchId!==null){navigator.geolocation.clearWatch(watchId);watchId=null;locate?.classList.remove('active');return}
 status.textContent='Allow location to follow your route';status.hidden=false;
 watchId=navigator.geolocation.watchPosition(updateFromPosition,err=>{
   status.textContent=err.code===1?'Location permission blocked':'Location unavailable';status.hidden=false;locate?.classList.remove('active');
 },{enableHighAccuracy:true,maximumAge:3000,timeout:10000});
}
function renderRoute(d){
 currentRoute=d?.route||null;currentGeometry=currentRoute?.geometry?.coordinates||[];
 if(!currentRoute)return;
 turnCard.hidden=false;tripBar.hidden=false;
 etaClock.textContent=formatEta(currentRoute.duration_s);
 etaRemain.textContent=Math.max(1,Math.round((+currentRoute.duration_s||0)/60))+' min';
 routeDistance.textContent=((+currentRoute.distance_m||0)/1000).toFixed(1)+' km';
 updateTurn(0);zoom=1;viewCenter=[500,350];applyView();
 if(currentGeometry.length){const p=currentGeometry[0];placeVehicle(+p[0],+p[1],0)}
}
driveToggle?.addEventListener('click',()=>setDrive(!driveMode));
detailsToggle?.addEventListener('click',()=>{details.hidden=!details.hidden;detailsToggle.setAttribute('aria-expanded',String(!details.hidden))});
detailsClose?.addEventListener('click',()=>{details.hidden=true;detailsToggle?.setAttribute('aria-expanded','false')});
locate?.addEventListener('click',startLocation);
recenter?.addEventListener('click',()=>{if(lastProjected){viewCenter=lastProjected;applyView()}else{viewCenter=[500,350];applyView()}});
zoomIn?.addEventListener('click',()=>setZoom(zoom+.45));
zoomOut?.addEventListener('click',()=>setZoom(zoom-.45));
window.addEventListener('oap-map-route-ready',e=>renderRoute(e.detail||{}));
window.addEventListener('pagehide',()=>{if(watchId!==null)navigator.geolocation?.clearWatch(watchId)});
window.OAP_MAP_NAVIGATION={version:'2.0',lowNoise:true,driveFollow:true,progressiveTurnGuidance:true,consentLocation:true,storesPreciseLocation:false,individualPeopleTracking:false};
})();