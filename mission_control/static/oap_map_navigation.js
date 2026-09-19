(()=>{
const q=s=>document.querySelector(s),qa=s=>[...document.querySelectorAll(s)];
const body=document.body,routeSvg=q('#route-svg'),routeLine=q('#route-line'),status=q('#route-state');
const turnIcon=q('#turn-icon'),turnRoad=q('#turn-road'),turnDistance=q('#turn-distance');
const etaClock=q('#eta-clock'),etaRemain=q('#eta-remain'),routeDistance=q('#route-distance-hud');
const routeIntel=q('#route-intel'),etaIntel=q('#eta-intel'),peopleIntel=q('#people-intel'),liveIntel=q('#live-intel'),providerIntel=q('#provider-intel');
const sourceDrawer=q('#map-source-drawer'),sourceToggle=q('#map-source-toggle'),locate=q('#map-locate');
let currentRoute=null,currentGeometry=[],watchId=null,follow=true,lastPoint=null,lastHeading=0;
function setMode(mode){
  body.dataset.mapMode=mode;
  qa('[data-map-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mapMode===mode));
  try{localStorage.setItem('oap-map-mode',mode)}catch{}
}
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
function ensureVehicle(){
 if(!routeSvg)return null;
 let g=q('#vehicle-marker'); if(g)return g;
 g=document.createElementNS('http://www.w3.org/2000/svg','g');g.id='vehicle-marker';g.setAttribute('class','vehicle-marker');
 const poly=document.createElementNS('http://www.w3.org/2000/svg','polygon');poly.setAttribute('points','0,-18 13,14 0,9 -13,14');
 const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('r','4');
 g.append(poly,dot);routeSvg.append(g);return g;
}
function placeVehicle(lon,lat,heading){
 if(!currentGeometry.length)return;
 const b=padBounds(currentGeometry),p=project(lon,lat,b),g=ensureVehicle();
 g.setAttribute('transform',`translate(${p[0]} ${p[1]}) rotate(${Number.isFinite(heading)?heading:0})`);
}
function nearestProgress(lon,lat){
 if(!currentGeometry.length)return 0;
 let best=Infinity,index=0;
 currentGeometry.forEach((p,i)=>{const dx=(+p[0]-lon)*Math.cos(lat*Math.PI/180),dy=(+p[1]-lat),d=dx*dx+dy*dy;if(d<best){best=d;index=i}});
 return currentGeometry.length>1?index/(currentGeometry.length-1):0;
}
function updateFromPosition(pos){
 const {longitude,latitude,heading,speed}=pos.coords;
 let h=Number.isFinite(heading)?heading:lastHeading;
 if(!Number.isFinite(heading)&&lastPoint){
   const dx=(longitude-lastPoint[0])*Math.cos(latitude*Math.PI/180),dy=latitude-lastPoint[1];
   h=(Math.atan2(dx,dy)*180/Math.PI+360)%360;
 }
 lastHeading=h;lastPoint=[longitude,latitude];placeVehicle(longitude,latitude,h);
 const progress=nearestProgress(longitude,latitude);
 if(currentRoute){
   const remain=Math.max(0,(+currentRoute.distance_m||0)*(1-progress));
   routeDistance.textContent=(remain/1000).toFixed(remain<10000?1:0)+' km';
   etaRemain.textContent=Math.max(1,Math.round((+currentRoute.duration_s||0)*(1-progress)/60))+' min';
 }
 if(locate){locate.classList.add('active');locate.title='Using consented device position'+(Number.isFinite(speed)?' · '+Math.round(speed*3.6)+' km/h':'')}
}
function startLocation(){
 if(!navigator.geolocation){status.textContent='Device position unavailable';return}
 status.textContent='Location permission required · precise position is not stored';
 if(watchId!==null){navigator.geolocation.clearWatch(watchId);watchId=null;locate?.classList.remove('active');return}
 watchId=navigator.geolocation.watchPosition(updateFromPosition,err=>{
   status.textContent=err.code===1?'Location permission blocked':'Location temporarily unavailable';
   locate?.classList.remove('active');
 },{enableHighAccuracy:true,maximumAge:3000,timeout:10000});
}
function renderRoute(d){
 currentRoute=d?.route||null;currentGeometry=currentRoute?.geometry?.coordinates||[];
 const first=(currentRoute?.steps||[])[0];
 turnIcon.textContent=iconFor(first);turnRoad.textContent=instruction(first);turnDistance.textContent=Math.round(first?.distance_m||0)+' m';
 etaClock.textContent=formatEta(currentRoute?.duration_s);etaRemain.textContent=Math.max(1,Math.round((+currentRoute?.duration_s||0)/60))+' min';
 routeDistance.textContent=((+currentRoute?.distance_m||0)/1000).toFixed(1)+' km';
 routeIntel.textContent='Route Intelligence · first-party';routeIntel.dataset.state='live';
 etaIntel.textContent='ETA Intelligence · route model';etaIntel.dataset.state='live';
 const reports=currentRoute?.live_pattern_reports||[],verified=reports.filter(x=>x?.authority_verified===true).length;
 liveIntel.textContent=reports.length?`Live Pattern · ${reports.length} signal${reports.length===1?'':'s'}`:'Live Pattern · clear';liveIntel.dataset.state=verified?'attention':'live';
 peopleIntel.textContent='People Intelligence · aggregate only';peopleIntel.dataset.state='live';
 if(currentGeometry.length){const p=currentGeometry[0];placeVehicle(+p[0],+p[1],0)}
 loadProviders(d?.origin,d?.destination);
}
async function loadProviders(origin=null,destination=null){
 try{
   const params=new URLSearchParams();
   if(origin?.latitude!=null&&origin?.longitude!=null){params.set('start_latitude',origin.latitude);params.set('start_longitude',origin.longitude)}
   if(destination?.latitude!=null&&destination?.longitude!=null){params.set('end_latitude',destination.latitude);params.set('end_longitude',destination.longitude)}
   const url='/map-intelligence/oap-adapter'+(params.size?'?'+params.toString():'');
   const r=await fetch(url,{cache:'no-store',credentials:'same-origin'}),d=await r.json();
   const uber=d?.providers?.find(x=>x.id==='uber');
   providerIntel.textContent=uber?.live_ready?'OAP Adapter · mobility live':'OAP Adapter · OAP Direct';
   providerIntel.dataset.state=uber?.live_ready?'live':'attention';
   const holder=q('#provider-source-list'); if(holder){holder.textContent='';(d.providers||[]).forEach(p=>{const row=document.createElement('div');row.className='map-source-row';row.innerHTML='<b></b><span></span>';row.querySelector('b').textContent=p.id==='oap_direct'?'OAP Direct':'External mobility source';row.querySelector('span').textContent=p.live_ready?'Live':'Locked / unavailable';holder.append(row)})}
 }catch{providerIntel.textContent='OAP Adapter · status unavailable';providerIntel.dataset.state='attention'}
}
qa('[data-map-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mapMode)));
sourceToggle?.addEventListener('click',()=>sourceDrawer?.classList.toggle('show'));
locate?.addEventListener('click',startLocation);
window.addEventListener('oap-map-route-ready',e=>renderRoute(e.detail||{}));
window.addEventListener('pagehide',()=>{if(watchId!==null)navigator.geolocation?.clearWatch(watchId)});
setMode((()=>{try{return localStorage.getItem('oap-map-mode')||'explore'}catch{return'explore'}})());
loadProviders();
window.OAP_MAP_NAVIGATION={version:'1.0',modes:['explore','journey','drive','cockpit'],consentLocation:true,storesPreciseLocation:false,individualPeopleTracking:false};
})();