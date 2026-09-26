/* OAP SMI exact-character rig proof aggregator.
 * The source-pixel motion renderer remains the only pixel owner. This module
 * never creates a second avatar or second renderer; it records canonical
 * seven-layer runtime proof from that first-party renderer.
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
  const LAYERS=Object.freeze(["eyes","head","breathing","mouth_visemes","face","hands","upper_body"]);
  const STATES=new Set(["ready","listening","thinking","speaking","paused","stopped"]);

  function create(){
    let state="ready",epoch=0,stopped=false,paused=false;
    let acceptedEvents=0,rejectedEvents=0,motionSession=null;
    function sourceSnapshot(){
      try{return motionSession?.snapshot?.()||null;}catch{return null;}
    }
    function freezeSnapshot(){
      const source=sourceSnapshot();
      const hashes=source?.evidenceLayerSha256||{};
      const frames=source?.rigLayerFrames||{};
      const layers=Object.fromEntries(LAYERS.map(name=>[name,Boolean(
        /^[a-f0-9]{64}$/.test(String(hashes[name]||""))&&Number(frames[name]||0)>0
      )]));
      const fullRigProven=source?.fullBodyRigProven===true&&LAYERS.every(name=>layers[name]);
      return Object.freeze({
        version:"1.0-live-source-pixel-proof",
        asset:APPROVED_ART.path,assetSha256:APPROVED_ART.sha256,
        enabled:Boolean(motionSession),active:Boolean(source?.live),
        proofState:fullRigProven?"machine_proven":"awaiting_runtime_frames",
        state,epoch,stopped,paused,layers:Object.freeze(layers),
        acceptedEvents,rejectedEvents,emitsFrames:false,
        rendererOwner:"smi_source_pixel_motion",
        fullRigProven,
        accurateSoftwareLipSyncProven:source?.accurateSoftwareLipSyncProven===true,
        accurateHumanLipSyncProven:false,
        physicalDeviceProofExcluded:true,
        storesAudio:false,storesTranscript:false,externalTelemetry:false,
        requiresHumanApproval:false,productionApproved:false,humanFinalApproved:false
      });
    }
    function transition(event){
      const next=String(event?.state||"");
      if(next==="stopped"){
        epoch+=1;state="stopped";stopped=true;paused=false;acceptedEvents+=1;
        return freezeSnapshot();
      }
      if(stopped){rejectedEvents+=1;return freezeSnapshot();}
      if(!STATES.has(next)){rejectedEvents+=1;return freezeSnapshot();}
      state=next;paused=next==="paused";acceptedEvents+=1;return freezeSnapshot();
    }
    function resetAfterExplicitHumanAction(approved){
      if(approved!==true||!stopped){rejectedEvents+=1;return freezeSnapshot();}
      epoch+=1;state="ready";stopped=false;paused=false;acceptedEvents+=1;
      return freezeSnapshot();
    }
    function bindMotionSession(session){
      if(!session||typeof session.snapshot!=="function"){rejectedEvents+=1;return freezeSnapshot();}
      const source=session.snapshot();
      if(source?.sourceSha256!==APPROVED_ART.sha256){rejectedEvents+=1;return freezeSnapshot();}
      motionSession=session;acceptedEvents+=1;return freezeSnapshot();
    }
    return Object.freeze({
      snapshot:freezeSnapshot,transition,bindMotionSession,
      frame:()=>null,activate:()=>freezeSnapshot(),resetAfterExplicitHumanAction
    });
  }
  function attachStateListener(root){
    if(!root?.addEventListener)return null;
    const rig=create();
    root.addEventListener("oap-smi-character-state",event=>rig.transition({state:event?.detail?.state}));
    return rig;
  }
  return Object.freeze({version:"1.0",asset:APPROVED_ART,layers:LAYERS,create,attachStateListener});
});
