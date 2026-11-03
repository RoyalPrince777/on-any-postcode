(()=>{
"use strict";
const root=document.querySelector("[data-c4-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,agentMode=false,busy=false;
let lastMove=null;
const colours=[
 ["Gold","#f5c451"],["Red","#e45d68"],["Blue","#57b2fa"],
 ["Green","#50c995"],["Orange","#fa9b50"],["Pink","#ee87be"],["White","#f3f4f8"]
];
const icons=[["Crown","👑"],["Lion","🦁"],["Wolf","🐺"],["Diamond","💎"],["Star","⭐"],["Fire","🔥"],["Lightning","⚡"]];
function pieceSelection(){
 const mode=q("[data-piece-style]").value, select=q("[data-piece-choice]");
 const previous=Number(select.value)||0;
 select.replaceChildren();
 (mode==="icon"?icons:colours).forEach(([name],index)=>{
  const option=document.createElement("option");option.value=String(index);option.textContent=name;select.append(option);
 });
 select.value=String(Math.min(previous,6));
}
function winCells(board){
 for(let row=0;row<6;row++)for(let col=0;col<7;col++){
  const player=board[row][col];if(!player)continue;
  for(const [dr,dc] of [[0,1],[1,0],[1,1],[1,-1]]){
   const cells=Array.from({length:4},(_,i)=>[row+dr*i,col+dc*i]);
   if(cells.every(([r,c])=>r>=0&&r<6&&c>=0&&c<7&&board[r][c]===player))return cells.map(([r,c])=>r*7+c);
  }
 }
 return [];
}
function applyState(next){
 const previous=state?.board;
 lastMove=null;
 if(previous && state.game_id===next.game_id){
  for(let row=0;row<6;row++)for(let col=0;col<7;col++){
   if(previous[row][col]!==next.board[row][col]&&next.board[row][col])lastMove=row*7+col;
  }
 }
 state=next;
}
function dropColumn(column){
 if(busy||state?.status!=="active"||(agentMode&&state.current_player_id==="p2"))return;
 if(state.board[0][column]!==0)return;
 action("/arena/connect4/drop",{column,request_id:req()},true);
}
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
 if(!state)return;
 q("[data-game]").hidden=false;
 q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-status]").textContent=state.status;
 const activity=window.OAPGameplayProgress?.measure("connect4",state);
 q("[data-gameplay-percent]").textContent=activity?"Gameplay "+activity.value+"% · "+activity.label:"Gameplay percentage unavailable";
 q("[data-gameplay-bar]").value=activity?activity.value:0;
 const active=state.status==="active";
 q("[data-stop]").disabled=busy||!active;q("[data-resign]").disabled=busy||!active;
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
 const iconMode=q("[data-piece-style]").value==="icon";
 const choice=Number(q("[data-piece-choice]").value)||0;
 board.style.setProperty("--c4-human",colours[choice][1]);
 const winners=state.result==="connect_four"?winCells(state.board):[];
 state.board.flat().forEach((value,index)=>{
  const column=index%7;
  const cell=document.createElement("button");
  cell.type="button";cell.dataset.col=String(column);
  cell.className="c4-cell"+(value===1?" c4-p1":value===2?" c4-p2":"")+
    (winners.includes(index)?" c4-winning":"")+(lastMove===index?" c4-last c4-placed":"");
  cell.textContent=iconMode&&value?(value===1?icons[choice][1]:"●"):"";
  cell.setAttribute("aria-label","Row "+(Math.floor(index/7)+1)+", column "+(column+1)+
    (value===1?", your piece":value===2?", opponent piece":", empty")+
    (winners.includes(index)?", winning piece":"")+". Tap to drop into column "+(column+1));
  cell.disabled=locked||state.board[0][column]!==0;
  board.append(cell);
 });
 const feedback=q("[data-match-feedback]");
 feedback.textContent=state.status==="completed"?
  (state.winner_id?state.players.find(p=>p.id===state.winner_id)?.name+" wins!":state.result==="draw_full_board"?"Draw — board full.":"Match completed."):
  state.status==="stopped"?"Match stopped.":locked?"Opponent turn.":"Your turn — tap a circle to drop.";
}
async function runAgent(){
 if(!agentMode||state?.status!=="active"||state.current_player_id!=="p2")return;
 const key=q("[data-agent]").value,difficulty=q("[data-difficulty]").value;
 q("[data-agent-status]").textContent="Agent turn · calculating legal move…";
 const response=await post("/arena/connect4/agent-move",{agent_key:key,difficulty,request_id:req()});
 applyState(response);
 q("[data-agent-status]").textContent=response.agent.name+" · "+response.agent.fit_stars+"/7 stars · "+difficulty;
 q("[data-retry-agent]").hidden=true;
 render();
}
async function action(path,payload,followAgent=false){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  applyState(await post(path,payload));
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
q("[data-piece-style]").onchange=()=>{pieceSelection();render();};
q("[data-piece-choice]").onchange=()=>render();
pieceSelection();
q("[data-board]").onclick=e=>{
 const button=e.target.closest("[data-col]");
 if(!button||button.disabled)return;
 dropColumn(Number(button.dataset.col));
};
q("[data-controls]").onclick=e=>{
 const button=e.target.closest("[data-col]");
 if(!button||button.disabled||busy||state?.status!=="active")return;
 dropColumn(Number(button.dataset.col));
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
})();
