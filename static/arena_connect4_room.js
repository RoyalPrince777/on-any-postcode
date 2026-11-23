(()=>{
"use strict";
const root=document.querySelector("[data-room-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
const controls=q("[data-controls]");
const renderBoard=window.OAPConnect4Board.mount(root);
const colours=["empty","yellow","purple"];
const emptyBoard=Array.from({length:6},()=>Array(7).fill(0));
let membership=null;let snapshot=null;let busy=false;let entryBusy=false;let needsRefresh=false;let refreshInFlight=null;
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
 const me=snapshot.players.find(p=>p.seat===membership.seat);
 q("[data-players]").textContent=snapshot.players.map(p=>p.display_name+" (P"+p.seat+")").join(" vs ");
 const game=snapshot.game_state||{};
 const myTurn=snapshot.status==="ACTIVE" &&
  (!game.started || game.current_player_id==="p"+membership.seat) &&
  (game.started || membership.seat===1);
 const turn=game.status==="completed"
 ?(game.winner_id?"Winner: "+snapshot.players.find(p=>"p"+p.seat===game.winner_id)?.display_name:"Draw")
 :(game.status==="stopped"?"Match stopped":myTurn?"Your turn":snapshot.status==="WAITING"?"Waiting for another player":"Other player's turn");
 q("[data-turn]").textContent=(me?"Playing as "+me.display_name+" · ":"")+turn;
 controls.hidden=snapshot.status!=="ACTIVE";
 renderBoard(game.board||emptyBoard,colours,busy||needsRefresh||!myTurn);
 q("[data-stop]").disabled=busy||needsRefresh||snapshot.status!=="ACTIVE";
}
async function refresh(){
 if(!membership)return;
 if(refreshInFlight)return refreshInFlight;
 const current=membership;
 refreshInFlight=(async()=>{
  const next=await post("/arena/rooms/state",{
   room_id:current.room_id,reconnect_token:current.reconnect_token,
  });
  if(membership!==current)return;
  if(next.game_key!=="connect4")throw new Error("arena_room_game_invalid");
  snapshot=next;membership.seat=next.your_seat;needsRefresh=false;render();
 })();
 try{await refreshInFlight;}finally{refreshInFlight=null;}
}
function lockEntry(locked){
 entryBusy=locked;
 for(const key of ["[data-matchmake]","[data-create]","[data-join]","[data-reconnect]"])
  q(key).disabled=locked;
}
async function enter(task){
 if(entryBusy||busy)return;
 lockEntry(true);clear();
 try{await task();}catch(e){error(e);}
 finally{lockEntry(false);}
}
async function action(action,column){
 if(busy||needsRefresh||!membership||!snapshot)return;
 busy=true;render();clear();
 try{
  const data=await post("/arena/rooms/connect4/action",{
   ...membership,expected_revision:snapshot.revision,request_id:req(),action,column,
  });
  message(data.duplicate?"Action already recorded":"Action recorded");
  await refresh();
 }catch(e){
  error(e);needsRefresh=true;
  message("Move outcome requires server read-back. Refresh before another action.");
  try{await refresh();if(e.message==="arena_room_revision_conflict")message("Match refreshed after another move.");}
  catch(refreshError){error(refreshError);}

 }finally{busy=false;render();}
}
q("[data-matchmake]").onclick=()=>enter(async()=>{const d=await post("/arena/rooms/matchmake",{game_key:"connect4",display_name:q("[data-host]").value.trim()});identity(d,d.seat);await refresh();});
q("[data-create]").onclick=()=>enter(async()=>{
 const host=q("[data-host]").value.trim();
 const result=await post("/arena/rooms/create",{game_key:"connect4",capacity:2,host_name:host});
 identity(result,1);
 message("Room created. Keep your reconnect token private; share only the code.");
 await refresh();
});
q("[data-join]").onclick=()=>enter(async()=>{
 const result=await post("/arena/rooms/join",{
  room_code:q("[data-join-code]").value.trim().toUpperCase(),
  display_name:q("[data-guest]").value.trim(),
 });
 identity(result,result.seat);
 message("Room joined. Keep your reconnect token private.");
 await refresh();
});
q("[data-reconnect]").onclick=()=>enter(async()=>{
 const room_id=q("[data-reconnect-id]").value.trim();
 const reconnect_token=q("[data-reconnect-token]").value.trim();
 if(!room_id||!reconnect_token)throw new Error("Room ID and private token are required.");
 const previous=membership;
 membership={room_id,reconnect_token,seat:0};
 try{
  await refresh();
  if(!snapshot.players.some(p=>p.seat===membership.seat))throw new Error("arena_room_seat_invalid");
  q("[data-entry]").hidden=true;q("[data-room]").hidden=false;
  q("[data-id]").textContent=room_id;q("[data-token]").textContent=reconnect_token;
  message("Reconnected.");
 }catch(e){membership=previous;snapshot=null;throw e;}
});
q("[data-refresh]").onclick=async()=>{
 if(busy||entryBusy)return;
 clear();q("[data-refresh]").disabled=true;
 try{await refresh();message("Current server state loaded.");}
 catch(e){needsRefresh=true;error(e);message("Could not confirm the current board. Retry Refresh before moving.");}
 finally{q("[data-refresh]").disabled=false;render();}
};
controls.onclick=e=>{
 const target=e.target.closest("[data-column]");if(!target||target.getAttribute("aria-disabled")==="true")return;
 action("drop",Number(target.dataset.column));
};
q("[data-stop]").onclick=()=>action("stop",null);
})();
