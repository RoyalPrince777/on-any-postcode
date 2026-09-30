(()=>{
"use strict";
const root=document.querySelector("[data-room-root]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let membership=null;let snapshot=null;let busy=false;
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
 const board=game.board||Array.from({length:6},()=>Array(7).fill(0));
 const myTurn=snapshot.status==="ACTIVE" &&
  (!game.started || game.current_player_id==="p"+membership.seat) &&
  (game.started || membership.seat===1);
 const turn=game.status==="completed"
 ?(game.winner_id?"Winner: "+snapshot.players.find(p=>"p"+p.seat===game.winner_id)?.display_name:"Draw")
 :(game.status==="stopped"?"Match stopped":myTurn?"Your turn":snapshot.status==="WAITING"?"Waiting for another player":"Other player's turn");
 q("[data-turn]").textContent=(me?"Playing as "+me.display_name+" · ":"")+turn;
 const columns=q("[data-columns]");columns.replaceChildren();
 for(let i=0;i<7;i++){
  const btn=document.createElement("button");btn.type="button";btn.textContent="↓";
  btn.setAttribute("aria-label","Drop into column "+(i+1));btn.dataset.column=String(i);
  btn.disabled=busy||!myTurn||board[0][i]!==0;
  columns.append(btn);
 }
 const cells=q("[data-board]");cells.replaceChildren();
 board.flat().forEach(value=>{
  const cell=document.createElement("div");cell.className="room-cell"+(value===1?" room-p1":value===2?" room-p2":"");
  cells.append(cell);
 });
 q("[data-stop]").disabled=busy||snapshot.status!=="ACTIVE";
}
async function refresh(){
 if(!membership)return;
 snapshot=await post("/arena/rooms/state",{
  room_id:membership.room_id,reconnect_token:membership.reconnect_token,
 });
 membership.seat=snapshot.your_seat;
 render();
}
async function action(action,column){
 if(busy||!membership||!snapshot)return;
 busy=true;render();clear();
 try{
  const data=await post("/arena/rooms/connect4/action",{
   ...membership,expected_revision:snapshot.revision,request_id:req(),action,column,
  });
  message(data.duplicate?"Action already recorded":"Action recorded");
  await refresh();
 }catch(e){
  error(e);if(e.message==="arena_room_revision_conflict")try{await refresh();message("Match refreshed after another move.");}catch(refreshError){error(refreshError);}
 }finally{busy=false;render();}
}
q("[data-create]").onclick=async()=>{
 clear();try{
  const host=q("[data-host]").value.trim();
  const result=await post("/arena/rooms/create",{game_key:"connect4",capacity:2,host_name:host});
  identity(result,1);await refresh();message("Room created. Share only the room code.");
 }catch(e){error(e);}
};
q("[data-join]").onclick=async()=>{
 clear();try{
  const result=await post("/arena/rooms/join",{
   room_code:q("[data-join-code]").value.trim().toUpperCase(),display_name:q("[data-guest]").value.trim(),
  });
  identity(result,result.seat);await refresh();message("Joined the room.");
 }catch(e){error(e);}
};
q("[data-reconnect]").onclick=async()=>{
 clear();
 const room_id=q("[data-reconnect-id]").value.trim();
 const reconnect_token=q("[data-reconnect-token]").value.trim();
 if(!room_id||!reconnect_token){error(new Error("Room ID and private token are required."));return;}
 membership={room_id,reconnect_token,seat:0};
 try{
  await refresh();
  if(!snapshot.players.some(p=>p.seat===membership.seat))throw new Error("arena_room_seat_invalid");
  q("[data-entry]").hidden=true;q("[data-room]").hidden=false;
  q("[data-id]").textContent=room_id;q("[data-token]").textContent=reconnect_token;
  message("Reconnected.");
 }catch(e){membership=null;snapshot=null;error(e);}
};
q("[data-refresh]").onclick=async()=>{clear();try{await refresh();message("Current server state loaded.");}catch(e){error(e);}};
q("[data-columns]").onclick=e=>{
 const target=e.target.closest("[data-column]");if(!target||target.disabled)return;
 action("drop",Number(target.dataset.column));
};
q("[data-stop]").onclick=()=>action("stop",null);
})();
