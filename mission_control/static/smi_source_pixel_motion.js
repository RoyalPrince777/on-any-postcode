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
 function motionFor(state,ms,speechPulse=0){
  if(state==="stopped"||state==="paused")return Object.freeze({head:[0,0,1],eyes:[0,0,1],mouth:[0,0,1],chest:[0,0,1],hands:[0,0,1]});
  // Bounded, natural-feeling movement of the same approved source pixels.
  const breathe=Math.sin(ms/1510);
  const glance=Math.sin(ms/2440);
  const micro=Math.sin(ms/760);
  const engaged=state==="listening"?1.16:state==="thinking"?1.09:1;
  const speak=state==="speaking";
  const blinkPhase=ms%4300;
  const blink=blinkPhase<135?Math.max(0,1-Math.abs(blinkPhase-67.5)/67.5):0;
  const eyeScale=Math.max(.2,1-(blink*.78));
  return Object.freeze({
   head:[(micro*.9+glance*.30)*engaged,(breathe*.65+(speak?micro*.28:0))*engaged,1],
   eyes:[(glance*1.25+micro*.35)*engaged,breathe*.38,eyeScale],
   mouth:speak?[speechPulse*1.15,speechPulse*1.45,1+speechPulse*.32]:[0,0,1],
   chest:[0,breathe*.74,1+breathe*.0045],
   hands:[micro*(state==="listening"?.22:.44),-breathe*.36,1]
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
  // Render at native source resolution on the display canvas. Readback belongs
  // to a one-time evidence canvas; willReadFrequently on the display surface
  // would force software rendering on common Android Chromium builds.
  const context=canvas.getContext("2d",{alpha:false});
  if(!context){canvas.remove();image.close?.();return null;}
  context.imageSmoothingEnabled=true;
  context.imageSmoothingQuality="high";
  const evidenceCanvas=doc.createElement("canvas");
  evidenceCanvas.width=WIDTH;evidenceCanvas.height=HEIGHT;
  const evidenceContext=evidenceCanvas.getContext("2d",{willReadFrequently:true});
  if(!evidenceContext){canvas.remove();image.close?.();return null;}
  evidenceContext.drawImage(image,0,0);
  const samples=Object.fromEntries(REGIONS.map(region=>[
    region.id,evidenceContext.getImageData(region.x,region.y,region.w,region.h)
  ]));
  evidenceCanvas.width=0;evidenceCanvas.height=0;
  context.drawImage(image,0,0);
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
  // 30/60 live and 20/30 idle are upper *targets*, not measured results.
  // Dynamically lower the rate if drawing is expensive; no 60-FPS device claim.
  const frameBudgetMs=lowPower?33:16;
  const ambientFrameBudgetMs=lowPower?50:33;
  let epoch=0,frame=0,last=0,phase="ready",live=false,reducedPreference=Boolean(win.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches),userReducedMotion=Boolean(win.OAP_SMI_REDUCED_MOTION?.read?.()),explicitLiveMotion=false,played=0,speechUntil=0,audioCues=0,droppedFrames=0;
  let renderCostMs=0,observedFps=0,lastPaintTime=0,adaptiveFrameBudgetMs=ambientFrameBudgetMs;
  function resetFrameTelemetry(){
   last=0;lastPaintTime=0;observedFps=0;renderCostMs=0;
   adaptiveFrameBudgetMs=live?frameBudgetMs:ambientFrameBudgetMs;
  }
  function renderActive(){
   return epoch>=0&&!doc.hidden&&!userReducedMotion&&
    (!reducedPreference||explicitLiveMotion)&&
    phase!=="paused"&&phase!=="stopped"&&(live||phase==="ready");
  }
  let playbackEpoch=null,localAudio=false,localViseme="silence",maxAudioClockDeltaMs=0;
  const rigLayerFrames={eyes:0,head:0,breathing:0,mouth_visemes:0,face:0,hands:0,upper_body:0};
  const LOCAL_POSE=Object.freeze({silence:0,closed:.04,wide:1,round:.7,teeth:.45,tongue:.55});
  // One-time edge feathering from the approved source JPG only. Hard cropped
  // ellipses left visible borders against the unmoving original at subpixel
  // offsets. Cached source-derived overlays remove that seam without a
  // substitute character, hidden anatomy, a second renderer, or per-frame
  // getImageData readbacks. Everything stays in this private browser session.
  const featheredPatches=new Map(REGIONS.map(region=>{
   const patch=doc.createElement("canvas");
   patch.width=region.w;patch.height=region.h;
   const pc=patch.getContext("2d",{alpha:true});
   if(!pc)return [region.id,null];
   pc.drawImage(image,region.x,region.y,region.w,region.h,0,0,region.w,region.h);
   pc.globalCompositeOperation="destination-in";
   pc.save();
   pc.translate(region.cx-region.x,region.cy-region.y);
   pc.scale(region.rx,region.ry);
   const edge=pc.createRadialGradient(0,0,.77,0,0,1);
   edge.addColorStop(0,"rgba(255,255,255,1)");
   edge.addColorStop(1,"rgba(255,255,255,0)");
   pc.fillStyle=edge;
   // Normalised extent covers the entire original region, including outside
   // its ellipse; transparent outer pixels cannot retain a hard rectangle.
   pc.fillRect(-2,-2,4,4);
   pc.restore();
   pc.globalCompositeOperation="source-over";
   return [region.id,patch];
  }));
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
   const patch=featheredPatches.get(region.id);
   if(patch)context.drawImage(patch,region.x,region.y);
   else context.drawImage(image,region.x,region.y,region.w,region.h,region.x,region.y,region.w,region.h);
   context.restore();
  }
  function draw(ms){
   context.drawImage(image,0,0);
   const motionAllowed=!userReducedMotion&&(!reducedPreference||explicitLiveMotion);
   if((!live&&phase!=="ready")||!motionAllowed||phase==="paused"||phase==="stopped")return;
   const pulse=phase==="speaking"?(localAudio?LOCAL_POSE[localViseme]:Math.max(0,Math.min(1,(speechUntil-ms)/170))):0;
   const poses=motionFor(phase,ms,pulse);
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
   if(!renderActive())return;
   const baseline=live?frameBudgetMs:ambientFrameBudgetMs;
   adaptiveFrameBudgetMs=Math.max(baseline,Math.min(100,renderCostMs*1.8));
   if(now-last<adaptiveFrameBudgetMs){droppedFrames+=1;return;}
   last=now;
   const paintStart=win.performance.now();
   draw(now);
   const cost=Math.max(0,win.performance.now()-paintStart);
   renderCostMs=renderCostMs===0?cost:renderCostMs*.85+cost*.15;
   if(lastPaintTime>0){
     const instantaneous=1000/Math.max(1,now-lastPaintTime);
     observedFps=observedFps===0?instantaneous:observedFps*.8+instantaneous*.2;
   }
   lastPaintTime=now;
  }
  function onState(event){
   const state=String(event?.detail?.state||"ready");
   phase=STATES.has(state)?state:"stopped";
   playbackEpoch=event?.detail?.epoch;
   explicitLiveMotion=event?.detail?.live===true&&!event?.detail?.stopped;
   live=(explicitLiveMotion||phase==='listening'||phase==='thinking'||phase==='speaking')&&
    !event?.detail?.stopped&&phase!=="paused"&&phase!=="stopped";
   resetFrameTelemetry();
   if(!live||phase==="paused"||phase==="stopped"){speechUntil=0;localViseme="silence";draw(0);}
  }
  win.addEventListener("oap-smi-character-state",onState);
  win.addEventListener("oap-smi-reduced-motion-change",event=>{
   userReducedMotion=event?.detail?.enabled===true;
   resetFrameTelemetry();
   if(userReducedMotion){speechUntil=0;localViseme="silence";draw(0);}
  });
  win.addEventListener("oap-smi-playback-state",event=>{
   localAudio=event?.detail?.phase==="playing"&&event?.detail?.source==="oap-first-party-pcm"&&event?.detail?.decodedAudio===true;
   if(!localAudio){speechUntil=0;localViseme="silence";}
  });
  win.addEventListener("oap-smi-audio-cue",event=>{
   const cue=event?.detail;
   if(!localAudio||phase!=="speaking"||!live||userReducedMotion||(!explicitLiveMotion&&reducedPreference)||
      cue?.source!=="oap-first-party-pcm"||cue?.decodedAudio!==true||
      cue?.synthesisPhonemeTiming!==true||cue?.epoch!==playbackEpoch||
      !Number.isFinite(cue?.audioClockMs)||cue.audioClockMs<0||
      !Object.hasOwn(LOCAL_POSE,cue?.viseme))return;
   localViseme=cue.viseme;
   audioCues+=1;
   if(Number.isFinite(cue.atMs))maxAudioClockDeltaMs=Math.max(maxAudioClockDeltaMs,Math.abs(cue.audioClockMs-cue.atMs));
   draw(win.performance.now());
  });
  win.addEventListener("oap-smi-speech-boundary",event=>{
   if(phase!=="speaking"||!live||event?.detail?.source!=="browser-speech-synthesis"||event?.detail?.decodedAudio!==false)return;
   if(!Number.isFinite(event.detail.elapsedMs)||event.detail.elapsedMs<0)return;
   speechUntil=win.performance.now()+170;
  });
  doc.addEventListener?.("visibilitychange",resetFrameTelemetry);
  win.addEventListener("pagehide",()=>{epoch=-1;win.cancelAnimationFrame?.(frame);resetFrameTelemetry();context.drawImage(image,0,0);for(const patch of featheredPatches.values())if(patch){patch.width=0;patch.height=0;}image.close?.();});
  frame=win.requestAnimationFrame(tick);
  shell.dataset.smiSourcePixelMotion="original_sha_verified";
  function proofSnapshot(){
   const layerKeys=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
   const allHashes=layerKeys.every(name=>/^[a-f0-9]{64}$/.test(String(evidenceLayerSha256[name]||"")));
   // Cropped source-image regions demonstrate renderer activity, NOT an
   // independently reviewed anatomical seven-layer rig.
   const sourcePixelRegionsObserved=played>0&&layerKeys.every(name=>rigLayerFrames[name]>0)&&allHashes;
   const fullBodyRigProven=false;
   const accurateSoftwareLipSyncProven=audioCues>=3&&maxAudioClockDeltaMs<=80&&rigLayerFrames.mouth_visemes>0;
   return Object.freeze({phase,live,frames:played,audioCues,localAudio,localViseme,
    sourceSha256:actual,evidenceLayerSha256,rigLayerFrames:Object.freeze({...rigLayerFrames}),
    reducedMotionPreference:reducedPreference,userReducedMotionPreference:userReducedMotion,explicitLiveMotion,
    ambientVisualMotion:renderActive()&&phase==="ready"&&!live&&played>0,
    renderActive:renderActive(),
    frameRateTargetFps:renderActive()?(live?(lowPower?30:60):(lowPower?20:30)):0,
    observedFps:renderActive()?Math.round(observedFps*10)/10:0,
    renderCostMs:Math.round(renderCostMs*10)/10,
    adaptiveFrameBudgetMs:Math.round(adaptiveFrameBudgetMs*10)/10,
    regionEdgeBlending:"source_pixel_feather_no_anatomy_approval",
    maxAudioClockDeltaMs,fullSceneSourcePixelMotion:played>0,sourcePixelRegionsObserved,fullBodyRigProven,
    accurateSoftwareLipSyncProven,accurateHumanLipSyncProven:false,
    physicalDeviceProofExcluded:true,privacyNoTelemetry:true});
  }
  return Object.freeze({sourceSha256:actual,sourceOnly:true,decodedAudio:false,
   privacyNoTelemetry:true,snapshot:proofSnapshot,
   stop:()=>{epoch=-1;win.cancelAnimationFrame?.(frame);resetFrameTelemetry();context.drawImage(image,0,0);}});
 }
 return Object.freeze({SOURCE,SHA256,WIDTH,HEIGHT,REGIONS,remapRegion,motionFor,attach});
});
