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
 start.disabled=busy||state?.status==="active";
 q("[data-mode]").disabled=busy||state?.status==="active";
 q("[data-agent]").disabled=busy||state?.status==="active";
 q("[data-difficulty]").disabled=busy;
 const active=state?.status==="active";
 q("[data-start]").hidden=active;
 start.textContent=state?"New game":"Play";
 q("[data-controls]").hidden=!active;
 q("[data-stop]").hidden=!active;
 q("[data-resign]").hidden=!active;
 q("[data-stop]").disabled=busy;
 q("[data-resign]").disabled=busy;
 if(state){
  q("[data-players]").hidden=false;
  q("[data-red-player]").textContent=state.players[0].name;
  q("[data-yellow-player]").textContent=state.players[1].name;
  const winner=state.players.find(player=>player.id===state.winner_id);
  const turn=state.current_player_name+"’s turn";
  q("[data-turn]").textContent=active?turn:winner?winner.name+" wins":state.status==="stopped"?"Match stopped":"Draw";
 }
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
 const cells=state?state.board.flat():Array(42).fill(0);
 const colors=["empty","red","yellow"];
 board.setAttribute("aria-label",state?"Connect 4 board. Rows top to bottom: "+state.board.map(row=>row.map(piece=>colors[piece]).join(", ")).join("; "):"Empty Connect 4 board");
 cells.forEach(value=>{
  const cell=document.createElement("div");
  cell.className="c4-cell"+(value===1?" c4-p1":value===2?" c4-p2":"");
  board.append(cell);
 });
}
async function runAgent(){
 if(!agentMode||state?.status!=="active"||state.current_player_id!=="p2")return;
 const key=q("[data-agent]").value,difficulty=q("[data-difficulty]").value;
 const response=await post("/arena/connect4/agent-move",{agent_key:key,difficulty,request_id:req()});
 state=response;
 q("[data-agent-status]").textContent="";
 q("[data-retry-agent]").hidden=true;
 render();
}
async function action(path,payload,followAgent=false){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  state=await post(path,payload);
  if(path.endsWith("/start")){
   q("[data-settings]").open=false;
   q("[data-agent-status]").textContent="";
   q("[data-retry-agent]").hidden=true;
  }
  if(state.status!=="active"){
   q("[data-agent-status]").textContent="";
   q("[data-retry-agent]").hidden=true;
  }
  render();
  if(followAgent)await runAgent();
 }catch(e){
  error(e);
  if(agentMode&&state?.status==="active"&&state.current_player_id==="p2"){
   q("[data-agent-status]").textContent="Agent action could not finish. Resume its turn to continue.";
   q("[data-retry-agent]").hidden=false;
  }
 }finally{busy=false;render();}
}
q("[data-mode]").onchange=()=>{
 if(state?.status==="active")return;
 agentMode=q("[data-mode]").value==="agent";
 q("[data-human-wrap]").hidden=agentMode;q("[data-agent-wrap]").hidden=!agentMode;
};
q("[data-start]").onclick=()=>{
 if(busy||state?.status==="active")return;
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
q("[data-retry-agent]").onclick=()=>{
 if(busy||!agentMode||state?.status!=="active"||state.current_player_id!=="p2")return;
 busy=true;q("[data-error]").textContent="";render();
 runAgent().catch(error).finally(()=>{busy=false;render();});
};
q("[data-resign]").onclick=()=>{if(busy||state?.status!=="active")return;action("/arena/connect4/resign",{request_id:req()});};
q("[data-stop]").onclick=()=>{
 if(busy||state?.status!=="active")return;
 action("/arena/connect4/stop",{request_id:req()});
};
render();
})();
