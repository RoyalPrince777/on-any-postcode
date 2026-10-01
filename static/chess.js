(()=>{
"use strict";const root=document.querySelector("[data-chess-root]");if(!root)return;
const q=s=>root.querySelector(s),csrf=document.querySelector('meta[name="oap-csrf-token"]')?.content||"";
let state=null,busy=false,selected=null,lastBoard={};
const requestId=()=>crypto.randomUUID().replaceAll("-").slice(0,20);
const character={K:"🤴",Q:"👸",R:"🏰",B:"🧙",N:"🐎",P:"🛡️"};
const pieceName={K:"king",Q:"queen",R:"rook",B:"bishop",N:"knight",P:"pawn"};

function inferredMove(previous,current){
 const arrivals=[];const departures=[];
 for(const file of "abcdefgh")for(const rank of "12345678"){
  const square=file+rank,oldPiece=previous[square],newPiece=current[square];
  if(oldPiece&&oldPiece!==newPiece)departures.push({square,piece:oldPiece});
  if(newPiece&&oldPiece!==newPiece)arrivals.push({square,piece:newPiece,oldPiece});
 }
 for(const arrival of arrivals){
  const match=departures.find(item=>
   item.piece===arrival.piece ||
   (item.piece?.[1]==="P"&&arrival.piece?.[0]===item.piece?.[0]&&["Q","R","B","N"].includes(arrival.piece?.[1]))
  );
  if(match)return {source:match.square,target:arrival.square,capture:Boolean(arrival.oldPiece&&arrival.oldPiece[0]!==arrival.piece[0])};
 }
 return null;
}
function animateWalk(board,move){
 if(!move||matchMedia("(prefers-reduced-motion: reduce)").matches)return;
 const from=board.querySelector('[data-square="'+move.source+'"]');
 const to=board.querySelector('[data-square="'+move.target+'"]');
 const actor=to?.querySelector(".arena-chess-character");
 if(!from||!to||!actor)return;
 const a=from.getBoundingClientRect(),b=to.getBoundingClientRect();
 const dx=a.left-b.left,dy=a.top-b.top;
 actor.animate(
  [
   {transform:"translate("+dx+"px,"+dy+"px) translateY(0) scale(.96)"},
   {transform:"translate("+(dx*.72)+"px,"+(dy*.72)+"px) translateY(-5px) scale(.98)",offset:.25},
   {transform:"translate("+(dx*.48)+"px,"+(dy*.48)+"px) translateY(2px)",offset:.48},
   {transform:"translate("+(dx*.22)+"px,"+(dy*.22)+"px) translateY(-4px)",offset:.72},
   {transform:"translate(0,0) translateY(0) scale(1)"}
  ],
  {duration:360,easing:"cubic-bezier(.2,.75,.25,1)"}
 );
}

function characterPiece(piece){
 if(!piece)return null;
 const span=document.createElement("span");
 span.className="arena-chess-character "+(piece[0]==="w"?"arena-chess-character-white":"arena-chess-character-black");
 span.dataset.piece=piece;
 span.setAttribute("aria-hidden","true");
 span.textContent=character[piece[1]];
 return span;
}
const error=e=>q("[data-error]").textContent=e?.message||String(e);
async function post(path,payload){const r=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data?.error?.code||"arena_request_failed");return data;}
function render(){
 if(!state)return;q("[data-game]").hidden=false;
 const active=state.status==="active";
 q("[data-start]").disabled=busy||active;
 q("[data-turn]").textContent=active?state.turn:"—";q("[data-status]").textContent=state.status;
 q("[data-stop]").disabled=!active||busy;q("[data-move]").disabled=!active||busy;
 const previous=lastBoard;const walk=inferredMove(previous,state.board);const board=q("[data-board]");board.replaceChildren();
 for(let rank=8;rank>=1;rank--)for(const file of "abcdefgh"){
  const id=file+rank,piece=state.board[id];const square=document.createElement("button");
  square.type="button";square.className="arena-chess-square "+(((file.charCodeAt(0)-97+rank)%2)?"arena-chess-dark":"arena-chess-light");
  square.dataset.square=id;square.disabled=!active||busy;
  square.replaceChildren();
  const characterNode=characterPiece(piece);if(characterNode)square.append(characterNode);
  square.dataset.piece=piece||"";
  square.setAttribute("aria-label",id+" "+(piece?(piece[0]==="w"?"White ":"Black ")+pieceName[piece[1]]:"empty"));
  if(previous[id]&&piece&&previous[id][0]!==piece[0])square.classList.add("arena-chess-capture");
  square.setAttribute("aria-pressed",String(selected===id));board.append(square);
 }
 animateWalk(board,walk);lastBoard={...state.board};
 const completedMessage={checkmate:"Checkmate. Winner: "+state.winner,stalemate:"Stalemate.",draw_threefold:"Draw by threefold repetition.",draw_fifty_move:"Draw by fifty-move rule.",draw_insufficient_material:"Draw by insufficient material."};
 q("[data-feedback]").textContent=state.status==="completed"?(completedMessage[state.result]||"Game completed."):state.status==="stopped"?"Match stopped.":state.check?"Check. "+state.turn+" must respond.":selected?"Selected "+selected+". Choose destination.":"Select your piece or enter source and target squares.";
}
async function act(path,payload){if(busy||(path==="/arena/chess/start"&&state?.status==="active"))return;busy=true;q("[data-start]").disabled=true;q("[data-error]").textContent="";try{state=await post(path,payload);selected=null;
 if(path==="/arena/chess/start"||path==="/arena/chess/move"){
  q("[data-source]").value="";q("[data-target]").value="";q("[data-promotion]").value="";
 }
 render();}catch(e){error(e);}finally{busy=false;q("[data-start]").disabled=state?.status==="active";render();}}
function move(){
 const source=q("[data-source]").value.trim().toLowerCase(),target=q("[data-target]").value.trim().toLowerCase();
 if(!/^[a-h][1-8]$/.test(source)||!/^[a-h][1-8]$/.test(target)){error(new Error("Use squares a1–h8 (for example e2 → e4)."));return;}
 const promotion=q("[data-promotion]").value||null;act("/arena/chess/move",{source,target,promotion,request_id:requestId()});
}
q("[data-start]").onclick=()=>act("/arena/chess/start",{});
q("[data-move]").onclick=move;
q("[data-stop]").onclick=()=>act("/arena/chess/stop",{request_id:requestId()});
q("[data-board]").onclick=e=>{
 const btn=e.target.closest("[data-square]");if(!btn||btn.disabled)return;
 const id=btn.dataset.square;
 const piece=state.board[id];
 const ownColour=state.turn==="White"?"w":"b";
 if(!selected){
  if(!piece||piece[0]!==ownColour){
   q("[data-feedback]").textContent="Select one of your own pieces to begin.";
   return;
  }
  selected=id;q("[data-source]").value=id;q("[data-target]").value="";
  render();q('[data-square="'+id+'"]')?.focus();return;
 }
 if(selected===id){
  selected=null;q("[data-source]").value="";q("[data-target]").value="";
  render();q('[data-square="'+id+'"]')?.focus();return;
 }
 if(piece&&piece[0]===ownColour){
  selected=id;q("[data-source]").value=id;q("[data-target]").value="";
  render();q('[data-square="'+id+'"]')?.focus();return;
 }
 q("[data-target]").value=id;move();
};
})();