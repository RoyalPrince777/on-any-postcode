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
function winningColumns(board,piece){
 const cols=[];
 for(let col=0;col<7;col++){
  if(board[0][col]!==0)continue;
  const next=board.map(row=>row.slice());
  for(let row=5;row>=0;row--)if(next[row][col]===0){next[row][col]=piece;break;}
  if(winCells(next).length)cols.push(col);
 }
 return cols;
}
const personalities={
 fox:{name:"Fox",icon:"🦊",tone:"Quick hands, quicker wit.",intro:["Welcome to the trap department.","I promise nothing. Especially an easy win."],win:["Four connected. You got outfoxed!","Caught you looking the other way."],block:["Not today. I saw that postcode away.","That trap was missing a fox."],trap:["Two doors. Pick carefully.","That's what I call options."],move:["Quietly setting something up.","Don't mind me. Just being clever."],loss:["Fair play. You outfoxed the fox.","I'm filing an appeal with the woodland."],draw:["A draw? That wasn't in my cunning plan."],talk:["Trick is to watch what isn't played.","I can read the board. Your mind? Not so much."]},
 tiger:{name:"Shere Khan",icon:"🐅",tone:"Royal pressure. No empty threats.",intro:["Welcome to my jungle. Play well.","Your move. Earn my respect."],win:["Four in a row. The jungle has spoken.","A royal finish. Respect the board."],block:["I saw the ambush. Denied.","Good idea. I had a better one."],trap:["Two threats. Choose wisely.","The tiger controls the clearing."],move:["Patience is part of power.","I don't roar at every move."],loss:["A worthy victory. I respect good play.","You earned that. We go again."],draw:["Neither yields. Respect."],talk:["Strength without strategy is noise.","I challenge the move, not the player."]},
 neo:{name:"Neo",icon:"🕶️",tone:"Quiet. Precise. Sees patterns.",intro:["There is always another line.","Let's see the board for what it is."],win:["Four. The pattern was there.","You saw one path. I saw another."],block:["That line closes here.","The obvious move wasn't the only move."],trap:["Different paths. Same destination.","Watch the diagonals."],move:["The board is changing.","Some choices only make sense later."],loss:["You found the line. Good game.","I missed that path. Well played."],draw:["No winner in this version."],talk:["Look at the empty spaces.","A prediction isn't a guarantee."]},
 "queen-bee":{name:"Queen Bee",icon:"🐝",tone:"Organised and sharp.",intro:["The hive is ready. Are you?","Let's make every move count."],win:["The hive delivers. Four!","Flawless coordination, darling."],block:["The swarm covers that gap.","Not through my hive."],trap:["Two lanes. One queen.","A little teamwork goes a long way."],move:["Every piece has a job.","Sweet move. Mine is sweeter."],loss:["Well played. The hive learns.","I'll have to brief the workers."],draw:["A diplomatic result for the hive."],talk:["One piece is nothing without the pattern.","My workers call that strategic honey."]},
 octopus:{name:"Octopus",icon:"🐙",tone:"Flexible, many angles.",intro:["Eight arms. One board.","I'll keep my options open."],win:["Four connected. Plenty of arms left.","You covered one line. Not the other."],block:["Caught that with a spare arm.","That route is occupied."],trap:["Several lines, one move.","I'm reaching in more than one direction."],move:["Let's explore another angle.","I can change direction."],loss:["You slipped through. Well played.","Even eight arms can't catch everything."],draw:["A tangled finish."],talk:["Look for intersecting lines.","Eight arms don't mean eight turns."]},
 panther:{name:"Bagheera",icon:"🐈‍⬛",tone:"Calm, observant, disciplined.",intro:["A quiet board rewards patience.","Observe before you strike."],win:["Precision wins. Four.","A calm finish."],block:["That path was visible.","Patience made that easy."],trap:["Two openings. Neither accidental.","Every line has a purpose."],move:["Watch carefully.","Steady play is still dangerous."],loss:["A fine move. You earned it.","Well played. I misread that."],draw:["A balanced contest."],talk:["The centre matters, but not at any cost.","Think first. Move once."]},
 falcon:{name:"Falcon",icon:"🦅",tone:"Fast, sharp, decisive.",intro:["Eyes up. Game on.","I see the opening."],win:["Target acquired. Four!","Fast finish."],block:["Intercepted.","Too slow on that lane."],trap:["Two targets in sight.","The board's opening up."],move:["Quick decision.","Eyes on the next move."],loss:["You got there first. Respect.","That one flew past me."],draw:["Both held altitude."],talk:["Scan every column.","Speed without vision misses the target."]},
 owl:{name:"Owl",icon:"🦉",tone:"Thoughtful and dry.",intro:["Shall we think before we drop?","The night favours careful minds."],win:["A wise four, if I may say.","Interesting. Precisely as planned."],block:["I noticed that.","A most educational attempt."],trap:["Two answers to one question.","Consider the consequences."],move:["Hmm. Noted.","An intriguing development."],loss:["A lesson for us both. Well played.","Even owls occasionally blink."],draw:["A thoughtful stalemate."],talk:["Count the diagonals, not the compliments.","The board rarely lies."]},
 gorilla:{name:"Gorilla",icon:"🦍",tone:"Solid defence, warm humour.",intro:["Big hands. Gentle opening.","Let's build something solid."],win:["Four locked in. Gorilla power!","That's a strong finish."],block:["No getting through this wall.","I hold the line."],trap:["Strong on both sides.","Built that like a fortress."],move:["Solid move.","I like a sturdy position."],loss:["You broke the wall. Fair play.","Good game. I'll reinforce next time."],draw:["Two strong sides. No collapse."],talk:["Defence gives attack a foundation.","I don't throw the pieces. I place them."]}
};
let lastQuip="", lastAgentEvent="", banterCount=0, seenQuips=new Set();
function sayAgent(kind, details=""){
 if(!agentMode)return;
 const agent=personalities[q("[data-agent]").value]||personalities.panther;
 const lines=agent[kind]||agent.move;
 const fresh=lines.filter(line=>!seenQuips.has(kind+":"+line));
 const pool=fresh.length?fresh:lines;
 const index=(banterCount+String(state?.game_id||"").length)%pool.length;
 const line=pool[index];
 seenQuips.add(kind+":"+line);banterCount++;
 lastQuip=line;
 const output=q("[data-agent-status]");
 output.textContent=agent.icon+" "+agent.name+" · "+line;
 output.dataset.event=kind;
 const transcript=q("[data-agent-banter]");
 if(transcript){
  const entry=document.createElement("li");
  const who=document.createElement("strong");who.textContent=agent.icon+" "+agent.name+": ";
  entry.append(who,document.createTextNode(line));
  transcript.append(entry);
  while(transcript.children.length>5)transcript.firstElementChild.remove();
 }
}
function announceAgent(previous,next){
 const blocks=winningColumns(previous.board,1);
 const kind=next.winner_id==="p2"?"win":blocks.includes(next.agent_column)?"block":
  winningColumns(next.board,2).length>=2?"trap":"move";
 lastAgentEvent=kind;
 sayAgent(kind);
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
 const previous=state;
 const response=await post("/arena/connect4/agent-move",{agent_key:key,difficulty,request_id:req()});
 applyState(response);
 announceAgent(previous,response);
 q("[data-retry-agent]").hidden=true;
 render();
}
async function action(path,payload,followAgent=false){
 if(busy)return;busy=true;q("[data-error]").textContent="";render();
 try{
  if(path==="/arena/connect4/start"){lastQuip="";lastMove=null;lastAgentEvent="";banterCount=0;seenQuips.clear();q("[data-agent-banter]").replaceChildren();}
  applyState(await post(path,payload));
  render();
  if(path==="/arena/connect4/start" && agentMode)sayAgent("intro");
  if(path==="/arena/connect4/drop" && agentMode && state.status==="completed" && state.winner_id==="p1")sayAgent("loss");
  if(path==="/arena/connect4/drop" && agentMode && state.status==="completed" && state.result==="draw_full_board")sayAgent("draw");
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
function updateAgentLevels(){
 const key=q("[data-agent]").value;
 const select=q("[data-difficulty]");
 const previous=select.value;
 let choices=[["Easy","easy"],["Standard","standard"],["Strong","strong"],["A7","a7"]];
 if(key==="fox")choices=[["Cheeky Fox","easy"],["Sly Fox","strong"],["Fox No Mercy","a7"]];
 if(key==="tiger")choices=[["Tiger Cub","easy"],["Royal Roar","strong"],["Jungle Tyrant","a7"]];
 select.replaceChildren();
 for(const [label,value] of choices){
  const option=document.createElement("option");option.value=value;option.textContent=label;select.append(option);
 }
 select.value=choices.some(([,value])=>value===previous)?previous:choices[1][1];
}
q("[data-agent]").onchange=()=>{updateAgentLevels();const p=personalities[q("[data-agent]").value];q("[data-agent-persona]").textContent=p?.tone||"";};
q("[data-agent-persona]").textContent=(personalities[q("[data-agent]").value]||personalities.panther).tone;
q("[data-agent-talk]").onclick=()=>{if(!agentMode||!state)return;sayAgent("talk");};

updateAgentLevels();
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
