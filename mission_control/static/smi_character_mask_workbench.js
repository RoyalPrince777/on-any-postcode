/* Founder-only local exact-art mask editor. No telemetry, backend writes or motion.
 * An export is DRAFT, never rig/identity approval. No substitute art is created.
 */
(() => {
  "use strict";
  const NAMES=["eyes","head","breathing","mouth_visemes","face","hands","upper_body"];
  const LABELS=["Eyes","Head","Breathing","Mouth visemes","Face","Hands","Upper body"];
  const $=id=>document.getElementById(id);
  const stage=$("art-stage"),image=$("source-art"),feedback=$("feedback"),
    buttons=$("layers"),brush=$("brush"),coverage=$("coverage");
  const sourceUrl=document.body.dataset.approvedImage;
  const expected=document.body.dataset.approvedSha256;
  const state=new Map();
  let active=NAMES[0],ready=false,painting=false,erase=false,
    cursor={x:0,y:0},undo=null,objectUrl=null,busy=false;
  const actionIds=["paint","erase","brush","undo","clear","save-one","save-all","import-mask"];
  function say(value){feedback.textContent=value;}
  function enable(value){for(const id of actionIds)$(id).disabled=!value;
    for(const btn of buttons.querySelectorAll("button"))btn.disabled=!value;}
  function paintState(){for(const b of buttons.querySelectorAll("button")){
    const name=b.dataset.name;b.setAttribute("aria-pressed",String(name===active));
    b.dataset.filled=String(Boolean(state.get(name)?.filled));
  }
    const count=[...state.values()].filter(v=>v.filled).length;
    coverage.value=count;$("coverage-label").textContent=count+" / 7 painted";
  }
  function getLayer(name){
    if(state.has(name))return state.get(name);
    const canvas=document.createElement("canvas");
    canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
    canvas.dataset.name=name;canvas.hidden=name!==active;
    canvas.tabIndex=0;
    canvas.setAttribute("role","application");
    canvas.setAttribute("aria-label",LABELS[NAMES.indexOf(name)]
      +" mask canvas. Arrow keys move brush. Space stamps. Select Erase to remove pixels.");
    stage.append(canvas);
    const record={canvas,ctx:canvas.getContext("2d",{willReadFrequently:true}),filled:false};
    canvas.addEventListener("pointerdown",event=>{
      if(!ready||busy||event.button!==0)return;
      painting=true;undo={name,frame:record.ctx.getImageData(0,0,canvas.width,canvas.height)};
      canvas.setPointerCapture(event.pointerId);
      cursor=position(canvas,event);stroke(record,cursor,cursor);
      event.preventDefault();
    });
    canvas.addEventListener("pointermove",event=>{
      if(!painting||!canvas.hasPointerCapture(event.pointerId))return;
      const next=position(canvas,event);stroke(record,cursor,next);cursor=next;
      event.preventDefault();
    });
    const finish=event=>{
      if(!painting)return;
      painting=false;
      if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);
      record.filled=hasAlpha(record.ctx,canvas);paintState();
    };
    canvas.addEventListener("pointerup",finish);
    canvas.addEventListener("pointercancel",finish);
    canvas.addEventListener("keydown",event=>{
      if(!ready||busy)return;
      const step=Math.max(1,Number(brush.value));
      if(["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(event.key)){
        cursor={
          x:Math.max(0,Math.min(canvas.width,cursor.x
            +(event.key==="ArrowRight"?step:event.key==="ArrowLeft"?-step:0))),
          y:Math.max(0,Math.min(canvas.height,cursor.y
            +(event.key==="ArrowDown"?step:event.key==="ArrowUp"?-step:0)))};
        say("Brush at original pixel "+Math.round(cursor.x)+", "+Math.round(cursor.y));
        event.preventDefault();
      }else if(event.key===" "||event.key==="Enter"){
        undo={name,frame:record.ctx.getImageData(0,0,canvas.width,canvas.height)};
        stroke(record,cursor,cursor);record.filled=hasAlpha(record.ctx,canvas);
        paintState();event.preventDefault();
      }
    });
    state.set(name,record);return record;
  }
  function hasAlpha(ctx,canvas){
    const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    for(let i=3;i<data.length;i+=4)if(data[i]>0)return true;
    return false;
  }
  function position(canvas,event){
    const rect=canvas.getBoundingClientRect();
    return {x:Math.max(0,Math.min(canvas.width,(event.clientX-rect.left)
      *canvas.width/rect.width)),
      y:Math.max(0,Math.min(canvas.height,(event.clientY-rect.top)
      *canvas.height/rect.height))};
  }
  function stroke(rec,from,to){
    const ctx=rec.ctx;
    ctx.save();ctx.globalCompositeOperation=erase?"destination-out":"source-over";
    ctx.strokeStyle=erase?"rgba(0,0,0,1)":"rgba(255,255,255,1)";
    ctx.fillStyle=ctx.strokeStyle;
    ctx.lineCap="round";ctx.lineJoin="round";ctx.lineWidth=Number(brush.value);
    ctx.beginPath();ctx.moveTo(from.x,from.y);ctx.lineTo(to.x,to.y);ctx.stroke();
    ctx.beginPath();ctx.arc(to.x,to.y,Number(brush.value)/2,0,Math.PI*2);
    ctx.fill();ctx.restore();
  }
  function choose(name){
    if(!ready||busy||!NAMES.includes(name))return;
    active=name;undo=null;
    for(const [key,record] of state)record.canvas.hidden=key!==name;
    const chosen=getLayer(name);chosen.canvas.hidden=false;
    // On a narrow display the controls occupy a separate row. A newly
    // selected layer must remain paintable without an off-screen tap.
    if(window.matchMedia("(max-width: 820px)").matches){
      chosen.canvas.scrollIntoView({block:"center",behavior:"instant"});
    }
    cursor={x:image.naturalWidth/2,y:image.naturalHeight/2};
    paintState();say("Editing "+LABELS[NAMES.indexOf(name)]+"; draft only.");
  }
  for(let i=0;i<NAMES.length;i++){
    const btn=document.createElement("button");
    btn.type="button";btn.dataset.name=NAMES[i];btn.textContent=LABELS[i];
    btn.setAttribute("aria-pressed",String(i===0));btn.disabled=true;
    btn.addEventListener("click",()=>choose(NAMES[i]));buttons.append(btn);
  }
  enable(false);
  $("brush-label").textContent=brush.value;
  brush.addEventListener("input",()=>{$("brush-label").textContent=brush.value;});
  function setMode(value){
    erase=value;$("paint").setAttribute("aria-pressed",String(!value));
    $("erase").setAttribute("aria-pressed",String(value));
  }
  $("paint").addEventListener("click",()=>setMode(false));
  $("erase").addEventListener("click",()=>setMode(true));
  $("undo").addEventListener("click",()=>{
    if(!undo||undo.name!==active){say("No stroke to undo on this layer.");return;}
    const rec=getLayer(active);rec.ctx.putImageData(undo.frame,0,0);undo=null;
    rec.filled=hasAlpha(rec.ctx,rec.canvas);paintState();say("Last stroke restored.");
  });
  $("clear").addEventListener("click",()=>{
    const rec=getLayer(active);undo={name:active,
      frame:rec.ctx.getImageData(0,0,rec.canvas.width,rec.canvas.height)};
    rec.ctx.clearRect(0,0,rec.canvas.width,rec.canvas.height);
    rec.filled=false;paintState();say("Cleared "+active+"; undo available.");
  });
  function maskBlob(canvas){return new Promise((resolve,reject)=>{
    canvas.toBlob(blob=>blob?resolve(blob):reject(Error("mask_export_failed")),"image/png");
  });}
  function download(blob,name){
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
  }
  async function exportOne(){
    if(!ready||busy)return;
    busy=true;enable(false);
    try{
      const rec=getLayer(active);
      if(!rec.filled||!hasAlpha(rec.ctx,rec.canvas))throw Error("paint_layer_first");
      download(await maskBlob(rec.canvas),active+".png");
      say("Draft "+active+".png downloaded locally; not yet approved.");
    }catch(error){say("Export blocked: "+error.message);}
    finally{busy=false;enable(true);}
  }
  $("save-one").addEventListener("click",exportOne);
  $("save-all").addEventListener("click",async()=>{
    if(!ready||busy)return;
    busy=true;enable(false);
    try{
      const entries=[];
      for(const name of NAMES){
        const rec=state.get(name);
        if(!rec?.filled||!hasAlpha(rec.ctx,rec.canvas))
          throw Error("Finish all seven nonempty masks; missing "+name);
        const blob=await maskBlob(rec.canvas);
        entries.push({name:name+".png",data:new Uint8Array(await blob.arrayBuffer())});
      }
      const manifest={version:"0.1",source_sha256:expected,
        canvas:[image.naturalWidth,image.naturalHeight],
        names:NAMES,approval:"DRAFT_REQUIRES_FOUNDER_REVIEW",
        animation_active:false,includes_hidden_regions:false};
      entries.push({name:"mask-bundle.json",
        data:new TextEncoder().encode(JSON.stringify(manifest,null,2)+"\n")});
      const bytes=window.OAP_SMI_MASK_ZIP.createZip(entries);
      download(new Blob([bytes],{type:"application/zip"}),
        "smi-exact-character-draft-masks.zip");
      say("Seven original-canvas draft masks saved locally. Human review required.");
    }catch(error){say("ZIP export blocked: "+error.message);}
    finally{busy=false;enable(true);}
  });
  $("import-mask").addEventListener("change",async event=>{
    const file=event.target.files?.[0];event.target.value="";
    if(!file||!ready||busy)return;
    busy=true;enable(false);
    try{
      if(file.type!=="image/png"||file.size>20*1024*1024)
        throw Error("Choose a PNG mask under 20 MB");
      const bmp=await createImageBitmap(file);
      try{
        if(bmp.width!==image.naturalWidth||bmp.height!==image.naturalHeight)
          throw Error("Mask must match original full image canvas");
        const scratch=document.createElement("canvas");
        scratch.width=bmp.width;scratch.height=bmp.height;
        const c=scratch.getContext("2d",{willReadFrequently:true});
        c.drawImage(bmp,0,0);
        const pixels=c.getImageData(0,0,bmp.width,bmp.height).data;
        let filled=false;
        for(let i=0;i<pixels.length;i+=4){
          if(pixels[i+3]>0){
            filled=true;
            if(pixels[i]!==255||pixels[i+1]!==255||pixels[i+2]!==255)
              throw Error("Mask must be white with alpha, not a colour photo");
          }
        }
        if(!filled)throw Error("Empty mask cannot be imported");
        const rec=getLayer(active);
        undo={name:active,
          frame:rec.ctx.getImageData(0,0,rec.canvas.width,rec.canvas.height)};
        rec.ctx.clearRect(0,0,rec.canvas.width,rec.canvas.height);
        rec.ctx.drawImage(scratch,0,0);rec.filled=true;
        paintState();say("Restored local "+active+" mask as draft.");
      }finally{bmp.close();}
    }catch(error){say("Restore blocked: "+error.message);}
    finally{busy=false;enable(true);}
  });
  async function start(){
    try{
      if(!sourceUrl.startsWith("/static/oap/")||!/^[a-f0-9]{64}$/.test(expected)
        ||!window.crypto?.subtle)throw Error("Approved source verification unavailable");
      const result=await fetch(sourceUrl,{credentials:"same-origin",cache:"no-store",
        referrerPolicy:"no-referrer"});
      if(!result.ok)throw Error("Approved source unavailable");
      const bytes=await result.arrayBuffer();
      if(bytes.byteLength===0||bytes.byteLength>20*1024*1024)
        throw Error("Unexpected source image size");
      const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",bytes)))
        .map(x=>x.toString(16).padStart(2,"0")).join("");
      if(digest!==expected)throw Error("Original character identity mismatch");
      objectUrl=URL.createObjectURL(new Blob([bytes],{type:"image/jpeg"}));
      image.src=objectUrl;
      await image.decode();
      if(!image.naturalWidth||!image.naturalHeight
        ||image.naturalWidth*image.naturalHeight>16000000)
        throw Error("Original canvas size unsupported");
      image.hidden=false;ready=true;
      enable(true);choose(active);
      say("Exact original verified. Draw your first draft region.");
    }catch(error){
      ready=false;enable(false);
      say("Workbench locked: "+error.message+". Original character remains unchanged.");
    }
  }
  window.addEventListener("pagehide",()=>{
    if(objectUrl)URL.revokeObjectURL(objectUrl);
  });
  start();
})();
