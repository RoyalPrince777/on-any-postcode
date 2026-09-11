(()=>{
'use strict';
const form=document.getElementById('chat-form');
const input=document.getElementById('message');
const send=document.getElementById('send');
if(!form||!input)return;

let submitLocked=false;
let releaseTimer=null;
const RELEASE_AFTER_MS=125000;

function release(){
  submitLocked=false;
  if(releaseTimer){clearTimeout(releaseTimer);releaseTimer=null;}
}
function lock(){
  submitLocked=true;
  if(releaseTimer)clearTimeout(releaseTimer);
  releaseTimer=setTimeout(release,RELEASE_AFTER_MS);
}

// The base chat already owns Enter-to-send. The final UI layer previously added a
// second anonymous keydown handler, which could call requestSubmit twice for one
// Enter press. Capture the key first and issue exactly one governed submit.
input.addEventListener('keydown',event=>{
  if(event.key!=='Enter'||event.shiftKey||event.isComposing)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  if(submitLocked||send?.disabled)return;
  form.requestSubmit();
},true);

// Fail closed on any second submit while a response is active. This also protects
// against double taps, keyboard repeat and UI wrappers dispatching submit twice.
form.addEventListener('submit',event=>{
  if(submitLocked){
    event.preventDefault();
    event.stopImmediatePropagation();
    return;
  }
  lock();
},true);

// Release only when the governed stream completes, is explicitly stopped, or the
// page regains an idle send button after an error. Never poll the server.
window.addEventListener('oap-smi-complete',release);
document.getElementById('stop-button')?.addEventListener('click',release,true);

const observer=new MutationObserver(()=>{
  if(submitLocked&&send&&!send.disabled){release();}
});
observer.observe(send||form,{attributes:true,attributeFilter:['disabled']});

window.addEventListener('pagehide',()=>{
  if(releaseTimer)clearTimeout(releaseTimer);
  observer.disconnect();
},{once:true});
})();
