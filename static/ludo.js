(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s),qa=s=>[...root.querySelectorAll(s)];
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
function fitScreen(){
 const vv=window.visualViewport,w=Math.max(1,Math.round(vv?.width||window.innerWidth)),h=Math.max(1,Math.round(vv?.height||window.innerHeight));
 const board=Math.max(280,Math.min(w,h));
 const portrait=h>=w,compact=Math.min(w,h)<430;
 const style=document.documentElement.style;
 style.setProperty("--screen-w",w+"px");style.setProperty("--screen-h",h+"px");style.setProperty("--board-size",board+"px");
 style.setProperty("--board-left",portrait?Math.round((w-board)/2)+"px":"0px");
 style.setProperty("--board-top",portrait?Math.round((h-board)/2)+"px":"0px");
 root.classList.toggle("screen-portrait",portrait);root.classList.toggle("screen-landscape",!portrait);root.classList.toggle("screen-compact",compact);
 requestAnimationFrame(()=>renderBoard());
}
window.addEventListener("resize",fitScreen,{passive:true});
window.addEventListener("orientationchange",()=>setTimeout(fitScreen,120),{passive:true});
document.addEventListener("fullscreenchange",()=>setTimeout(fitScreen,80));
window.visualViewport?.addEventListener("resize",fitScreen,{passive:true});
window.visualViewport?.addEventListener("scroll",fitScreen,{passive:true});
let state=null,busy=false,agentIds=new Set(),agentDifficulty="sharp",agentTimer=null,lastSetup=null;
const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>{const n=q("[data-error]");if(n)n.textContent=e?.message||String(e)};
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}

const TRACK=[
[6,1],[6,2],[6,3],[6,4],[6,5],[5,6],[4,6],[3,6],[2,6],[1,6],[0,6],[0,7],[0,8],
[1,8],[2,8],[3,8],[4,8],[5,8],[6,9],[6,10],[6,11],[6,12],[6,13],[6,14],[7,14],[8,14],
[8,13],[8,12],[8,11],[8,10],[8,9],[9,8],[10,8],[11,8],[12,8],[13,8],[14,8],[14,7],[14,6],
[13,6],[12,6],[11,6],[10,6],[9,6],[8,5],[8,4],[8,3],[8,2],[8,1],[8,0],[7,0],[6,0]
];
const HOME_LANES={
green:[[7,1],[7,2],[7,3],[7,4],[7,5],[7,6]],
red:[[1,7],[2,7],[3,7],[4,7],[5,7],[6,7]],
blue:[[13,7],[12,7],[11,7],[10,7],[9,7],[8,7]],
yellow:[[7,13],[7,12],[7,11],[7,10],[7,9],[7,8]]
};
const OFFSETS=[0,13,26,39],COLORS=["green","red","yellow","blue"];

function settings(){return {
 mode:q("[data-mode]")?.value||"1a",
 difficulty:q("[data-difficulty]")?.value||"sharp",
 speed:q("[data-speed]")?.value||"normal",
 sound:!!q("[data-sound]")?.checked,
 haptics:!!q("[data-haptics]")?.checked
}}
function delayMs(){const s=settings().speed;return s==="fast"?350:s==="slow"?1100:650}
function feedbackPulse(){if(settings().haptics&&navigator.vibrate)navigator.vibrate(35);if(settings().sound){try{const C=window.AudioContext||window.webkitAudioContext;if(!C)return;const a=new C(),o=a.createOscillator(),g=a.createGain();o.frequency.value=520;g.gain.value=.035;o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+.06);setTimeout(()=>a.close(),120)}catch{}}}

function buildBoard(){
 const board=q("[data-visual-board]");if(!board||board.dataset.ready)return;board.dataset.ready="1";
 for(let r=0;r<15;r++)for(let c=0;c<15;c++){const cell=document.createElement("div");cell.className="ludo-cell";cell.dataset.rc=r+","+c;if(TRACK.some(p=>p[0]===r&&p[1]===c))cell.classList.add("track");for(const [color,lane] of Object.entries(HOME_LANES))if(lane.some(p=>p[0]===r&&p[1]===c))cell.classList.add(color+"-lane");if([[6,1],[1,8],[8,13],[13,6],[2,6],[6,12],[12,8],[8,2]].some(p=>p[0]===r&&p[1]===c))cell.classList.add("safe");board.append(cell)}
 for(const color of COLORS){const zone=document.createElement("div");zone.className="home-zone "+color;const yard=document.createElement("div");yard.className="yard";for(let i=0;i<4;i++){const s=document.createElement("div");s.className="yard-slot";s.dataset.yard=color+"-"+i;yard.append(s)}zone.append(yard);board.append(zone)}
 const home=document.createElement("div");home.className="center-home";home.innerHTML="<span>OAP ARENA</span>";board.append(home)
}
function cellCenter([r,c]){return{left:((c+.5)/15)*100,top:((r+.5)/15)*100}}
function piecePoint(pi,piece){
 const color=COLORS[pi];
 if(piece.zone==="yard"){const yardIndex=Math.max(0,Number(piece.id.split("-").at(-1))-1),slot=q('[data-yard="'+color+'-'+yardIndex+'"]');if(slot){const b=q("[data-visual-board]").getBoundingClientRect(),s=slot.getBoundingClientRect();return{left:((s.left+s.width/2-b.left)/b.width)*100,top:((s.top+s.height/2-b.top)/b.height)*100}}}
 if(piece.zone==="track")return cellCenter(TRACK[(piece.track_square??0)%52]);
 if(piece.zone==="home"){const step=Math.max(0,Math.min(5,(piece.home_step??1)-1));return cellCenter(HOME_LANES[color][step])}
 return{left:50,top:50}
}
function isAgentTurn(){return !!state&&agentIds.has(state.current_player_id)&&state.status==="active"}
function renderBoard(){
 buildBoard();const board=q("[data-visual-board]");board.querySelectorAll(".board-piece").forEach(x=>x.remove());if(!state)return;
 state.players.forEach((player,pi)=>player.pieces.forEach(piece=>{const el=document.createElement("button");el.type="button";el.className="board-piece "+COLORS[pi];const p=piecePoint(pi,piece);el.style.left=p.left+"%";el.style.top=p.top+"%";el.dataset.piece=piece.id;el.setAttribute("aria-label",player.name+" "+piece.id);const selectable=state.status==="active"&&!isAgentTurn()&&player.id===state.current_player_id&&state.movable_piece_ids.includes(piece.id)&&state.pending_roll!==null;el.disabled=!selectable||busy;if(selectable)el.classList.add("selectable");board.append(el)}))
}
function pieceLabel(piece){if(piece.zone==="yard")return"Yard";if(piece.zone==="track")return"Track "+((piece.track_square??0)+1);if(piece.zone==="home")return"Home "+piece.home_step;return"Finished"}
function showResults(){
 const r=q("[data-results]");if(!r)return;const done=state?.status==="completed";r.hidden=!done;r.style.display=done?"grid":"none";if(done){const t=q("[data-result-title]");if(t)t.textContent="👑 "+(state.winner_name||"Arena Winner")}
}
function render(){
 renderBoard();if(!state)return;
 q("[data-game]").hidden=false;
 const movePanel=q("[data-move-panel]");if(movePanel)movePanel.classList.toggle("active",!isAgentTurn()&&state.status==="active"&&state.pending_roll!==null&&state.movable_piece_ids.length>0);
 q("[data-turn]").textContent=state.status==="active"?(isAgentTurn()?"🤖 "+state.current_player_name:state.current_player_name):"—";
 q("[data-roll-value]").textContent=state.pending_roll??"🎲";q("[data-status]").textContent=state.status==="completed"?"Complete":state.status;
 const view=q("[data-players-view]");view.replaceChildren();
 for(const player of state.players){const row=document.createElement("section");row.className="player-entry";const left=document.createElement("div"),title=document.createElement("strong"),meta=document.createElement("span");title.textContent=(agentIds.has(player.id)?"🤖 ":"")+player.name;meta.textContent=player.finished+"/4 home";left.append(title,meta);const pieces=document.createElement("div");pieces.style.display="grid";pieces.style.gap="6px";for(const piece of player.pieces){const legal=!isAgentTurn()&&state.status==="active"&&player.id===state.current_player_id&&state.pending_roll!==null&&state.movable_piece_ids.includes(piece.id);const b=document.createElement("button");b.type="button";b.dataset.piece=piece.id;b.textContent=(legal?"MOVE · ":"")+pieceLabel(piece);b.disabled=!legal||busy;if(legal){b.className="arena-primary";b.style.minHeight="42px"}pieces.append(b)}row.append(left,pieces);view.append(row)}
 const active=state.status==="active",pending=state.pending_roll!==null,roll=q("[data-roll]");
 q("[data-start]").disabled=busy||active;q("[data-players]").disabled=busy||active;if(roll)roll.disabled=busy||!active||pending||isAgentTurn();q("[data-stop]").disabled=busy||!active;
 const feedback=q("[data-feedback]");
 if(state.status==="completed")feedback.textContent="👑 Arena Winner: "+(state.winner_name||"—");
 else if(state.status==="stopped")feedback.textContent="Match stopped.";
 else if(isAgentTurn())feedback.textContent="🤖 "+state.current_player_name+" is thinking…";
 else if(pending&&state.movable_piece_ids.length)feedback.textContent="🎯 Rolled "+state.pending_roll+" · tap a glowing piece.";
 else if(pending)feedback.textContent="Rolled "+state.pending_roll+".";
 else feedback.textContent="Tap the dice. You need a 6 to bring a piece out.";
 showResults();scheduleAgent()
}
async function action(path,payload,{silent=false}={}){
 if(busy||(path==="/arena/ludo/start"&&state?.status==="active"))return;busy=true;error("");try{state=await post(path,payload);if(!silent)feedbackPulse();render();if(path==="/arena/ludo/start"){const dlg=q("[data-settings]");if(dlg?.open)dlg.close()}}catch(e){error(e)}finally{busy=false;render()}
}
function setupRoster(){
 const s=settings(),raw=q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean),names=[];
 agentDifficulty=s.difficulty;
 if(s.mode==="1a"){names.push(raw[0]||"Player One","Arena Agent")}
 else if(s.mode==="2a"){names.push(raw[0]||"Player One",raw[1]||"Player Two","Arena Agent Alpha","Arena Agent Beta")}
 else{for(let i=0;i<4;i++)names.push(raw[i]||"Player "+(i+1))}
 lastSetup={...s,names};return names
}
async function startGame(){
 if(document.fullscreenEnabled&&!document.fullscreenElement){try{await document.documentElement.requestFullscreen()}catch{}}
 const names=setupRoster();await action("/arena/ludo/start",{players:names},{silent:true});
 agentIds=new Set();
 if(state){if(lastSetup.mode==="1a")agentIds.add(state.players[1]?.id);if(lastSetup.mode==="2a"){agentIds.add(state.players[2]?.id);agentIds.add(state.players[3]?.id)}}
 render()
}
function scoreMove(piece){
 const roll=state.pending_roll||0,pi=state.players.findIndex(p=>p.id===state.current_player_id),safe=new Set(state.safe_track_squares||[]);
 if(agentDifficulty==="easy")return Math.random()*100;
 const nextProgress=piece.progress<0?0:piece.progress+roll;
 let score=nextProgress*1.3;
 if(piece.zone==="yard"&&roll===6)score+=22;
 if(nextProgress>=58)score+=180;
 if(nextProgress>=52)score+=55+(nextProgress-52)*10;
 if(nextProgress<52){
   const landing=(OFFSETS[pi]+nextProgress)%52;
   if(safe.has(landing))score+=24;
   for(const opponent of state.players.filter(p=>p.id!==state.current_player_id))for(const target of opponent.pieces)if(target.zone==="track"&&target.track_square===landing&&!safe.has(landing))score+=75;
   const mates=state.players[pi].pieces.filter(p=>p.id!==piece.id&&p.zone==="track"&&p.track_square===landing).length;if(mates)score+=18*mates;
   if(agentDifficulty==="ruthless"){
     for(const opponent of state.players.filter(p=>p.id!==state.current_player_id))for(const target of opponent.pieces)if(target.zone==="track"){const d=(landing-target.track_square+52)%52;if(d>=1&&d<=6&&!safe.has(landing))score-=34-(d*3)}
     score+=Math.min(35,nextProgress*.45)
   }
 }
 if(agentDifficulty==="sharp")score+=Math.random()*8;
 return score
}
function chooseAgentPiece(){
 const player=state.players.find(p=>p.id===state.current_player_id);if(!player)return null;
 const legal=player.pieces.filter(p=>state.movable_piece_ids.includes(p.id));if(!legal.length)return null;
 return [...legal].sort((a,b)=>scoreMove(b)-scoreMove(a))[0]
}
function scheduleAgent(){
 clearTimeout(agentTimer);if(!isAgentTurn()||busy)return;
 agentTimer=setTimeout(async()=>{
   if(!isAgentTurn()||busy)return;
   if(state.pending_roll===null){
     const die=q("[data-roll]");if(die){die.classList.remove("rolling");void die.offsetWidth;die.classList.add("rolling");setTimeout(()=>die.classList.remove("rolling"),620)}
     await action("/arena/ludo/roll",{request_id:requestId()},{silent:true});return
   }
   const piece=chooseAgentPiece();if(piece)await action("/arena/ludo/move",{piece_id:piece.id,request_id:requestId()},{silent:true})
 },delayMs())
}

q("[data-start]").onclick=startGame;
const roll=q("[data-roll]");
async function rollHuman(){
 if(!roll||isAgentTurn()||busy)return;
 roll.classList.remove("rolling"); void roll.offsetWidth; roll.classList.add("rolling");
 const faces=["⚀","⚁","⚂","⚃","⚄","⚅"]; let ticks=0;
 const spin=setInterval(()=>{roll.textContent=faces[ticks++%faces.length]},70);
 try{await action("/arena/ludo/roll",{request_id:requestId()})}
 finally{clearInterval(spin);setTimeout(()=>roll.classList.remove("rolling"),80)}
}
if(roll)roll.onclick=rollHuman;
root.addEventListener("click",e=>{const btn=e.target.closest("[data-piece]");if(btn&&!btn.disabled&&!isAgentTurn())action("/arena/ludo/move",{piece_id:btn.dataset.piece,request_id:requestId()})});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
q("[data-rematch]")?.addEventListener("click",()=>{state=null;agentIds.clear();q("[data-results]").hidden=true;q("[data-results]").style.display="none";const dlg=q("[data-settings]");if(dlg&&!dlg.open)dlg.showModal()});
qa("[data-fullscreen]").forEach(b=>b.addEventListener("click",async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch{}}));
buildBoard();fitScreen();renderBoard();
})();