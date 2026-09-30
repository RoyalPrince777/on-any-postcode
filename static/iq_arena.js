(()=>{
"use strict";
const root=document.querySelector("[data-iq-root]");if(!root)return;
const q=s=>root.querySelector(s),csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;
const req=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){
 const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",
  headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});
 const d=await r.json();if(!r.ok)throw new Error(d?.error?.code||"request_failed");return d;
}
function render(){
 q("[data-start]").disabled=busy||state?.status==="active";
 q("[data-stop]").disabled=busy||state?.status!=="active";
 if(!state)return;
 q("[data-play]").hidden=false;q("[data-status]").textContent=state.status;
 q("[data-score]").textContent=state.score;q("[data-total]").textContent=state.total;
 const profile=q("[data-profile]");profile.replaceChildren();
 for(const [domain,value] of Object.entries(state.domain_scores||{})){
  const card=document.createElement("div");card.className="iq-card";
  const title=document.createElement("strong");title.textContent=domain;
  const line=document.createElement("p");line.textContent=value+"/1";card.append(title,line);profile.append(card);
 }
 const node=q("[data-question]");node.replaceChildren();
 if(!state.question){
  if(state.status==="completed"){
   const h=document.createElement("h2");h.textContent="Challenge complete";
   const p=document.createElement("p");p.textContent="In-game skill profile only; not a clinical IQ score.";
   node.append(h,p);
  }return;
 }
 const caption=document.createElement("p");caption.textContent=state.question.domain+" · "+state.question.number+"/"+state.total;
 const h=document.createElement("h2");h.textContent=state.question.prompt;node.append(caption,h);
 for(const choice of state.question.choices){
  const button=document.createElement("button");button.type="button";button.className="iq-choice";
  button.dataset.choice=choice.id;button.textContent=choice.label;button.disabled=busy||state.status!=="active";
  node.append(button);
 }
}
async function act(url,payload){
 if(busy||(url==="/arena/iq/start"&&state?.status==="active"))return;
 busy=true;q("[data-error]").textContent="";render();
 try{state=await post(url,payload);}catch(e){error(e);}
 finally{busy=false;render();}
}
q("[data-start]").onclick=()=>act("/arena/iq/start",{});
q("[data-question]").onclick=e=>{
 const button=e.target.closest("[data-choice]");
 if(!button||button.disabled||!state?.question||state.status!=="active"||busy)return;
 act("/arena/iq/answer",{question_id:state.question.id,choice_id:button.dataset.choice,request_id:req()});
};
q("[data-stop]").onclick=()=>{if(state?.status==="active")act("/arena/iq/stop",{request_id:req()});};
render();
})();
