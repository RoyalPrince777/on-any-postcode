(()=>{
"use strict";
const root=document.querySelector("[data-ludo-room]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let membership=null,snapshot=null,busy=false,entryBusy=false,needsRefresh=false,refreshInFlight=null;
const req=()=>crypto.randomUUID().replaceAll("-","").slice(0,20);
const message=s=>{q("[data-message]").textContent=s;};
const error=e=>{q("[data-error]").textContent=e?.message||String(e);};
const clear=()=>{q("[data-error]").textContent="";};
async function post(path,body){
 const res=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",
 headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(body)});
 const data=await res.json();
 if(!res.ok)throw new Error(data?.error?.code||"arena_room_request_failed");
 return data;
}
function identity(data,seat){
 membership={room_id:data.room_id,reconnect_token:data.reconnect_token,seat};
 q("[data-entry]").hidden=true;q("[data-room]").hidden=false;
 q("[data-id]").textContent=membership.room_id;q("[data-token]").textContent=membership.reconnect_token;
 q("[data-code]").textContent=data.room_code||"";
}
function render(){
 if(!membership||!snapshot)return;
 q("[data-code]").textContent=snapshot.room_code;
 q("[data-status]").textContent=snapshot.status;
 q("[data-revision]").textContent=String(snapshot.revision);
 const game=snapshot.game_state||{};
 const myTurn=snapshot.status==="ACTIVE"&&game.current_player_id==="p"+membership.seat;
 q("[data-roll-value]").textContent=game.pending_roll??"—";
 q("[data-turn]").textContent=snapshot.status==="WAITING"?"Waiting for another player":
  game.status==="completed"?"Winner: "+(game.winner_name||"confirmed"):
  game.status==="stopped"?"Match stopped":myTurn?"Your turn":"Other player's turn";
 q("[data-roll]").disabled=busy||needsRefresh||!myTurn||game.pending_roll!=null;
 q("[data-stop]").disabled=busy||needsRefresh||snapshot.status!=="ACTIVE";
 const players=q("[data-players]");players.replaceChildren();
 for(const player of game.players||[]){
  const card=document.createElement("section");card.className="ludo-player";
  const title=document.createElement("strong");title.textContent=player.name+" · "+player.finished+"/4 home";
  const pieces=document.createElement("div");pieces.className="ludo-pieces";
  for(const piece of player.pieces||[]){
   const btn=document.createElement("button");btn.type="button";btn.className="ludo-piece";
   btn.textContent=piece.id+" · "+piece.zone+(piece.track_square!=null?" "+piece.track_square:"");
   btn.dataset.piece=piece.id;
   btn.disabled=busy||needsRefresh||!myTurn||!(game.movable_piece_ids||[]).includes(piece.id);
   pieces.append(btn);
  }
  card.append(title,pieces);players.append(card);
 }
}
async function refresh(){
 if(!membership)return;
 if(refreshInFlight)return refreshInFlight;
 const current=membership;
 refreshInFlight=(async()=>{
  const next=await post("/arena/rooms/state",{room_id:current.room_id,reconnect_token:current.reconnect_token});
  if(membership!==current)return;
  if(next.game_key!=="ludo")throw new Error("arena_room_game_invalid");
  snapshot=next;membership.seat=next.your_seat;needsRefresh=false;render();
 })();
 try{await refreshInFlight;}finally{refreshInFlight=null;}
}
function lockEntry(locked){
 entryBusy=locked;
 for(const key of ["[data-create]","[data-join]","[data-reconnect]"])q(key).disabled=locked;
}
async function enter(task){
 if(entryBusy||busy)return;lockEntry(true);clear();
 try{await task();}catch(e){error(e);}finally{lockEntry(false);}
}
async function action(action,piece_id=null){
 if(busy||needsRefresh||!membership||!snapshot)return;
 busy=true;render();clear();
 try{
  const data=await post("/arena/rooms/ludo/action",{
   ...membership,expected_revision:snapshot.revision,request_id:req(),action,piece_id,
  });
  message(data.duplicate?"Action already recorded":"Action recorded");
  await refresh();
 }catch(e){
  error(e);needsRefresh=true;message("Action outcome requires server read-back. Refresh before another action.");
  try{await refresh();if(e.message==="arena_room_revision_conflict")message("Match refreshed after another action.");}
  catch(refreshError){error(refreshError);}
 }finally{busy=false;render();}
}
q("[data-create]").onclick=()=>enter(async()=>{
 const result=await post("/arena/rooms/create",{game_key:"ludo",capacity:2,host_name:q("[data-host]").value.trim()});
 identity(result,1);message("Room created. Share only the room code.");await refresh();
});
q("[data-join]").onclick=()=>enter(async()=>{
 const result=await post("/arena/rooms/join",{room_code:q("[data-join-code]").value.trim().toUpperCase(),display_name:q("[data-guest]").value.trim()});
 identity(result,result.seat);message("Room joined.");await refresh();
});
q("[data-reconnect]").onclick=()=>enter(async()=>{
 const room_id=q("[data-reconnect-id]").value.trim(),reconnect_token=q("[data-reconnect-token]").value.trim();
 if(!room_id||!reconnect_token)throw new Error("Room ID and private token are required.");
 const previous=membership;membership={room_id,reconnect_token,seat:0};
 try{await refresh();q("[data-entry]").hidden=true;q("[data-room]").hidden=false;q("[data-id]").textContent=room_id;q("[data-token]").textContent=reconnect_token;message("Reconnected.");}
 catch(e){membership=previous;snapshot=null;throw e;}
});
q("[data-refresh]").onclick=async()=>{
 if(busy||entryBusy)return;clear();q("[data-refresh]").disabled=true;
 try{await refresh();message("Current server state loaded.");}
 catch(e){needsRefresh=true;error(e);message("Could not confirm the current game. Retry Refresh before acting.");}
 finally{q("[data-refresh]").disabled=false;render();}
};
q("[data-roll]").onclick=()=>action("roll");
q("[data-players]").onclick=e=>{const target=e.target.closest("[data-piece]");if(!target||target.disabled)return;action("move",target.dataset.piece);};
q("[data-stop]").onclick=()=>action("stop");
})();