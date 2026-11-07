/* Offline SMI exact-character motion candidate.
 * Not imported by the live page. It produces bounded transform metadata only:
 * no DOM writes, images, audio capture, storage, network or telemetry.
 */
"use strict";

const APPROVED_SHA="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
const STATES=new Set(["ready","listening","thinking","speaking","paused"]);
const VISEMES=new Set(["silence","closed","wide","round","teeth","tongue"]);

function proofAccepted(proof){
  return Boolean(proof &&
    proof.approvedSourceSha256===APPROVED_SHA &&
    proof.pixelLineageProven===true &&
    proof.maskRegistrationProven===true &&
    proof.humanLayerReviewApproved===true &&
    proof.isolatedPrivateCandidate===true);
}

function frozenFrame(state,t,values){
  return Object.freeze({state,tMs:t,...values,productionApproved:false,
    humanFinalApproved:false,externalTelemetry:false,storesAudio:false,
    storesTranscript:false});
}

function createCandidate(proof){
  const admitted=proofAccepted(proof);
  let running=false,stopped=false,reducedMotion=true,state="ready",epoch=0;
  let acceptedEvents=0,rejectedEvents=0;
  function snapshot(){
    return Object.freeze({version:"0.1-isolated-candidate",admitted,running,
      stopped,reducedMotion,state,epoch,acceptedEvents,rejectedEvents,
      attachedToLivePage:false,rendersPixels:false,productionApproved:false,
      humanFinalApproved:false,externalTelemetry:false,storesAudio:false,
      storesTranscript:false});
  }
  function start(options={}){
    if(!admitted||options.humanAction!==true||stopped){rejectedEvents+=1;return snapshot();}
    reducedMotion=options.reducedMotion!==false;
    running=true;acceptedEvents+=1;return snapshot();
  }
  function transition(next){
    if(next==="stopped"){
      epoch+=1;state="stopped";stopped=true;running=false;acceptedEvents+=1;
      return snapshot();
    }
    if(stopped||!STATES.has(next)){rejectedEvents+=1;return snapshot();}
    state=next;acceptedEvents+=1;return snapshot();
  }
  function resetAfterExplicitHumanAction(approved){
    if(approved!==true||!stopped){rejectedEvents+=1;return snapshot();}
    epoch+=1;state="ready";stopped=false;running=false;reducedMotion=true;
    acceptedEvents+=1;return snapshot();
  }
  function frame(tMs,audio={}){
    if(!running||stopped||reducedMotion||state==="paused"||!Number.isFinite(tMs))return null;
    const t=Math.max(0,Math.min(30000,tMs));
    const breathe=Math.sin(t/850)*0.8;
    const neutral={eyes:{x:0,y:0},head:{rotateDeg:0,y:0},breathing:{scaleY:1},
      mouth_visemes:{scaleY:1,viseme:"silence"},face:{browY:0},
      hands:{leftY:0,rightY:0},upper_body:{y:0}};
    if(state==="ready")return frozenFrame(state,t,neutral);
    if(state==="listening")return frozenFrame(state,t,{...neutral,
      eyes:{x:Math.sin(t/700)*0.45,y:0},head:{rotateDeg:-0.45,y:0},
      breathing:{scaleY:1+breathe/100}});
    if(state==="thinking")return frozenFrame(state,t,{...neutral,
      eyes:{x:0.7,y:-0.35},head:{rotateDeg:0.7,y:-0.25},
      breathing:{scaleY:1+breathe/140},face:{browY:-0.35}});
    // Never animate speech from an arbitrary viseme or unproven decoded audio.
    // This isolated renderer is not a substitute for the authenticated audio gate.
    const audioClockValid=Number.isFinite(audio.playedAudioMs) &&
      audio.playedAudioMs>=0 && audio.playedAudioMs<=30000 &&
      Math.abs(audio.playedAudioMs-t)<=80;
    const audioAccepted=audioClockValid && audio.decodedAudio===true &&
      audio.source==="oap-first-party-pcm" && VISEMES.has(audio.viseme);
    const viseme=audioAccepted?audio.viseme:"silence";
    // Source-backed phoneme cues are sufficient to articulate a mouth even when
    // the audio renderer does not expose amplitude; untrusted audio stays neutral.
    const shapes={silence:1,closed:1,wide:1.12,round:1.08,teeth:1.05,tongue:1.06};
    const baseScale=shapes[viseme];
    const amplitude=Number.isFinite(audio.amplitude)?
      Math.max(0,Math.min(1,audio.amplitude)):null;
    const mouthScale=audioAccepted&&viseme!=="silence"?
      (amplitude===null?baseScale:1+(baseScale-1)*amplitude):1;
    if(!audioAccepted || viseme==="silence"){
      return frozenFrame(state,t,{...neutral,
        mouth_visemes:{scaleY:1,viseme:"silence"}});
    }
    return frozenFrame(state,t,{...neutral,
      head:{rotateDeg:Math.sin(t/900)*0.3,y:0},
      breathing:{scaleY:1+breathe/120},mouth_visemes:{scaleY:mouthScale,viseme},
      hands:{leftY:Math.sin(t/650)*0.6,rightY:Math.sin(t/650+0.8)*0.6}});
  }
  return Object.freeze({snapshot,start,transition,frame,resetAfterExplicitHumanAction});
}

module.exports=Object.freeze({APPROVED_SHA,createCandidate,proofAccepted});
