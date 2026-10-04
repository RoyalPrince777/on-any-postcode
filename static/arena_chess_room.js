(()=>{"use strict";
const root=document.querySelector("[data-room-root]");if(!root)return;const q=s=>root.querySelector(s);
const csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
const character={K:"🤴",Q:"👸",R:"🏰",B:"🧙",N:"🐎",P:"🛡️"};
const pieceName={K:"king",Q:"queen",R:"rook",B:"bishop",N:"knight",P:"pawn"};
function characterPiece(piece){
 if(!piece)return null;
 const span=document.createElement("span");
 span.className="arena-chess-character "+(piece[0]==="w"?"arena-chess-character-white":"arena-chess-character-black");
 span.dataset.piece=piece;
 span.setAttribute("aria-hidden","true");
 span.textContent=character[piece[1]];
 return span;
}
let membership=null,snapshot=null,busy=false,entryBusy=false,needsRefresh=false,selected=null,lastBoard={};
const req=()=>crypto.randomUUID().replaceAll("-","").slice(0,20);
const error=e=>q("[data-error]").textContent=e?.message||String(e);const clear=()=>q("[data-error]").textContent="";
async function post(path,body){const r=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(body)});const d=await r.json();if(!r.ok)throw new Error(d?.error?.code||"arena_room_request_failed");return d;}
function identity(data,seat){membership={room_id:data.room_id,reconnect_token:data.reconnect_token,seat};q("[data-entry]").hidden=true;q("[data-room]").hidden=false;q("[data-id]").textContent=membership.room_id;q("[data-token]").textContent=membership.reconnect_token;q("[data-code]").textContent=data.room_code||"";}
function render(){if(!membership||!snapshot)return;q("[data-code]").textContent=snapshot.room_code;q("[data-status]").textContent=snapshot.status;q("[data-revision]").textContent=String(snapshot.revision);
const me=snapshot.players.find(p=>p.seat===membership.seat);q("[data-players]").textContent=snapshot.players.map(p=>p.display_name+" ("+(p.seat===1?"White":"Black")+")").join(" vs ");
const game=snapshot.game_state||{};const myColour=membership.seat===1?"w":"b";const myTurn=snapshot.status==="ACTIVE"&&(!game.started||(game.turn===(membership.seat===1?"White":"Black")));
q("[data-turn]").textContent=(me?"Playing as "+me.display_name+" · ":"")+(game.status==="completed"?"Game completed":game.status==="stopped"?"Match stopped":myTurn?"Your turn":snapshot.status==="WAITING"?"Waiting for another player":"Other player's turn");
const previous=lastBoard;const board=q("[data-board]");board.replaceChildren();for(let rank=8;rank>=1;rank--)for(const file of "abcdefgh"){const id=file+rank,piece=(game.board||{})[id];const b=document.createElement("button");b.type="button";b.dataset.square=id;b.className="arena-chess-square "+(((file.charCodeAt(0)-97+rank)%2)?"arena-chess-dark":"arena-chess-light");b.replaceChildren();const characterNode=characterPiece(piece);if(characterNode)b.append(characterNode);b.dataset.piece=piece||"";b.setAttribute("aria-label",id+" "+(piece?(piece[0]==="w"?"White ":"Black ")+pieceName[piece[1]]:"empty"));b.disabled=busy||needsRefresh||!myTurn;if(previous[id]&&piece&&previous[id][0]!==piece[0])b.classList.add("arena-chess-capture");b.setAttribute("aria-pressed",String(selected===id));b.onclick=()=>{if(!myTurn)return;if(!selected){if(!piece||piece[0]!==myColour)return;selected=id;q("[data-source]").value=id;}else if(selected===id){selected=null;q("[data-source]").value="";}else{q("[data-target]").value=id;move();}render();};board.append(b);}
lastBoard={...(game.board||{})};q("[data-move]").disabled=busy||needsRefresh||!myTurn;q("[data-stop]").disabled=busy||needsRefresh||snapshot.status!=="ACTIVE";}
async function refresh(){const d=await post("/arena/rooms/state",{room_id:membership.room_id,reconnect_token:membership.reconnect_token});if(d.game_key!=="chess")throw new Error("arena_room_game_invalid");snapshot=d;membership.seat=d.your_seat;needsRefresh=false;render();}
async function enter(task){if(entryBusy||busy)return;entryBusy=true;clear();try{await task();}catch(e){error(e);}finally{entryBusy=false;}}
async function action(body){if(busy||needsRefresh||!membership||!snapshot)return;busy=true;render();clear();try{await post("/arena/rooms/chess/action",{...membership,expected_revision:snapshot.revision,request_id:req(),...body});selected=null;q("[data-source]").value="";q("[data-target]").value="";q("[data-promotion]").value="";await refresh();}catch(e){error(e);needsRefresh=true;try{await refresh();}catch(_){} }finally{busy=false;render();}}
function move(){const source=q("[data-source]").value.trim().toLowerCase(),target=q("[data-target]").value.trim().toLowerCase(),promotion=q("[data-promotion]").value||null;if(!/^[a-h][1-8]$/.test(source)||!/^[a-h][1-8]$/.test(target)){error(new Error("Use squares a1–h8."));return;}action({action:"move",source,target,promotion});}
q("[data-matchmake]").onclick=()=>enter(async()=>{const d=await post("/arena/rooms/matchmake",{game_key:"chess",display_name:q("[data-host]").value.trim()});identity(d,d.seat);await refresh();});
q("[data-matchmake]").onclick=()=>enter(async()=>{const d=await post("/arena/rooms/matchmake",{game_key:"chess",display_name:q("[data-host]").value.trim()});identity(d,d.seat);await refresh();});
q("[data-create]").onclick=()=>enter(async()=>{const d=await post("/arena/rooms/create",{game_key:"chess",capacity:2,host_name:q("[data-host]").value.trim()});identity(d,1);await refresh();});
q("[data-join]").onclick=()=>enter(async()=>{const d=await post("/arena/rooms/join",{room_code:q("[data-join-code]").value.trim().toUpperCase(),display_name:q("[data-guest]").value.trim()});identity(d,d.seat);await refresh();});
q("[data-reconnect]").onclick=()=>enter(async()=>{membership={room_id:q("[data-reconnect-id]").value.trim(),reconnect_token:q("[data-reconnect-token]").value.trim(),seat:0};await refresh();q("[data-entry]").hidden=true;q("[data-room]").hidden=false;q("[data-id]").textContent=membership.room_id;q("[data-token]").textContent=membership.reconnect_token;});
q("[data-refresh]").onclick=async()=>{clear();try{await refresh();}catch(e){error(e);needsRefresh=true;render();}};
q("[data-move]").onclick=move;q("[data-stop]").onclick=()=>action({action:"stop"});})();