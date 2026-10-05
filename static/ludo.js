(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s);const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}

const COLORS={green:"#19aa53",red:"#e24449",yellow:"#f3ca24",blue:"#3694eb"};
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
const START_INDEX={green:0,red:13,yellow:26,blue:39};

function buildBoard(){
 const board=q("[data-visual-board]"); if(!board||board.dataset.ready)return;
 board.dataset.ready="1";
 for(let r=0;r<15;r++)for(let c=0;c<15;c++){
   const cell=document.createElement("div"); cell.className="ludo-cell"; cell.dataset.rc=r+","+c;
   if(TRACK.some(p=>p[0]===r&&p[1]===c))cell.classList.add("track");
   for(const [color,lane] of Object.entries(HOME_LANES))if(lane.some(p=>p[0]===r&&p[1]===c))cell.classList.add(color+"-lane");
   if([[6,1],[1,8],[8,13],[13,6],[2,6],[6,12],[12,8],[8,2]].some(p=>p[0]===r&&p[1]===c))cell.classList.add("safe");
   board.append(cell);
 }
 for(const color of ["green","red","yellow","blue"]){
   const zone=document.createElement("div");zone.className="home-zone "+color;
   const yard=document.createElement("div");yard.className="yard";
   for(let i=0;i<4;i++){const s=document.createElement("div");s.className="yard-slot";s.dataset.yard=color+"-"+i;yard.append(s)}
   zone.append(yard);board.append(zone);
 }
 const home=document.createElement("div");home.className="center-home";home.innerHTML="<span>OAP ARENA</span>";board.append(home);
}
function cellCenter(rc){
 const [r,c]=rc; return {left:((c+.5)/15)*100,top:((r+.5)/15)*100};
}
function piecePoint(playerIndex,piece){
 const color=["green","red","yellow","blue"][playerIndex];
 if(piece.zone==="yard"){
   const yardIndex=Math.max(0,Number(piece.id.split("-").at(-1))-1); const slot=q('[data-yard="'+color+'-'+yardIndex+'"]');
   if(slot){const b=q("[data-visual-board]").getBoundingClientRect(),s=slot.getBoundingClientRect();return {left:((s.left+s.width/2-b.left)/b.width)*100,top:((s.top+s.height/2-b.top)/b.height)*100}}
 }
 if(piece.zone==="track"){
   const idx=piece.track_square??0; return cellCenter(TRACK[idx%52]);
 }
 if(piece.zone==="home"){
   const step=Math.max(0,Math.min(5,(piece.home_step??1)-1)); return cellCenter(HOME_LANES[color][step]);
 }
 return {left:50,top:50};
}
function renderBoard(){
 buildBoard();
 const board=q("[data-visual-board]"); board.querySelectorAll(".board-piece").forEach(x=>x.remove());
 if(!state)return;
 state.players.forEach((player,pi)=>{
   player.pieces.forEach(piece=>{
     const el=document.createElement("button");el.type="button";el.className="board-piece "+["green","red","yellow","blue"][pi];
     const p=piecePoint(pi,piece);el.style.left=p.left+"%";el.style.top=p.top+"%";el.dataset.piece=piece.id;
     el.setAttribute("aria-label",player.name+" "+piece.id);
     const selectable=state.status==="active"&&player.id===state.current_player_id&&state.movable_piece_ids.includes(piece.id)&&state.pending_roll!==null;
     el.disabled=!selectable||busy;if(selectable)el.classList.add("selectable");
     board.append(el);
   });
 });
}
function pieceLabel(piece){if(piece.zone==="yard")return "Yard";if(piece.zone==="track")return "Track "+((piece.track_square??0)+1);if(piece.zone==="home")return "Home "+piece.home_step;return "Finished";}
function render(){
 renderBoard();
 if(!state)return;
 q("[data-game]").hidden=false;q("[data-turn]").textContent=state.status==="active"?state.current_player_name:"—";
 q("[data-roll-value]").textContent=state.pending_roll??"⚄";q("[data-status]").textContent=state.status==="completed"?"Complete":state.status;
 const view=q("[data-players-view]");view.replaceChildren();
 for(const player of state.players){
  const row=document.createElement("section");row.className="player-entry";
  const left=document.createElement("div");const title=document.createElement("strong");title.textContent=player.name;
  const meta=document.createElement("span");meta.textContent=player.finished+"/4 home";
  left.append(title,meta);
  const pieces=document.createElement("div");pieces.style.display="grid";pieces.style.gap="6px";
  for(const piece of player.pieces){
    const legal=state.status==="active"&&player.id===state.current_player_id&&state.pending_roll!==null&&state.movable_piece_ids.includes(piece.id);
    const b=document.createElement("button");b.type="button";b.dataset.piece=piece.id;
    b.textContent=(legal?"MOVE · ":"")+pieceLabel(piece);b.disabled=!legal||busy;
    if(legal){b.className="arena-primary";b.style.minHeight="42px";}
    pieces.append(b);
  }
  row.append(left,pieces);view.append(row);
 }
 const active=state.status==="active",pending=state.pending_roll!==null;
 q("[data-start]").disabled=busy||active;q("[data-players]").disabled=busy||active;q("[data-roll]").disabled=busy||!active||pending;q("[data-stop]").disabled=busy||!active;
 const feedback=q("[data-feedback]");
 if(state.status==="completed"){feedback.textContent="👑 Arena Winner: "+(state.winner_name||state.players.find(p=>p.id===state.winner_id)?.name||"—");}
 else if(state.status==="stopped"){feedback.textContent="Match stopped.";}
 else if(pending&&state.movable_piece_ids.length){feedback.textContent="🎯 Rolled "+state.pending_roll+" · tap a glowing piece or a MOVE button.";}
 else if(pending){feedback.textContent="Rolled "+state.pending_roll+".";}
 else{feedback.textContent="Roll when it is your move. You need a 6 to bring a piece out of the yard.";}
}
async function action(path,payload){if(busy||(path==="/arena/ludo/start"&&state?.status==="active"))return;busy=true;q("[data-error]").textContent="";try{state=await post(path,payload);render();}catch(e){error(e);}finally{busy=false;render();}}
q("[data-start]").onclick=()=>action("/arena/ludo/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
q("[data-roll]").onclick=()=>action("/arena/ludo/roll",{request_id:requestId()});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-piece]");if(btn&&!btn.disabled)action("/arena/ludo/move",{piece_id:btn.dataset.piece,request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
buildBoard();renderBoard();
})();