(()=>{
"use strict";const root=document.querySelector("[data-dot-room]");if(!root)return;
const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let me=null,state=null,busy=false,entryBusy=false,needsRefresh=false,refreshInFlight=null;
const rid=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);
const clear=()=>q("[data-error]").textContent="";
const note=s=>q("[data-message]").textContent=s;
async function post(path,payload){
 const res=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",
  headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});
 const data=await res.json();if(!res.ok)throw new Error(data?.error?.code||"dot_room_error");return data;
}
const edges=[];
for(let x=0;x<3;x++)for(let y=0;y<3;y++){
 if(x<2)edges.push([`${x},${y}`,`${x+1},${y}`]);
 if(y<2)edges.push([`${x},${y}`,`${x},${y+1}`]);
}
function showIdentity(data){
 me={room_id:data.room_id,reconnect_token:data.reconnect_token,seat:0};
 q("[data-entry]").hidden=true;q("[data-match]").hidden=false;
 q("[data-id]").textContent=me.room_id;q("[data-token]").textContent=me.reconnect_token;
}
function render(){
 if(!state||!me)return;
 q("[data-code]").textContent=state.room_code;
 q("[data-status]").textContent=state.status;
 q("[data-revision]").textContent=state.revision;
 q("[data-players]").textContent=state.players.map(p=>p.display_name+" (P"+p.seat+")").join(" vs ");
 const game=state.game_state||{},drawn=game.edges||[];
 const current=game.turn_player_id||(state.status==="ACTIVE"?"p1":null);
 const myTurn=state.status==="ACTIVE"&&current==="p"+me.seat;
 q("[data-turn]").textContent=game.status==="completed"?"Finished":game.status==="stopped"?"Stopped":state.status==="WAITING"?"Waiting for player two":myTurn?"Your turn":"Other player's turn";
 const scores=(game.players||[]).map(p=>p.name+": "+p.score).join(" · ");
 q("[data-boxes]").textContent=scores+" · Boxes: "+Object.keys(game.boxes||{}).length+"/4";
 q("[data-edges]").replaceChildren();
 for(const [a,b] of edges){
  const taken=drawn.some(e=>e[0]===a&&e[1]===b||e[0]===b&&e[1]===a);
  const button=document.createElement("button");button.type="button";
  button.dataset.a=a;button.dataset.b=b;
  button.textContent=a+" → "+b+(taken?" ✓":"");
  button.setAttribute("aria-label","Draw edge "+a+" to "+b);
  button.disabled=busy||needsRefresh||taken||!myTurn;q("[data-edges]").append(button);
 }
 q("[data-stop]").disabled=busy||needsRefresh||state.status!=="ACTIVE";
}
async function refresh(){
 if(!me)return;
 if(refreshInFlight)return refreshInFlight;
 const current=me;
 refreshInFlight=(async()=>{
  const next=await post("/arena/rooms/state",{
   room_id:current.room_id,reconnect_token:current.reconnect_token,
  });
  if(me!==current)return;
  if(next.game_key!=="dot")throw new Error("arena_room_game_invalid");
  state=next;me.seat=next.your_seat;needsRefresh=false;render();
 })();
 try{await refreshInFlight;}finally{refreshInFlight=null;}
}
function lockEntry(locked){
 entryBusy=locked;
 for(const key of ["[data-create]","[data-join]","[data-reconnect]"])
  q(key).disabled=locked;
}
async function enter(task){
 if(entryBusy||busy)return;
 lockEntry(true);clear();
 try{await task();}catch(e){error(e);}
 finally{lockEntry(false);}
}
async function act(action,a=null,b=null){
 if(busy||needsRefresh||!state||!me)return;
 busy=true;render();clear();
 try{
  const data=await post("/arena/rooms/dot/action",{...me,expected_revision:state.revision,request_id:rid(),action,a,b});
  note(data.duplicate?"Action already recorded":"Move recorded");await refresh();
 }catch(e){
  error(e);needsRefresh=true;
  note("Move outcome requires server read-back. Refresh before another action.");
  try{
   await refresh();
   if(e.message==="arena_room_revision_conflict")note("Board refreshed after other player's move.");
  }catch(err){
   error(err);note("Could not confirm the board. Retry Refresh before moving.");
  }
 }
 finally{busy=false;render();}
}
q("[data-create]").onclick=()=>enter(async()=>{
 const data=await post("/arena/rooms/create",{
  game_key:"dot",host_name:q("[data-host]").value.trim(),capacity:2,
 });
 showIdentity(data);note("Room created. Share only the room code; save your private token.");
 await refresh();
});
q("[data-join]").onclick=()=>enter(async()=>{
 const data=await post("/arena/rooms/join",{
  room_code:q("[data-code-input]").value.trim().toUpperCase(),
  display_name:q("[data-guest]").value.trim(),
 });
 showIdentity(data);note("Room joined. Save your private reconnect token.");
 await refresh();
});
q("[data-reconnect]").onclick=()=>enter(async()=>{
 const room_id=q("[data-reconnect-id]").value.trim();
 const reconnect_token=q("[data-reconnect-token]").value.trim();
 if(!room_id||!reconnect_token)throw new Error("Room ID and private token are required.");
 const previous=me;
 me={room_id,reconnect_token,seat:0};
 try{
  await refresh();
  if(!state.players.some(p=>p.seat===me.seat))throw new Error("arena_room_seat_invalid");
  q("[data-entry]").hidden=true;q("[data-match]").hidden=false;
  q("[data-id]").textContent=me.room_id;q("[data-token]").textContent=me.reconnect_token;
  note("Reconnected.");
 }catch(e){me=previous;state=null;throw e;}
});
q("[data-refresh]").onclick=async()=>{
 if(busy||entryBusy)return;
 clear();q("[data-refresh]").disabled=true;
 try{await refresh();note("Latest server board loaded.");}
 catch(e){needsRefresh=true;error(e);note("Could not confirm the board. Retry Refresh before moving.");}
 finally{q("[data-refresh]").disabled=false;render();}
};
q("[data-edges]").onclick=e=>{const btn=e.target.closest("[data-a]");if(btn&&!btn.disabled)act("draw",btn.dataset.a,btn.dataset.b);};
q("[data-stop]").onclick=()=>act("stop");
})();
