/* OAP SMI: verified original-art pixel motion. No new avatar, no guessed lip-sync,
 * no private asset export, no new pixels or inferred hidden anatomy. */
(function(root,factory){
 "use strict";
 const api=factory();
 if(typeof module==="object"&&module.exports)module.exports=api;
 if(root)root.OAP_SMI_SOURCE_PIXEL_MOTION=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
 "use strict";
 const SOURCE="/static/oap/smi_live_chat_dashboard.jpg";
 const SHA256="f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b";
 const WIDTH=1536,HEIGHT=1024;
 const REGIONS=Object.freeze([
  Object.freeze({id:"head",x:622,y:95,w:304,h:250,rx:149,ry:120,cx:768,cy:203}),
  Object.freeze({id:"eyes",x:716,y:210,w:106,h:38,rx:51,ry:17,cx:769,cy:228}),
  Object.freeze({id:"mouth",x:738,y:253,w:66,h:33,rx:30,ry:14,cx:769,cy:267}),
  Object.freeze({id:"chest",x:618,y:338,w:307,h:295,rx:148,ry:143,cx:770,cy:485}),
  Object.freeze({id:"left-hand",x:385,y:704,w:177,h:113,rx:85,ry:52,cx:479,cy:767}),
  Object.freeze({id:"right-hand",x:968,y:704,w:178,h:113,rx:86,ry:52,cx:1056,cy:766})
 ]);
 const STATES=new Set(["ready","listening","thinking","speaking","paused","stopped"]);
 function remapRegion(source,region,dx,dy,scaleY){
  if(!source||source.width!==region.w||source.height!==region.h||!source.data)return null;
  const w=source.width,h=source.height,old=source.data,next=new Uint8ClampedArray(old);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   const px=region.x+x,py=region.y+y;
   const nx=(px-region.cx)/region.rx,ny=(py-region.cy)/region.ry;
   const r2=nx*nx+ny*ny;
   if(r2>=1)continue;
   const fade=(1-r2)*(1-r2);
   const sx=Math.max(0,Math.min(w-1,Math.round(x-dx*fade)));
   const sy=Math.max(0,Math.min(h-1,Math.round(y-dy*fade-(py-region.cy)*(scaleY-1)*fade)));
   const a=(y*w+x)*4,b=(sy*w+sx)*4;
   for(let k=0;k<4;k++)next[a+k]=old[b+k];
  }
  return {width:w,height:h,data:next};
 }
 function boundedGaze(target){
  if(!target||typeof target!=="object"||!Number.isFinite(target.x)||!Number.isFinite(target.y))return null;
  return Object.freeze({x:Math.max(-1,Math.min(1,target.x)),y:Math.max(-1,Math.min(1,target.y))});
 }
 function blinkEnvelope(ms){
  // Deterministic nonuniform intervals; never uses timers, microphones or camera tracking.
  const cycle=5650,phase=((ms%cycle)+cycle)%cycle;
  const triangular=(centre,width)=>Math.max(0,1-Math.abs(phase-centre)/width);
  return Math.max(triangular(750,90),triangular(3420,75),triangular(3575,55));
 }
 function motionFor(state,ms,speechPulse=0,gazeTarget=null){
  const a=Math.sin(ms/620),b=Math.sin(ms/1110);
  if(state==="stopped"||state==="paused")return Object.freeze({head:[0,0,1],eyes:[0,0,1],mouth:[0,0,1],chest:[0,0,1],hands:[0,0,1]});
  const focus=state==="thinking"?1.35:state==="listening"?1.18:1;
  const blink=blinkEnvelope(ms);
  const eyeScale=Math.max(.2,1-(blink*.78));
  const gaze=boundedGaze(gazeTarget);
  const gx=gaze?gaze.x:0,gy=gaze?gaze.y:0;
  // Coordinate small gestures with permitted audible viseme pulses; no inferred emotion.
  const audible=state==="speaking"&&Number.isFinite(speechPulse)?Math.max(0,Math.min(1,speechPulse)):0;
  const emphasis=audible*audible;
  return Object.freeze({
   head:[a*1.35*focus+gx*.55,b*.72*focus+gy*.35+emphasis*.35,1],
   eyes:[a*1.9*focus+gx*2.2,b*.58*focus+gy*1.15,eyeScale],
   mouth:state==="speaking"?[audible*1.15,audible*1.45,1+audible*.32]:[0,0,1],
   chest:[0,b*.78,1+b*.0045],
   hands:[a*.48+emphasis*.32,-b*.42-emphasis*.27,1]
  });
 }
 async function attach(win=typeof window!=="undefined"?window:null,doc=win?.document){
  const shell=doc?.querySelector?.(".smi-shell");
  if(!shell||!win?.fetch||!win?.crypto?.subtle||!win?.requestAnimationFrame||!doc.createElement)return null;
  const response=await win.fetch(SOURCE,{credentials:"same-origin",cache:"no-store"});
  if(!response.ok)return null;
  const bytes=await response.arrayBuffer();
  if(bytes.byteLength<1024||bytes.byteLength>10*1024*1024)return null;
  const digest=await win.crypto.subtle.digest("SHA-256",bytes);
  const actual=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,"0")).join("");
  if(actual!==SHA256)return null;
  const blob=new Blob([bytes],{type:"image/jpeg"});
  let image;
  if(win.createImageBitmap)image=await win.createImageBitmap(blob);
  else image=await new Promise((resolve,reject)=>{
   const el=new win.Image(),url=win.URL.createObjectURL(blob);
   el.onload=()=>{win.URL.revokeObjectURL(url);resolve(el);};
   el.onerror=()=>{win.URL.revokeObjectURL(url);reject(new Error("artwork decode failed"));};
   el.src=url;
  });
  if(image.width!==WIDTH||image.height!==HEIGHT){image.close?.();return null;}
  const canvas=doc.createElement("canvas");canvas.id="smi-source-pixel-motion";
  canvas.width=WIDTH;canvas.height=HEIGHT;canvas.setAttribute("aria-hidden","true");
  canvas.style.cssText="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center center;pointer-events:none;z-index:0";
  shell.prepend(canvas);
  const context=canvas.getContext("2d",{willReadFrequently:true});
  if(!context){canvas.remove();image.close?.();return null;}
  context.drawImage(image,0,0);
  const samples=Object.fromEntries(REGIONS.map(region=>[region.id,context.getImageData(region.x,region.y,region.w,region.h)]));
  async function digestParts(parts){
   const encoder=new win.TextEncoder();
   let total=0;
   const chunks=[];
   for(const [label,data] of parts){
    const prefix=encoder.encode(String(label)+":");
    const bytes=data instanceof Uint8Array?data:new Uint8Array(data.buffer||data);
    chunks.push(prefix,bytes);total+=prefix.length+bytes.length;
   }
   const merged=new Uint8Array(total);let offset=0;
   for(const chunk of chunks){merged.set(chunk,offset);offset+=chunk.length;}
   const hash=await win.crypto.subtle.digest("SHA-256",merged);
   return Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,"0")).join("");
  }
  const evidenceLayerSha256=Object.freeze({
   eyes:await digestParts([["eyes",samples["eyes"].data]]),
   head:await digestParts([["head",samples["head"].data]]),
   breathing:await digestParts([["chest",samples["chest"].data]]),
   mouth_visemes:await digestParts([["mouth",samples["mouth"].data]]),
   face:await digestParts([["head",samples["head"].data],["eyes",samples["eyes"].data],["mouth",samples["mouth"].data]]),
   hands:await digestParts([["left-hand",samples["left-hand"].data],["right-hand",samples["right-hand"].data]]),
   upper_body:await digestParts([["head",samples["head"].data],["chest",samples["chest"].data],["left-hand",samples["left-hand"].data],["right-hand",samples["right-hand"].data]])
  });
  const lowPower=/Android/i.test(win.navigator?.userAgent||"")||Number(win.navigator?.hardwareConcurrency||8)<=4;
  const frameBudgetMs=lowPower?50:34;
  let epoch=0,frame=0,last=0,phase="ready",live=false,reducedPreference=Boolean(win.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches),userReducedMotion=Boolean(win.OAP_SMI_REDUCED_MOTION?.read?.()),explicitLiveMotion=false,played=0,audioCues=0,droppedFrames=0;
  let playbackEpoch=null,localAudio=false,localViseme="silence",maxAudioClockDeltaMs=0,gazeTarget=null,stoppedLatched=false;
  const rigLayerFrames={eyes:0,head:0,breathing:0,mouth_visemes:0,face:0,hands:0,upper_body:0};
  const LOCAL_POSE=Object.freeze({silence:0,closed:.04,wide:1,round:.7,teeth:.45,tongue:.55});
  function drawRegion(region,params){
   const [dx,dy,scaleY]=params;
   context.save();
   context.beginPath();
   context.ellipse(region.cx,region.cy,region.rx,region.ry,0,0,Math.PI*2);
   context.clip();
   context.translate(dx,dy);
   context.translate(region.cx,region.cy);
   context.scale(1,Math.max(.18,Math.min(1.4,scaleY)));
   context.translate(-region.cx,-region.cy);
   context.drawImage(image,region.x,region.y,region.w,region.h,region.x,region.y,region.w,region.h);
   context.restore();
  }
  function draw(ms){
   context.drawImage(image,0,0);
   const motionAllowed=!userReducedMotion&&(!reducedPreference||explicitLiveMotion);
   if(!live||!motionAllowed||phase==="paused"||phase==="stopped")return;
   const pulse=phase==="speaking"&&localAudio?LOCAL_POSE[localViseme]:0;
   const poses=motionFor(phase,ms,pulse,gazeTarget);
   for(const region of REGIONS){
    const params=region.id==="left-hand"||region.id==="right-hand"?poses.hands:region.id==="chest"?poses.chest:region.id==="eyes"?poses.eyes:region.id==="mouth"?poses.mouth:poses.head;
    drawRegion(region,params);
   }
   played++;
   rigLayerFrames.head+=1;rigLayerFrames.eyes+=1;rigLayerFrames.breathing+=1;
   rigLayerFrames.face+=1;rigLayerFrames.hands+=1;rigLayerFrames.upper_body+=1;
   if(phase==="speaking"&&((localAudio&&localViseme!=="silence")||(!localAudio&&pulse>0)))rigLayerFrames.mouth_visemes+=1;
  }
  function tick(now){
   if(epoch<0)return;
   frame=win.requestAnimationFrame(tick);
   const motionAllowed=!userReducedMotion&&(!reducedPreference||explicitLiveMotion);
   if(doc.hidden||!live||!motionAllowed||phase==="paused"||phase==="stopped")return;
   if(now-last<frameBudgetMs){droppedFrames+=1;return;}
   last=now;draw(now);
  }
  function onState(event){
   const state=String(event?.detail?.state||"ready");
   if(stoppedLatched)return;
  phase=STATES.has(state)?state:"stopped";
  if(phase==="stopped"||event?.detail?.stopped===true){stoppedLatched=true;gazeTarget=null;}
   playbackEpoch=event?.detail?.epoch;
   explicitLiveMotion=event?.detail?.live===true&&!event?.detail?.stopped;
   live=(explicitLiveMotion||phase==='listening'||phase==='thinking'||phase==='speaking')&&!event?.detail?.stopped;
   if(!live||phase==="paused"||phase==="stopped"){localAudio=false;localViseme="silence";draw(0);}
  }
  // Only the explicit Live SMI human control may clear the renderer's STOP latch.
  win.addEventListener("oap-smi-human-motion-reset",event=>{
   if(event?.detail?.approved!==true||!stoppedLatched||epoch<0)return;
   stoppedLatched=false;gazeTarget=null;phase="ready";live=false;
   localViseme="silence";localAudio=false;
   context.drawImage(image,0,0);
  });
  win.addEventListener("oap-smi-character-state",onState);
  // Focus changes are explicit in-page interactions, not camera or pointer tracking.
  const focusTargets=[["message",{x:0.3,y:0.75}],["send",{x:0.65,y:0.55}],["live-character-toggle",{x:-0.65,y:-0.3}]];
  for(const [id,target] of focusTargets){
   const element=doc.getElementById?.(id);
   element?.addEventListener?.("focus",()=>{
    if(stoppedLatched||!live||userReducedMotion)return;
    gazeTarget=boundedGaze(target);
   });
  }
  // Opt-in directional gaze from explicit, bounded UI targets only; no eye/camera tracking.
  win.addEventListener("oap-smi-gaze-target",event=>{
   if(stoppedLatched||!live||userReducedMotion)return;
   gazeTarget=boundedGaze(event?.detail);
  });
  win.addEventListener("oap-smi-reduced-motion-change",event=>{
   userReducedMotion=event?.detail?.enabled===true;
   if(userReducedMotion){localViseme="silence";draw(0);}
  });
  win.addEventListener("oap-smi-playback-state",event=>{
   const playback=event?.detail;
   const allowed=!stoppedLatched&&live&&phase==="speaking"&&
     playback?.epoch===playbackEpoch;
   localAudio=allowed&&playback?.phase==="playing"&&
     playback?.source==="oap-first-party-pcm"&&playback?.decodedAudio===true;
   if(!localAudio)localViseme="silence";
  });
  win.addEventListener("oap-smi-audio-cue",event=>{
   const cue=event?.detail;
   if(stoppedLatched||!localAudio||phase!=="speaking"||!live||userReducedMotion||(!explicitLiveMotion&&reducedPreference)||
      cue?.source!=="oap-first-party-pcm"||cue?.decodedAudio!==true||
      cue?.synthesisPhonemeTiming!==true||cue?.epoch!==playbackEpoch||
      !Number.isFinite(cue?.audioClockMs)||cue.audioClockMs<0||
      !Object.hasOwn(LOCAL_POSE,cue?.viseme))return;
   localViseme=cue.viseme;
   audioCues+=1;
   if(Number.isFinite(cue.atMs))maxAudioClockDeltaMs=Math.max(maxAudioClockDeltaMs,Math.abs(cue.audioClockMs-cue.atMs));
   draw(win.performance.now());
  });
  // Browser text/speech boundary events are not an audio-aligned proof source.
  // Keep the mouth neutral unless decoded first-party audio supplied a viseme.

  win.addEventListener("pagehide",()=>{epoch=-1;win.cancelAnimationFrame?.(frame);context.drawImage(image,0,0);image.close?.();});
  frame=win.requestAnimationFrame(tick);
  shell.dataset.smiSourcePixelMotion="original_sha_verified";
  function proofSnapshot(){
   // Pixel warps and layer hashes show rendering activity, not an independently
   // verified segmented full-body character rig or physical-device acceptance.
   const fullBodyRigProven=false;
   // Browser event counts and measured deltas are observations, not independent
   // proof that visible mouth movement accurately tracks audible speech.
   const accurateSoftwareLipSyncProven=false;
   return Object.freeze({phase,live,frames:played,audioCues,localAudio,localViseme,gazeTarget,stoppedLatched,
    sourceSha256:actual,evidenceLayerSha256,rigLayerFrames:Object.freeze({...rigLayerFrames}),
    reducedMotionPreference:reducedPreference,userReducedMotionPreference:userReducedMotion,explicitLiveMotion,
    maxAudioClockDeltaMs,fullSceneSourcePixelMotion:played>0,fullBodyRigProven,
    accurateSoftwareLipSyncProven,accurateHumanLipSyncProven:false,
    physicalDeviceProofExcluded:true,privacyNoTelemetry:true});
  }
  return Object.freeze({sourceSha256:actual,sourceOnly:true,decodedAudio:false,
   privacyNoTelemetry:true,snapshot:proofSnapshot,
   stop:()=>{stoppedLatched=true;gazeTarget=null;live=false;phase="stopped";epoch=-1;win.cancelAnimationFrame?.(frame);context.drawImage(image,0,0);}});
 }
 return Object.freeze({SOURCE,SHA256,WIDTH,HEIGHT,REGIONS,remapRegion,boundedGaze,blinkEnvelope,motionFor,attach});
});
