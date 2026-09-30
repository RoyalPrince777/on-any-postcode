(()=>{
"use strict";
const root=document.querySelector("[data-c4-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,agentMode=false,busy=false;
const req=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){
 const response=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",
  headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});
 const data=await response.json();
 if(!response.ok)throw new Error(data?.error?.code||"arena_request_failed");
 return data;
}
function render(){
 const start=q("[data-start]");
 start.disabled=busy;
 if(!state)return;
 q("[data-game]").hidden=false;
 q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-status]").textContent=state.status;
 const active=state.status==="active";
 q("[data-stop]").disabled=busy||!active;
 const controls=q("[data-controls]");controls.replaceChildren();
 const locked=busy||!active||(agentMode&&state.current_player_id==="p2");
 for(let column=0;column<7;column++){
  const button=document.createElement("button");button.type="button";
  button.dataset.col=String(column);button.textContent="↓";
  button.setAttribute("aria-label","Drop into column "+(column+1));
  button.disabled=locked||state.board[0][column]!==0;
  controls.append(button);
 }
 const board=q("[data-board]");board.replaceChildren();
 state.board.flat().forEach(value=>{
  const cell=document.createElement("div");
  cell.className="c4-cell"+(value===1?" c4-p1":value===2?" c4-p2":"");
  board.append(cell);
 });
}
async function runAgent(){
 if(!agentMode||state?.status!=="active"||state.current_player_id!=="p2")return;
 const key=q("[data-agent]").value,difficulty=q("[data-difficulty]").value;
 q("[data-agent-status]").textContent="Agent turn · calculating legal move…";
 const response=await post("/arena/connect4/agent-move",{agent_key:key,difficulty,request_id:req()});
 state=response;
 q("[data-agent-status]").textContent=response.agent.name+" · "+response.agent.fit_stars+"/7 stars · "+difficulty;
 render();
}
async function action(path,payload,followAgent=false){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  state=await post(path,payload);
  render();
  if(followAgent)await runAgent();
 }catch(e){
  error(e);
  if(agentMode&&state?.status==="active"&&state.current_player_id==="p2")
   q("[data-agent-status]").textContent="Agent action could not finish. Do not submit a second human turn.";
 }finally{busy=false;render();}
}
q("[data-mode]").onchange=()=>{
 if(state?.status==="active")return;
 agentMode=q("[data-mode]").value==="agent";
 q("[data-human-wrap]").hidden=agentMode;q("[data-agent-wrap]").hidden=!agentMode;
};
q("[data-start]").onclick=()=>{
 if(busy)return;
 agentMode=q("[data-mode]").value==="agent";
 const agentName=agentMode?q("[data-agent]").selectedOptions[0].text:q("[data-p2]").value;
 action("/arena/connect4/start",{player_one:q("[data-p1]").value,player_two:agentName,
  opponent_mode:agentMode?"agent":"human",agent_key:agentMode?q("[data-agent]").value:null});
};
q("[data-controls]").onclick=e=>{
 const button=e.target.closest("[data-col]");
 if(!button||button.disabled||busy||state?.status!=="active")return;
 action("/arena/connect4/drop",{column:Number(button.dataset.col),request_id:req()},true);
};
q("[data-stop]").onclick=()=>{
 if(busy||state?.status!=="active")return;
 action("/arena/connect4/stop",{request_id:req()});
};
})();
