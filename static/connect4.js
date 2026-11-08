(()=>{
"use strict";
const root=document.querySelector("[data-c4-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
const board=q("[data-board]");
const colour=q("[data-colour]");
const cells=Array.from({length:42},(_,index)=>{
 const cell=document.createElement("div");
 cell.className="c4-cell";
 cell.style.setProperty("--c4-fall", -(Math.floor(index/7)+1)*110+"%");
 board.append(cell);
 return cell;
});
const columns=Array.from({length:7},(_,column)=>{
 const button=document.createElement("button");
 button.type="button";
 button.dataset.col=String(column);
 button.setAttribute("aria-label","Drop into column "+(column+1));
 const arrow=document.createElement("span");
 arrow.textContent="↓";
 arrow.setAttribute("aria-hidden","true");
 button.append(arrow);
 q("[data-controls]").append(button);
 return button;
});
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
 colour.disabled=busy||active;
 start.hidden=active;
 start.textContent=state?"New game":"Play";
 q("[data-controls]").hidden=!active;
 q("[data-stop]").hidden=!active;
 q("[data-resign]").hidden=!active;
 q("[data-stop]").disabled=busy;
 q("[data-resign]").disabled=busy;
 const playerOneIsYellow=root.dataset.playerOneColour==="yellow";
 if(state){
  q("[data-players]").hidden=false;
  q("[data-red-player]").textContent=state.players[playerOneIsYellow?1:0].name;
  q("[data-yellow-player]").textContent=state.players[playerOneIsYellow?0:1].name;
  const winner=state.players.find(player=>player.id===state.winner_id);
  const turn=state.current_player_name+"’s turn";
  q("[data-turn]").textContent=active?turn:winner?winner.name+" wins":state.status==="stopped"?"Match stopped":"Draw";
 }
 const locked=busy||!active||(agentMode&&state.current_player_id==="p2");
 columns.forEach((button,column)=>{
  // Keep the focused column in place during network requests.
  button.setAttribute("aria-disabled",String(locked||state.board[0][column]!==0));
 });
 const pieces=state?.board.flat()||[];
 const colors=playerOneIsYellow?["empty","yellow","red"]:["empty","red","yellow"];
 board.setAttribute("aria-label",state?"Connect 4 board. Rows top to bottom: "+state.board.map(row=>row.map(piece=>colors[piece]).join(", ")).join("; "):"Empty Connect 4 board");
 cells.forEach((cell,index)=>{
  const piece=pieces[index]||0;
  cell.classList.toggle("c4-p1",piece===1);
  cell.classList.toggle("c4-p2",piece===2);
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
   root.dataset.playerOneColour=colour.value;
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
 if(!button||button.getAttribute("aria-disabled")==="true")return;
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
