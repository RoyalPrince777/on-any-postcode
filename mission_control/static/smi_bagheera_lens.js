/* Optional Bagheera advisory lens for the existing SMI chat.
 * No agent process, portrait replacement, voice activation or second renderer.
 * The canonical SMI controller retains exclusive send/mic/voice/pause/stop.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module==="object"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_BAGHEERA_LENS=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const VALID=new Set(["ready","listening","thinking","speaking","paused","stopped"]);
  const NAMES=Object.freeze({ready:"Ready",listening:"Listening",thinking:"Considering",
    speaking:"Speaking",paused:"Paused",stopped:"Stopped"});
  function displayState(detail,visible=true,reducedMotion=false){
    const state=VALID.has(detail?.state)?detail.state:"stopped";
    return Object.freeze({
      state:visible===true?state:"paused",
      text:visible===true?NAMES[state]:"Paused · page hidden",
      movementAllowed:visible===true&&reducedMotion!==true&&
        detail?.live===true&&detail?.stopped!==true&&
        !["paused","stopped"].includes(state),
      runtimeProof:false,
    });
  }
  function attach(win=typeof window!=="undefined"?window:null,doc=win?.document){
    const head=doc?.querySelector?.(".chat-head");
    if(!head||!win?.addEventListener||!doc?.createElement)return null;
    if(doc.getElementById("smi-bagheera-lens-toggle"))return null;
    const toggle=doc.createElement("button");
    toggle.type="button";toggle.id="smi-bagheera-lens-toggle";
    toggle.textContent="🐈‍⬛ Bagheera";
    toggle.setAttribute("aria-expanded","false");
    toggle.setAttribute("aria-controls","smi-bagheera-lens-status");
    toggle.setAttribute("aria-label","Show Bagheera advisory lens");
    toggle.style.cssText="flex:0 0 auto;border:1px solid #7b8d80;background:#101d19;color:#f4f7f4;border-radius:16px;padding:7px 10px;cursor:pointer;font:inherit";
    const panel=doc.createElement("section");
    panel.id="smi-bagheera-lens-status";
    panel.hidden=true;
    panel.setAttribute("role","status");
    panel.setAttribute("aria-live","polite");
    panel.style.cssText="position:absolute;z-index:30;top:100%;right:10px;max-width:min(330px,85vw);padding:12px;border:1px solid #7b8d80;border-radius:12px;background:#101d19;color:#f4f7f4;box-shadow:0 8px 22px #0008;font:inherit;line-height:1.45";
    const heading=doc.createElement("strong");heading.textContent="Bagheera · Protection & Truth";
    const copy=doc.createElement("p");
    copy.textContent="Advisory lens only. SMI owns this conversation. No separate Bagheera voice, camera, microphone or agent execution.";
    const status=doc.createElement("p");status.textContent="SMI: Ready";
    panel.append(heading,copy,status);
    // The switch never modifies the chat form, prompt, render pipeline or audio.
    head.append(toggle,panel);
    let opened=false;
    let last=displayState({state:"ready"});
    function update(){
      status.textContent="SMI: "+last.text+" · "+(last.movementAllowed?"motion eligible":"no motion claim");
    }
    function onCharacter(event){
      last=displayState(event?.detail,!doc.hidden,Boolean(
        doc.body?.classList?.contains?.("smi-user-reduced-motion")||
        win.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches
      ));
      update();
      if(last.state==="stopped")close();
    }
    function close(){
      opened=false;panel.hidden=true;toggle.setAttribute("aria-expanded","false");
    }
    function onClick(){
      opened=!opened;panel.hidden=!opened;
      toggle.setAttribute("aria-expanded",String(opened));
      update();
    }
    function onKey(event){if(event?.key==="Escape"&&opened){close();toggle.focus();}}
    function onVisibility(){last=displayState({state:last.state,live:false},!doc.hidden,true);update();if(doc.hidden)close();}
    toggle.addEventListener("click",onClick);
    win.addEventListener("oap-smi-character-state",onCharacter);
    doc.addEventListener("visibilitychange",onVisibility);
    doc.addEventListener("keydown",onKey);
    function stop(){
      win.removeEventListener?.("oap-smi-character-state",onCharacter);
      doc.removeEventListener?.("visibilitychange",onVisibility);
      doc.removeEventListener?.("keydown",onKey);
      toggle.removeEventListener?.("click",onClick);
      toggle.remove();panel.remove();
    }
    win.addEventListener("pagehide",stop,{once:true});
    return Object.freeze({snapshot:()=>Object.freeze({
      open:opened,canonicalState:last.state,movementEligible:last.movementAllowed,
      performsAgentExecution:false,ownsVoice:false,ownsRenderer:false,
      physicalDeviceVerified:false
    }),stop});
  }
  return Object.freeze({displayState,attach});
});
