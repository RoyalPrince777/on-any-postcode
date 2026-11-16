(()=>{"use strict";
const root=document.querySelector("[data-oap-newgame]");if(!root)return;
const game=root.dataset.oapNewgame,status=document.getElementById("game-status"),play=document.getElementById("game-play"),restart=document.getElementById("restart");
const el=(tag,txt,cls)=>{const n=document.createElement(tag);if(txt!==undefined)n.textContent=String(txt);if(cls)n.className=cls;return n};
const btn=(txt,fn)=>{const b=el("button",txt,"action");b.type="button";b.addEventListener("click",fn);return b};
const random=n=>Math.floor(Math.random()*n);
const announce=t=>{status.textContent=t;};
const clear=()=>play.replaceChildren();
const journeys={3:22,8:30,19:41,27:54,39:60,48:72,58:84,66:90,94:73,89:67,79:56,64:43,52:29,37:14,25:5};
let snake;
function newSnakes(){snake={positions:[1,1],turn:0,finished:false,rolls:0};renderSnakes();}
function renderSnakes(){
 clear();const player=snake.turn;announce(snake.finished?"🏆 Player "+(player+1)+" wins!":"Player "+(player+1)+" to roll · Gold vs Purple · Exact 100 wins");
 const board=el("div",undefined,"board");board.setAttribute("aria-label","Snakes and ladders 100 square board");
 for(let row=9;row>=0;row--){const nums=Array.from({length:10},(_,i)=>row*10+(row%2===0?i+1:10-i));
 for(const n of nums){let mark=snake.positions[0]===n&&snake.positions[1]===n?"both":snake.positions[0]===n?"one":snake.positions[1]===n?"two":"";
 const glyph=journeys[n]?(journeys[n]>n?"🪜":"🐍"):"";const tile=el("button",n+" "+glyph+(mark==="both"?" 👑👑":mark==="one"?" 🟡":mark==="two"?" 🟣":""));tile.type="button";tile.disabled=true;if(journeys[n])tile.className="special";if(mark)tile.classList.add("piece");tile.dataset.here=mark;tile.setAttribute("aria-label","Square "+n+(journeys[n]?" to "+journeys[n]:"")+(mark?" occupied by "+mark:""));board.append(tile);}}
 play.append(board);const actions=el("div",undefined,"actions");const roll=btn("🎲 Roll dice",()=>{if(snake.finished)return;const dice=random(6)+1;let next=snake.positions[player]+dice;if(next>100)next=snake.positions[player];if(journeys[next])next=journeys[next];snake.positions[player]=next;snake.rolls++;snake.finished=next===100;if(!snake.finished)snake.turn=1-player;renderSnakes();const note=el("p","Last roll: "+dice+" · Player "+(player+1)+" moved to "+next);play.append(note);});roll.disabled=snake.finished;actions.append(roll);play.append(actions);
}
const words=[["POSTCODE","Local areas have their own codes"],["BOROUGH","Part of a city or region"],["CHRONICLE","A record of events"],["MARKET","A place to trade"],["JOURNEY","A trip from one place to another"],["COMMUNITY","People connected by place or purpose"],["CULTURE","Shared traditions and creativity"],["KINGDOM","A realm"],["HARMONY","Working well together"],["MANIFEST","To make clear or visible"]];
let scramble;
function shuffled(word){const a=word.split("");for(let i=a.length-1;i>0;i--){const j=random(i+1);[a[i],a[j]]=[a[j],a[i]];}const result=a.join("");return result===word?word.slice(1)+word[0]:result;}
function newScramble(){scramble={used:[],score:0,round:0,misses:0,current:null};nextWord();}
function nextWord(){const left=words.map((_,i)=>i).filter(i=>!scramble.used.includes(i));if(!left.length){scramble.current=null;renderScramble();return;}const id=left[random(left.length)];scramble.used.push(id);scramble.current={answer:words[id][0],hint:words[id][1],mix:shuffled(words[id][0])};scramble.round++;renderScramble();}
function renderScramble(){clear();announce(scramble.current?"Word "+scramble.round+" of "+words.length+" · Score "+scramble.score:"Finished · "+scramble.score+" / "+words.length+" correct");if(!scramble.current){play.append(el("p","All words completed!"));return;}const w=scramble.current;play.append(el("div",w.mix,"word"));play.append(el("p","Hint: "+w.hint));const form=el("form");const input=el("input");input.type="text";input.autocomplete="off";input.maxLength=32;input.setAttribute("aria-label","Unscramble word");input.required=true;form.append(input);const submit=btn("Unlock word",()=>{});submit.type="submit";submit.replaceWith();form.addEventListener("submit",e=>{e.preventDefault();const guess=input.value.trim().toUpperCase().replace(/\s+/g,"");if(!guess)return;if(guess===w.answer){scramble.score++;nextWord();}else{scramble.misses++;announce("Not quite · "+w.hint+" · Attempts: "+scramble.misses);}});form.append(submit);play.append(form);play.append(btn("Skip",nextWord));}
const places=["THE SPOT","SOUTH LONDON","COMMUNITY GARDEN","MARKET SQUARE","TRANSPORT LINK","BOROUGH HUB","LOCAL STUDIO","OAP TV","CULTURE HOUSE","LIBRARY","GHANA GATE","SPORTS GROUND","CREATOR LAB","SKILLS CENTRE","MUSIC YARD","CITY MARKET","YOUTH HUB","POSTCODE PARK","TECH QUARTER","GLOBAL LINK"];
const costs=[0,60,50,80,70,95,85,90,75,65,100,70,90,80,95,100,65,55,110,125];
let empire;
function newEmpire(){empire={p:[0,0],wallet:[300,300],owner:Array(20).fill(-1),levels:Array(20).fill(0),turn:0,last:"Welcome. Build neighbourhood value, not just rent.",round:0,over:false};renderEmpire();}
function renderEmpire(){clear();const t=empire.turn;announce(empire.over?"Final standings":"Player "+(t+1)+" · "+(t===0?"Gold":"Purple")+" · Credits "+empire.wallet[t]+" · Turn "+(empire.round+1));
const grid=el("div",undefined,"route");grid.setAttribute("aria-label","Postcode Empire twenty location circuit");places.forEach((name,i)=>{const own=empire.owner[i];const b=el("button",(i+1)+" · "+name+"\n"+(own<0?"Open":("P"+(own+1)+" Level "+empire.levels[i]))+"\n"+(empire.p[0]===i?"🟡 ":"")+(empire.p[1]===i?"🟣":""));b.type="button";b.disabled=true;if(empire.p.includes(i))b.classList.add("current");if(own>=0)b.classList.add("owned");grid.append(b);});play.append(grid);play.append(el("p",empire.last));
const actions=el("div",undefined,"actions");
if(!empire.over){const roll=btn("🎲 Travel",()=>{const d=random(6)+1;const pos=(empire.p[t]+d)%places.length;empire.p[t]=pos;if(pos===0)empire.wallet[t]+=70;
const own=empire.owner[pos];empire.last="Player "+(t+1)+" rolled "+d+" and reached "+places[pos]+".";
if(own>=0&&own!==t){const rent=Math.min(empire.wallet[t],10+empire.levels[pos]*10);empire.wallet[t]-=rent;empire.wallet[own]+=rent;empire.last+=" Local service fee "+rent+" credits to Player "+(own+1)+".";}renderEmpireChoice();});actions.append(roll);}
play.append(actions);}
function renderEmpireChoice(){renderEmpire();const t=empire.turn,pos=empire.p[t];const actions=el("div",undefined,"actions");const owner=empire.owner[pos];const price=costs[pos];
if(!empire.over&&pos!==0&&owner===-1&&empire.wallet[t]>=price){actions.append(btn("Develop "+places[pos]+" · "+price+" credits",()=>{empire.wallet[t]-=price;empire.owner[pos]=t;empire.levels[pos]=1;empire.last="Player "+(t+1)+" developed "+places[pos]+".";advance();}));}
if(!empire.over&&owner===t&&empire.levels[pos]<3&&empire.wallet[t]>=50){actions.append(btn("Upgrade local services · 50 credits",()=>{empire.wallet[t]-=50;empire.levels[pos]++;empire.last="Player "+(t+1)+" upgraded "+places[pos]+".";advance();}));}
actions.append(btn("End turn",advance));play.append(actions);}
function advance(){empire.turn=1-empire.turn;if(empire.turn===0)empire.round++;if(empire.round>=12){empire.over=true;const totals=empire.wallet.map((money,p)=>money+empire.owner.reduce((sum,own,i)=>sum+(own===p?costs[i]*empire.levels[i]:0),0));empire.last="After 12 rounds: Player 1 "+totals[0]+" | Player 2 "+totals[1]+". "+(totals[0]===totals[1]?"Draw!":"Player "+(totals[0]>totals[1]?1:2)+" wins!");}renderEmpire();}
restart.onclick=()=>({snakes:newSnakes,scramble:newScramble,empire:newEmpire}[game]||newSnakes)();
restart.click();
})();