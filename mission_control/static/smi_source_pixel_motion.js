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
  const a=Math.sin(ms/620),b=Math.sin(ms/1110),c=Math.sin(ms/3400);
  if(state==="stopped"||state==="paused")return Object.freeze({head:[0,0,1],eyes:[0,0,1],mouth:[0,0,1],chest:[0,0,1],hands:[0,0,1]});
  const focus=state==="thinking"?1.45:state==="listening"?1.2:1;
  return Object.freeze({head:[a*1.65*focus,b*.95*focus,1],
   eyes:[a*3.1*focus,Math.max(0,b)*1.2,1],
   mouth:state==="speaking"?[speechPulse*2,speechPulse*2.5,1+speechPulse*.25]:[0,0,1],
   chest:[0,b*1.15,1+b*.006],hands:[a*.72,-b*.6,1]});
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
  canvas.style.cssText="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center center;pointer-events:none;z-index:-1";
  shell.prepend(canvas);
  const context=canvas.getContext("2d",{willReadFrequently:true});
  if(!context){canvas.remove();image.close?.();return null;}
  context.drawImage(image,0,0);
  const samples=Object.fromEntries(REGIONS.map(region=>[region.id,context.getImageData(region.x,region.y,region.w,region.h)]));
  let epoch=0,frame=0,last=0,phase="ready",live=false,reduced=Boolean(win.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches),played=0,speechUntil=0;
  function draw(ms){
   context.drawImage(image,0,0);
   if(!live||reduced||phase==="paused"||phase==="stopped")return;
   const pulse=phase==="speaking"?Math.max(0,Math.min(1,(speechUntil-ms)/170)):0;
   const poses=motionFor(phase,ms,pulse);
   for(const region of REGIONS){
    const params=region.id==="left-hand"||region.id==="right-hand"?poses.hands:region.id==="chest"?poses.chest:region.id==="eyes"?poses.eyes:region.id==="mouth"?poses.mouth:poses.head;
    const result=remapRegion(samples[region.id],region,...params);
    if(!result)continue;
    const patch=context.createImageData(region.w,region.h);patch.data.set(result.data);
    context.putImageData(patch,region.x,region.y);
   }
   played++;
  }
  function tick(now){
   if(epoch<0)return;
   frame=win.requestAnimationFrame(tick);
   if(now-last<66||!live||reduced||phase==="paused"||phase==="stopped")return;
   last=now;draw(now);
  }
  function onState(event){
   const state=String(event?.detail?.state||"ready");
   phase=STATES.has(state)?state:"stopped";
   live=(event?.detail?.live===true||phase==='listening'||phase==='thinking'||phase==='speaking')&&!event?.detail?.stopped;
   if(!live||phase==="paused"||phase==="stopped"){speechUntil=0;draw(0);}
  }
  win.addEventListener("oap-smi-character-state",onState);
  win.addEventListener("oap-smi-playback-state",event=>{if(event?.detail?.phase!=="playing")speechUntil=0;});
  win.addEventListener("oap-smi-speech-boundary",event=>{
   if(phase!=="speaking"||!live||event?.detail?.source!=="browser-speech-synthesis"||event?.detail?.decodedAudio!==false)return;
   if(!Number.isFinite(event.detail.elapsedMs)||event.detail.elapsedMs<0)return;
   speechUntil=win.performance.now()+170;
  });
  win.addEventListener("pagehide",()=>{epoch=-1;win.cancelAnimationFrame?.(frame);context.drawImage(image,0,0);image.close?.();});
  frame=win.requestAnimationFrame(tick);
  shell.dataset.smiSourcePixelMotion="original_sha_verified";
  return Object.freeze({sourceSha256:actual,sourceOnly:true,decodedAudio:false,
   accurateLipSyncProven:false,fullBodyRigProven:false,privacyNoTelemetry:true,
   snapshot:()=>Object.freeze({phase,live,frames:played}),
   stop:()=>{epoch=-1;win.cancelAnimationFrame?.(frame);context.drawImage(image,0,0);}});
 }
 return Object.freeze({SOURCE,SHA256,WIDTH,HEIGHT,REGIONS,remapRegion,motionFor,attach});
});
