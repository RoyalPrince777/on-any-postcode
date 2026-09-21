/* SMI 21: exact-character rig CONTRACT, not a functioning animation rig.
 * No image edits, skeleton, visemes, movement, telemetry, network or UI claims.
 * The currently approved first-party artwork stays the only visible character.
 */
(function(root,factory){
  "use strict";
  const api=factory();
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.OAP_SMI_EXACT_CHARACTER_RIG=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const APPROVED_ART=Object.freeze({
    path:"/static/oap/smi_live_chat_dashboard.jpg",
    sha256:"f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b"
  });
  const LAYERS=Object.freeze([
    "eyes","head","breathing","mouth_visemes","face","hands","upper_body"
  ]);
  const STATES=new Set(["ready","listening","thinking","speaking","paused","stopped"]);
  const LOCK="design_only_no_approved_layered_rig";
  // None of these inputs may be inferred from state, a still image or CSS:
  // independently reviewed segmented asset, landmarks, motion/viseme curves,
  // synchronised voice proof, STOP interruption, accessibility and Human Final.
  function create(){
    let state="ready",epoch=0,stopped=false,paused=false;
    let acceptedEvents=0,rejectedEvents=0;
    const readiness=Object.fromEntries(LAYERS.map(name=>[name,false]));
    function freezeSnapshot(){
      return Object.freeze({
        version:"0.1-design-only",
        asset:APPROVED_ART.path,
        assetSha256:APPROVED_ART.sha256,
        enabled:false,
        active:false,
        proofState:"not_proven",
        reason:LOCK,
        state,epoch,stopped,paused,
        layers:Object.freeze({...readiness}),
        acceptedEvents,rejectedEvents,
        emitsFrames:false,storesAudio:false,storesTranscript:false,
        externalTelemetry:false,requiresHumanApproval:true
      });
    }
    function transition(event){
      const next=String(event?.state||"");
      // Incoming state changes are metadata only: not geometry or animation.
      // Once stopped, a delayed speaking/listening event can never revive rig.
      if(next==="stopped"){
        epoch+=1;state="stopped";stopped=true;paused=false;acceptedEvents+=1;
        return freezeSnapshot();
      }
      if(stopped){
        rejectedEvents+=1;
        return freezeSnapshot();
      }
      if(!STATES.has(next)){
        rejectedEvents+=1;
        return freezeSnapshot();
      }
      state=next;paused=next==="paused";acceptedEvents+=1;
      return freezeSnapshot();
    }
    function resetAfterExplicitHumanAction(approved){
      // Only a *separate explicit human action* may release STOP.
      // Even after release, this foundation cannot activate or emit motion.
      if(approved!==true||!stopped){rejectedEvents+=1;return freezeSnapshot();}
      epoch+=1;state="ready";stopped=false;paused=false;acceptedEvents+=1;
      return freezeSnapshot();
    }
    function frame(){return null;}
    function activate(){rejectedEvents+=1;return freezeSnapshot();}
    return Object.freeze({
      snapshot:freezeSnapshot,transition,frame,activate,
      resetAfterExplicitHumanAction
    });
  }
  function attachStateListener(root){
    if(!root?.addEventListener)return null;
    const rig=create();
    root.addEventListener("oap-smi-character-state",event=>{
      const detail=event?.detail;
      // Event metadata never supplies permission, frame or gesture data.
      if(detail?.state==="stopped")rig.transition({state:"stopped"});
      else rig.transition({state:detail?.state});
    });
    return rig;
  }
  return Object.freeze({version:"0.1",asset:APPROVED_ART,
    layers:LAYERS,create,attachStateListener});
});
