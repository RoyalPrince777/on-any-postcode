(()=>{
"use strict";
const root=document.querySelector("[data-ludo-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false;
const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(url,payload){const r=await fetch(url,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const result=await r.json();if(!r.ok)throw new Error(result?.error?.code||"arena_request_failed");return result;}
const track=[];const add=(r,c)=>{if(!track.some(p=>p[0]===r&&p[1]===c))track.push([r,c]);};
for(let c=1;c<=5;c++)add(6,c);
for(let r=5;r>=0;r--)add(r,6);
add(0,7);
for(let r=0;r<=5;r++)add(r,8);
for(let c=9;c<=14;c++)add(6,c);
add(7,14);
for(let c=14;c>=9;c--)add(8,c);
for(let r=9;r<=14;r++)add(r,8);
add(14,7);
for(let r=14;r>=9;r--)add(r,6);
for(let c=5;c>=0;c--)add(8,c);
add(7,0);add(6,0);
if(track.length!==52)throw Error("ludo_board_track_invalid");
const homes=[
 Array.from({length:6},(_,i)=>[7,i+1]),
 Array.from({length:6},(_,i)=>[i+1,7]),
 Array.from({length:6},(_,i)=>[7,13-i]),
 Array.from({length:6},(_,i)=>[13-i,7])
];
const corners=[[0,0],[0,9],[9,9],[9,0]];
const colours=["red","blue","yellow","green"];
const safe=new Set([0,8,13,21,26,34,39,47]);
const at=(r,c)=>q('[data-cell="'+r+'-'+c+'"]');
function boardBase(){
 const board=q("[data-board]");board.replaceChildren();
 for(let r=0;r<15;r++)for(let c=0;c<15;c++){
  const cell=document.createElement("div");cell.className="ludo-cell";cell.dataset.cell=r+"-"+c;
  const corner=corners.findIndex(([rr,cc])=>r>=rr&&r<rr+6&&c>=cc&&c<cc+6);
  if(corner!==-1)cell.classList.add("ludo-yard","ludo-"+colours[corner]);
  else if(r>=6&&r<=8&&c>=6&&c<=8)cell.classList.add("ludo-centre");
  else cell.classList.add("ludo-neutral");
  const ring=track.findIndex(p=>p[0]===r&&p[1]===c);
  if(ring!==-1){cell.classList.add("ludo-track");if(safe.has(ring)){cell.classList.add("ludo-safe");cell.textContent="★";}if([0,13,26,39].includes(ring))cell.classList.add("ludo-entry","ludo-"+colours[[0,13,26,39].indexOf(ring)]);}
  homes.forEach((lane,i)=>{if(lane.some(p=>p[0]===r&&p[1]===c))cell.classList.add("ludo-home","ludo-"+colours[i]);});
  board.append(cell);
 }
 at(7,7).textContent="OAP";
}
function pieceLabel(piece){if(piece.zone==="yard")return "Yard";if(piece.zone==="track")return "Track "+(piece.track_square+1);if(piece.zone==="home")return "Home "+piece.home_step;return "Finished";}
function position(piece,index,slot){
 if(piece.zone==="yard"){const [r,c]=corners[index];const places=[[2,2],[2,3],[3,2],[3,3]];return [r+places[slot][0],c+places[slot][1]];}
 if(piece.zone==="track")return track[piece.track_square];
 if(piece.zone==="home")return homes[index][piece.home_step-1];
 return [7,7];
}
function render(){
 if(!state)return;
 const active=state.status==="active",pending=state.pending_roll!==null;
 q("[data-game]").hidden=false;
 q("[data-turn]").textContent=active?state.current_player_name:"—";
 q("[data-roll-value]").textContent=pending?state.pending_roll:"—";
 q("[data-die-face]").textContent=pending?["⚀","⚁","⚂","⚃","⚄","⚅"][state.pending_roll-1]:"🎲";
 q("[data-status]").textContent=state.status==="completed"?"Finished":state.status;
 q("[data-sixes]").textContent=state.consecutive_sixes??0;
 q("[data-start]").disabled=busy||active;
 q("[data-players]").disabled=busy||active;
 q("[data-roll]").disabled=busy||!active||pending;
 q("[data-stop]").disabled=busy||!active;
 boardBase();
 const view=q("[data-players-view]");view.replaceChildren();
 state.players.forEach((player,index)=>{
  const row=document.createElement("section");row.className="arena-race-row ludo-player";
  const title=document.createElement("strong");title.textContent=player.name+" · "+player.finished+"/4 finished";title.className="ludo-"+colours[index];
  const pieces=document.createElement("div");pieces.className="arena-actions";pieces.setAttribute("role","group");pieces.setAttribute("aria-label",player.name+" pieces");
  player.pieces.forEach((piece,slot)=>{
   const selectable=active&&player.id===state.current_player_id&&state.movable_piece_ids.includes(piece.id)&&pending;
   const label=player.name+" piece "+(slot+1)+": "+pieceLabel(piece);
   const btn=document.createElement("button");btn.type="button";btn.dataset.piece=piece.id;
   btn.className="ludo-token ludo-"+colours[index]+(selectable?" ludo-legal":"");
   btn.textContent=String(slot+1);btn.setAttribute("aria-label",label);btn.title=label;btn.disabled=busy||!selectable;
   const [r,c]=position(piece,index,slot);at(r,c).append(btn);
   const detail=document.createElement("span");detail.textContent=(slot+1)+" · "+pieceLabel(piece);pieces.append(detail);
  });
  row.append(title,pieces);view.append(row);
 });
 const feedback=q("[data-feedback]");
 if(state.status==="completed")feedback.textContent="Winner: "+(state.winner_name||"—")+" · All four pieces home";
 else if(state.status==="stopped")feedback.textContent="Match stopped.";
 else if(pending&&state.movable_piece_ids.length)feedback.textContent="Rolled "+state.pending_roll+". Tap a glowing piece on the board.";
 else if(pending)feedback.textContent="Rolled "+state.pending_roll+".";
 else feedback.textContent="Tap the die. Only legal pieces can move.";
}
async function action(path,payload){
 if(busy||(path==="/arena/ludo/start"&&state?.status==="active"))return;
 busy=true;q("[data-error]").textContent="";q("[data-start]").disabled=true;
 try{state=await post(path,payload);render();}catch(e){error(e);}
 finally{busy=false;if(state)render();else q("[data-start]").disabled=false;}
}
q("[data-start]").onclick=()=>action("/arena/ludo/start",{players:q("[data-players]").value.split(",").map(x=>x.trim()).filter(Boolean)});
q("[data-roll]").onclick=()=>action("/arena/ludo/roll",{request_id:requestId()});
root.addEventListener("click",e=>{const btn=e.target.closest("[data-piece]");if(btn&&!btn.disabled)action("/arena/ludo/move",{piece_id:btn.dataset.piece,request_id:requestId()});});
q("[data-stop]").onclick=()=>action("/arena/ludo/stop",{request_id:requestId()});
boardBase();
})();