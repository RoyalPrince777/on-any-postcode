/* PROJECT SHELL: one Founder-private scene panel inside canonical SMI Studio.
   No parallel media renderer or independent job queue. */
(()=>{
  "use strict";
  function mount(){
    const studioButton=document.getElementById("studio-button");
    const menu=document.getElementById("attach-menu");
    const cfg=window.OAP_SMI_UI||{};
    if(!studioButton||!menu||!cfg.projectShellPrepareUrl||!cfg.studioStatusUrl)return;
    if(document.getElementById("smi-project-shell-open"))return;
    const openButton=document.createElement("button");
    openButton.type="button";
    openButton.id="smi-project-shell-open";
    openButton.className="attach-option connector";
    openButton.textContent="🎬 PROJECT SHELL · Scene Command";
    studioButton.after(openButton);

    const panel=document.createElement("section");
    panel.id="smi-project-shell-panel";
    panel.className="smi-project-shell";
    panel.hidden=true;
    panel.setAttribute("role","dialog");
    panel.setAttribute("aria-modal","true");
    panel.setAttribute("aria-label","PROJECT SHELL · Scene Command");
    panel.innerHTML=[
      '<div class="shell-scene-sheet">',
      '<header class="shell-scene-header"><div><small>SMI → OAP Studio → Scene Builder</small><h2>PROJECT SHELL</h2><p>Episode 01 · Founder-private</p></div>',
      '<button class="shell-close" type="button" data-shell-close aria-label="Close scene command">✕</button></header>',
      '<p class="shell-truth" data-shell-truth>Checking first-party Studio configuration…</p>',
      '<label class="shell-label">Scene<select data-shell-scene></select></label>',
      '<div class="shell-fields">',
      '<label class="shell-label">Film ratio<select data-shell-ratio><option value="16:9">16:9 landscape</option><option value="9:16">9:16 vertical</option></select></label>',
      '<label class="shell-label">FPS target<select data-shell-fps><option value="24">24</option><option value="30">30</option><option value="60" selected>60</option></select></label>',
      '</div>',
      '<p class="shell-footnote">FPS, South London voice and lip sync are targets, not certified output properties.</p>',
      '<p class="shell-reference" data-shell-reference>🔒 Approved character reference must be attached in this signed-in SMI session. ChatGPT files are not automatically imported.</p>',
      '<div class="shell-actions"><button type="button" data-shell-attach>Attach reference</button><button type="button" data-shell-prepare>Check renderer & prepare</button></div>',
      '<p class="shell-state" data-shell-state aria-live="polite">No render submitted. No charges made.</p>',
      '<pre class="shell-prompt" data-shell-prompt hidden></pre>',
      '<label class="shell-authority"><input type="checkbox" data-shell-consent> I confirm I have rights to the reference and authorise this potentially chargeable private render. Do not publish.</label>',
      '<button type="button" class="shell-render" data-shell-render disabled>Submit approved render</button>',
      '<small class="shell-footnote">Rendered MP4 remains unverified until the existing Studio status, content and media checks succeed. Guardian, HRM and Founder Final apply.</small>',
      '</div>'
    ].join("");
    document.body.append(panel);

    const get=s=>panel.querySelector(s);
    const scene=get("[data-shell-scene]");
    const ratio=get("[data-shell-ratio]");
    const fps=get("[data-shell-fps]");
    const truth=get("[data-shell-truth]");
    const state=get("[data-shell-state]");
    const prompt=get("[data-shell-prompt]");
    const consent=get("[data-shell-consent]");
    const render=get("[data-shell-render]");
    const prepareButton=get("[data-shell-prepare]");
    let prepared=null,backendAvailable=false;
    const referenceAttached=()=>{
      try{
        return typeof selectedImage==="string"&&
          /^data:image\/(png|jpeg|webp);base64,/.test(selectedImage);
      }catch{return false;}
    };
    const reset=()=>{
      prepared=null;
      consent.checked=false;
      render.disabled=true;
      prompt.hidden=true;
      prompt.textContent="";
      state.textContent="Scene options changed · prepare again. No render submitted.";
    };
    const setReference=()=>{
      get("[data-shell-reference]").textContent=referenceAttached()
        ?"🔒 A reference image is attached. Its identity and rights are not independently certified."
        :"🔒 Attach the approved OAP character reference here first. ChatGPT attachments are not imported.";
    };
    [scene,ratio,fps].forEach(el=>el.addEventListener("change",reset));
    consent.addEventListener("change",()=>{
      render.disabled=!(consent.checked&&prepared&&prepared.can_request_render&&referenceAttached());
    });
    const close=()=>{panel.hidden=true;reset();openButton.focus();};
    get("[data-shell-close]").addEventListener("click",close);
    document.addEventListener("keydown",event=>{
      if(event.key==="Escape"&&!panel.hidden)close();
    });
    get("[data-shell-attach]").addEventListener("click",()=>{
      document.getElementById("image-input")?.click();
      state.textContent="Select the approved reference image, then check renderer again.";
    });

    async function open(){
      panel.hidden=false;
      setReference();
      truth.textContent="Checking signed-in OAP Studio…";
      scene.replaceChildren();
      reset();
      try{
        const response=await fetch(cfg.studioStatusUrl,{credentials:"same-origin",cache:"no-store"});
        if(!response.ok)throw new Error("Studio status unavailable");
        const data=await response.json();
        const contract=data.project_shell||{};
        const scenes=Array.isArray(contract.scenes)?contract.scenes:[];
        if(!scenes.length)throw new Error("PROJECT SHELL is not installed in this SMI runtime");
        for(const item of scenes){
          const option=document.createElement("option");
          option.value=item.id;
          option.textContent=item.id+" · "+item.name;
          scene.append(option);
        }
        backendAvailable=contract.renderer_configured===true;
        truth.textContent=backendAvailable
          ?"🟣 Video provider configured · live render and final MP4 still unverified"
          :"🔴 Video renderer not configured · preparation only, no render submitted";
      }catch(error){
        backendAvailable=false;
        truth.textContent="🔴 "+(error.message||"Studio unavailable")+" · no render submitted";
      }
    }
    openButton.addEventListener("click",open);
    prepareButton.addEventListener("click",async()=>{
      if(!scene.value){state.textContent="No supported scene loaded";return;}
      prepareButton.disabled=true;
      prepared=null;
      render.disabled=true;
      consent.checked=false;
      setReference();
      state.textContent="Checking selected scene against existing Studio…";
      try{
        const response=await fetch(cfg.projectShellPrepareUrl,{
          method:"POST",
          credentials:"same-origin",
          headers:{
            "Content-Type":"application/json",
            "X-OAP-CSRF":window.csrfToken||cfg.csrfToken||""
          },
          body:JSON.stringify({
            scene_id:scene.value,
            aspect_ratio:ratio.value,
            fps_target:Number(fps.value),
            reference_attached:referenceAttached()
          })
        });
        const data=await response.json().catch(()=>({}));
        if(!response.ok)throw new Error(data?.error?.message||"Scene preflight failed");
        prepared=data;
        prompt.textContent=data.prompt||"";
        prompt.hidden=false;
        state.textContent=data.can_request_render
          ?"🟣 Prepared · no job submitted. Review the paid-render authorisation below."
          :"🔒 "+(data.blocked_reason||"Renderer unavailable")+" · no job submitted.";
        consent.dispatchEvent(new Event("change"));
      }catch(error){
        state.textContent="🔴 "+(error.message||"Cannot prepare scene")+" · no job submitted";
      }finally{prepareButton.disabled=false;}
    });
    render.addEventListener("click",()=>{
      if(!prepared||!prepared.can_request_render||!consent.checked||!referenceAttached()||!backendAvailable){
        state.textContent="🔒 Reference, provider and explicit authorisation required · no render submitted";
        return;
      }
      const textarea=document.getElementById("message");
      const sceneTool=menu.querySelector('[data-studio-tool="scene_builder"]');
      if(!textarea||!sceneTool){
        state.textContent="🔴 Canonical SMI Scene Builder not mounted · no render submitted";
        return;
      }
      const lockButton=document.getElementById("character-lock-button");
      if(lockButton&&lockButton.getAttribute("aria-pressed")!=="true")lockButton.click();
      window.OAP_SMI_CHARACTER_LOCK=true;
      window.OAP_SMI_PENDING_PROJECT_SHELL=Object.freeze({
        video_size:prepared.video_size,
        video_seconds:prepared.video_seconds
      });
      textarea.value=prepared.prompt;
      textarea.dispatchEvent(new Event("input",{bubbles:true}));
      state.textContent="Submitting to existing SMI Studio; completion and costs not yet verified…";
      render.disabled=true;
      panel.hidden=true;
      sceneTool.click();
      prepared=null;
      consent.checked=false;
    });
    window.OAP_SMI_PROJECT_SHELL=Object.freeze({
      installed:true,
      canonicalStudio:true,
      rendererDuplicated:false,
      autoSubmit:false,
      founderPrivate:true
    });
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",mount,{once:true});
  else mount();
})();
