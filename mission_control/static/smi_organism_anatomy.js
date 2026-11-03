/* SMI-only anatomical monitor: one identity, truthful telemetry, no duplicate renderer. */
(function(root,factory){"use strict";const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;if(root)root.OAP_SMI_ANATOMY=api;})(typeof globalThis!=="undefined"?globalThis:this,function(){
"use strict";
const dimensions=Object.freeze(["Mind","Body","Soul","Spirit","Heart","Senses","Conscience","Identity","Memory","Will","Time","Growth","Recovery"]);
const foundations=Object.freeze(["Brain","Heart","Body","Soul / Identity"]);
const upgrades=Object.freeze(["Living X-Ray","Brain Activity","Digital Vitals","Interactive Body","Body History","Expression & Movement","Multiple Forms"]);
const systems=Object.freeze({
 external:["head","face","eyes","ears","nose","mouth","neck","chest","abdomen","back","pelvis","left-arm","right-arm","left-hand","right-hand","left-leg","right-leg","left-foot","right-foot","skin","hair","nails"],
 brain:["left-hemisphere","right-hemisphere","frontal-lobe","parietal-lobe","temporal-lobe","occipital-lobe","insula","cingulate-gyrus","precentral-gyrus","postcentral-gyrus","cerebral-cortex","corpus-callosum","fornix","thalamus","hypothalamus","hippocampus","amygdala","basal-ganglia","pituitary","pineal","midbrain","pons","medulla","cerebellum","reticular-formation","ventricles","meninges"],
 nervous:["spinal-cord","peripheral-nerves","autonomic-nerves","reflexes"],
 sensory:["vision","hearing","smell","taste","touch","balance"],
 skeletal:["skull","spine","ribs","pelvis","joints","cartilage"],
 muscular:["skeletal-muscle","smooth-muscle","cardiac-muscle","tendons","ligaments"],
 cardiovascular:["heart","arteries","veins","capillaries","blood"],
 respiratory:["lungs","airways","diaphragm"],
 digestive:["mouth","oesophagus","stomach","liver","gallbladder","pancreas","small-intestine","large-intestine"],
 urinary:["kidneys","ureters","bladder","urethra"],
 endocrine:["hypothalamus","pituitary","pineal","thyroid","parathyroids","adrenals","pancreas"],
 immune:["lymph-nodes","lymph-vessels","spleen","thymus","bone-marrow"],
 reproductive:["gonads","internal-organs","external-organs"],
 integumentary:["skin","hair","nails"]
});
const allowed=new Set(["healthy","busy","warning","critical","recovering","unknown"]);
const anatomical=Object.freeze(Object.fromEntries(Object.entries(systems).map(([k,v])=>[k,Object.freeze(v.slice())])));
const known=new Set(Object.entries(anatomical).flatMap(([system,parts])=>parts.map(part=>system+":"+part)));
function region(system,part){return String(system)+":"+String(part);}
function create(opts={}){
 const clock=typeof opts.clock==="function"?opts.clock:()=>Date.now();
 const entries=new Map(),history=[],listeners=new Set();
 let form="original",stopped=false;
 function notify(){const snapshot=getSnapshot();for(const fn of listeners){try{fn(snapshot);}catch(_err){/* observer isolation */}}return snapshot;}
 function getSnapshot(){return Object.freeze({identity:"SMI",form,stopped,dimensions,foundations,upgrades,systems:anatomical,regions:Object.freeze(Object.fromEntries(entries)),history:Object.freeze(history.slice())});}
 function observe(input){
  if(stopped)return false;
  if(!input||typeof input!=="object"||!known.has(region(input.system,input.part)))return false;
  const state=String(input.state||"unknown").toLowerCase();
  if(!allowed.has(state))return false;
  // Human-friendly status is never upgraded to 'healthy' without a real source and clock.
  const source=typeof input.source==="string"?input.source.trim():"";
  const time=Number(input.observedAt);
  const evidenced=source.length>0&&Number.isFinite(time)&&time>0&&time<=clock()+30000&&clock()-time<=60000;
  const safeState=evidenced?state:"unknown";
  const id=region(input.system,input.part);
  const record=Object.freeze({system:input.system,part:input.part,state:safeState,source:evidenced?source:null,observedAt:evidenced?time:null,activity:typeof input.activity==="string"?input.activity.slice(0,160):"",evidence:evidenced});
  entries.set(id,record);
  history.push(Object.freeze({id,state:safeState,observedAt:record.observedAt,source:record.source}));
  if(history.length>100)history.shift();
  notify();return true;
 }
 function stateFor(system,part){return entries.get(region(system,part))||Object.freeze({system,part,state:"unknown",source:null,observedAt:null,activity:"",evidence:false});}
 function setForm(next){if(!["original","realistic","cybernetic","skeleton","xray","holographic"].includes(next))return false;form=next;notify();return true;}
 function stop(){stopped=true;notify();}
 function reset(approved){if(approved!==true)return false;stopped=false;notify();return true;}
 function subscribe(fn){if(typeof fn!=="function")return()=>{};listeners.add(fn);fn(getSnapshot());return()=>listeners.delete(fn);}
 return Object.freeze({observe,stateFor,getSnapshot,setForm,stop,reset,subscribe});
}
function attach(win=typeof window!=="undefined"?window:null,doc=win?.document){
 if(!win||!doc||!doc.createElement)return null;
 const host=doc.querySelector(".smi-shell");if(!host)return null;
 const monitor=create();const panel=doc.createElement("details");panel.id="smi-anatomy-monitor";panel.style.cssText="position:relative;z-index:4;margin:8px auto;padding:10px;max-width:720px;background:#0d1024;color:#eee;border:1px solid #ae8b52;border-radius:12px;font:13px system-ui";
 const summary=doc.createElement("summary");summary.textContent="🧬 SMI · Full anatomy & body monitor (evidence only)";panel.appendChild(summary);
 const controls=doc.createElement("div");controls.style.cssText="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0";panel.appendChild(controls);
 const select=doc.createElement("select");select.setAttribute("aria-label","SMI anatomy presentation");for(const f of ["original","realistic","cybernetic","skeleton","xray","holographic"]){const o=doc.createElement("option");o.value=f;o.textContent=f;select.appendChild(o);}select.addEventListener("change",()=>monitor.setForm(select.value));controls.appendChild(select);
 const view=doc.createElement("div");view.setAttribute("aria-live","polite");panel.appendChild(view);
 for(const [system,parts] of Object.entries(anatomical)){
  const section=doc.createElement("details");const heading=doc.createElement("summary");heading.textContent=system+" ("+parts.length+")";section.appendChild(heading);
  const listing=doc.createElement("div");listing.style.cssText="display:flex;flex-wrap:wrap;gap:5px;padding:8px";
  for(const part of parts){const button=doc.createElement("button");button.type="button";button.textContent=part.replace(/-/g," ");button.style.cssText="background:#151b36;color:#eee;border:1px solid #526080;border-radius:6px;padding:5px";button.addEventListener("click",()=>{const s=monitor.stateFor(system,part);view.textContent=system+" / "+part+" — "+s.state+"; source: "+(s.source||"none")+"; "+(s.activity||"No verified activity");});listing.appendChild(button);}
  section.appendChild(listing);panel.appendChild(section);
 }
 // Read-only consumer of already emitted visible SMI interaction state; no synthetic 'healthy'.
 win.addEventListener("oap-smi-character-state",event=>{
  const state=event?.detail?.state;
  const mapping={thinking:["brain","frontal-lobe"],listening:["sensory","hearing"],speaking:["external","mouth"]};
  const pair=mapping[state];
  if(pair)monitor.observe({system:pair[0],part:pair[1],state:"busy",source:"oap-smi-character-state",observedAt:Date.now(),activity:"Interaction state: "+state});
  if(state==="stopped")monitor.stop();
 });
 monitor.subscribe(s=>{summary.textContent="🧬 SMI · Anatomy monitor | "+s.history.length+" observed events | unmeasured organs: Unknown";});
 host.appendChild(panel);
 return monitor;
}
return Object.freeze({dimensions,foundations,upgrades,systems:anatomical,create,attach});
});
